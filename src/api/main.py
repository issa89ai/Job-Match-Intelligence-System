from __future__ import annotations

import ast
import glob
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.api.schemas import (
    DatasetRecommendationRequest,
    HealthResponse,
    JobsPreviewResponse,
    JobInput,
    MatchRequest,
    MatchResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from src.api.user_schemas import (
    AuthResponse,
    LoginRequest,
    PreferenceRequest,
    PreferenceResponse,
    RegisterRequest,
    SavedProfileRequest,
    SavedProfileResponse,
    UserMeResponse,
)
from src.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from src.candidate.feature_builder import build_candidate_features
from src.candidate.parser import parse_candidate_profile
from src.db.database import Base, engine, get_db
from src.db.models import CandidateProfileRecord, User, UserPreferenceRecord
from src.matching.ranking import rank_candidate_for_job
from src.matching.recommendation import recommend_jobs_for_candidate

security = HTTPBearer()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Job Match Intelligence API",
    description="""
An explainable API for matching candidates to jobs, with user accounts,
saved profiles, saved preferences, and multi-job recommendations.
""",
    version="3.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Auth", "description": "User registration and login."},
        {"name": "Profile", "description": "Save and load candidate profile."},
        {"name": "Preferences", "description": "Save and load job preferences."},
        {"name": "Matching", "description": "Core job-candidate matching endpoints."},
        {"name": "Recommendations", "description": "Multi-job recommendation endpoints."},
        {"name": "Jobs", "description": "Dataset-backed job preview endpoints."},
    ],
)


# -----------------------------
# Helpers
# -----------------------------
def _json_dump(value) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def _json_load(value: Optional[str]):
    if not value:
        return []
    try:
        return json.loads(value)
    except Exception:
        return []


def _safe_list(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []

        # Try JSON / Python-list-like strings first
        try:
            parsed = ast.literal_eval(stripped)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except Exception:
            pass

        # Fall back to comma-separated parsing
        return [item.strip() for item in stripped.split(",") if item.strip()]

    return [str(value).strip()] if str(value).strip() else []


def _find_latest_jobs_dataset(custom_path: Optional[str] = None) -> str:
    if custom_path:
        path = Path(custom_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset not found: {custom_path}")
        return str(path)

    patterns = [
        "data/curated/requirements_enriched/*.csv",
        "data/curated/requirements/*.csv",
    ]

    candidates: List[str] = []
    for pattern in patterns:
        candidates.extend(glob.glob(pattern))

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail=(
                "No jobs dataset found. Expected a CSV under "
                "data/curated/requirements_enriched/ or data/curated/requirements/."
            ),
        )

    latest = max(candidates, key=lambda p: Path(p).stat().st_mtime)
    return latest


def _load_jobs_from_csv(csv_path: str, limit_jobs: Optional[int] = None) -> List[Dict[str, Any]]:
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read dataset: {e}")

    records: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        job = {
            "job_id": str(row.get("job_id") or row.get("job_uid") or "").strip(),
            "title": str(row.get("title") or row.get("title_raw") or row.get("title_normalized") or "").strip(),
            "company": str(row.get("company") or row.get("source_company") or "").strip(),
            "location": str(row.get("location") or row.get("location_normalized") or row.get("location_raw") or "").strip(),
            "workplace_type": str(row.get("workplace_type") or "").strip(),
            "domains": _safe_list(row.get("domains")),
            "required_skills": _safe_list(row.get("required_skills")),
            "preferred_skills": _safe_list(row.get("preferred_skills")),
            "other_skills": _safe_list(row.get("other_skills") or row.get("other_skills_found")),
            "years_experience_required": None
            if pd.isna(row.get("years_experience_required", row.get("years_experience_extracted")))
            else int(row.get("years_experience_required", row.get("years_experience_extracted"))),
            "education_required": None
            if pd.isna(row.get("education_required", row.get("education_extracted")))
            else str(row.get("education_required", row.get("education_extracted"))).strip(),
            "seniority": None
            if pd.isna(row.get("seniority", row.get("seniority_inferred")))
            else str(row.get("seniority", row.get("seniority_inferred"))).strip(),
        }

        if not job["job_id"]:
            continue
        if not job["title"]:
            continue

        records.append(job)

    if limit_jobs:
        records = records[:limit_jobs]

    return records


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    email = decode_access_token(token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


# -----------------------------
# Health
# -----------------------------
@app.get("/", response_model=HealthResponse, include_in_schema=False)
def root() -> HealthResponse:
    return HealthResponse(status="ok", message="Job Match Intelligence API is running.")


@app.get("/health", response_model=HealthResponse, include_in_schema=False)
def health() -> HealthResponse:
    return HealthResponse(status="ok", message="Service healthy.")


# -----------------------------
# Auth
# -----------------------------
@app.post(
    "/auth/register",
    response_model=AuthResponse,
    tags=["Auth"],
    summary="Register a new user",
)
def register_user(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.email)

    return AuthResponse(
        access_token=token,
        user_email=user.email,
        full_name=user.full_name or "",
    )


@app.post(
    "/auth/login",
    response_model=AuthResponse,
    tags=["Auth"],
    summary="Login user",
)
def login_user(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(user.email)

    return AuthResponse(
        access_token=token,
        user_email=user.email,
        full_name=user.full_name or "",
    )


@app.get(
    "/me",
    response_model=UserMeResponse,
    tags=["Auth"],
    summary="Get current user",
)
def get_me(current_user: User = Depends(get_current_user)) -> UserMeResponse:
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name or "",
    )


# -----------------------------
# Profile
# -----------------------------
@app.post(
    "/profile",
    response_model=SavedProfileResponse,
    tags=["Profile"],
    summary="Save candidate profile for current user",
)
def save_profile(
    payload: SavedProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedProfileResponse:
    record = db.query(CandidateProfileRecord).filter(
        CandidateProfileRecord.user_id == current_user.id
    ).first()

    if not record:
        record = CandidateProfileRecord(user_id=current_user.id)
        db.add(record)

    record.candidate_id = payload.candidate_id
    record.full_name = payload.full_name
    record.current_title = payload.current_title
    record.location = payload.location
    record.education = payload.education
    record.years_experience = payload.years_experience
    record.skills_json = _json_dump(payload.skills)
    record.tools_json = _json_dump(payload.tools)
    record.domains_json = _json_dump(payload.domains)
    record.certifications_json = _json_dump(payload.certifications)
    record.projects_json = _json_dump(payload.projects)
    record.seniority = payload.seniority
    record.summary = payload.summary

    db.commit()
    db.refresh(record)

    return SavedProfileResponse(
        user_id=current_user.id,
        candidate_id=record.candidate_id,
        full_name=record.full_name or "",
        current_title=record.current_title or "",
        location=record.location or "",
        education=record.education,
        years_experience=record.years_experience,
        skills=_json_load(record.skills_json),
        tools=_json_load(record.tools_json),
        domains=_json_load(record.domains_json),
        certifications=_json_load(record.certifications_json),
        projects=_json_load(record.projects_json),
        seniority=record.seniority,
        summary=record.summary or "",
    )


@app.get(
    "/profile",
    response_model=SavedProfileResponse,
    tags=["Profile"],
    summary="Load candidate profile for current user",
)
def load_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedProfileResponse:
    record = db.query(CandidateProfileRecord).filter(
        CandidateProfileRecord.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="No saved profile found.")

    return SavedProfileResponse(
        user_id=current_user.id,
        candidate_id=record.candidate_id,
        full_name=record.full_name or "",
        current_title=record.current_title or "",
        location=record.location or "",
        education=record.education,
        years_experience=record.years_experience,
        skills=_json_load(record.skills_json),
        tools=_json_load(record.tools_json),
        domains=_json_load(record.domains_json),
        certifications=_json_load(record.certifications_json),
        projects=_json_load(record.projects_json),
        seniority=record.seniority,
        summary=record.summary or "",
    )


# -----------------------------
# Preferences
# -----------------------------
@app.post(
    "/preferences",
    response_model=PreferenceResponse,
    tags=["Preferences"],
    summary="Save job preferences for current user",
)
def save_preferences(
    payload: PreferenceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferenceResponse:
    record = db.query(UserPreferenceRecord).filter(
        UserPreferenceRecord.user_id == current_user.id
    ).first()

    if not record:
        record = UserPreferenceRecord(user_id=current_user.id)
        db.add(record)

    record.preferred_titles_json = _json_dump(payload.preferred_titles)
    record.preferred_locations_json = _json_dump(payload.preferred_locations)
    record.preferred_workplace_types_json = _json_dump(payload.preferred_workplace_types)
    record.preferred_domains_json = _json_dump(payload.preferred_domains)
    record.preferred_seniority = payload.preferred_seniority
    record.min_score = payload.min_score

    db.commit()
    db.refresh(record)

    return PreferenceResponse(
        user_id=current_user.id,
        preferred_titles=_json_load(record.preferred_titles_json),
        preferred_locations=_json_load(record.preferred_locations_json),
        preferred_workplace_types=_json_load(record.preferred_workplace_types_json),
        preferred_domains=_json_load(record.preferred_domains_json),
        preferred_seniority=record.preferred_seniority,
        min_score=record.min_score or 50,
    )


@app.get(
    "/preferences",
    response_model=PreferenceResponse,
    tags=["Preferences"],
    summary="Load job preferences for current user",
)
def load_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferenceResponse:
    record = db.query(UserPreferenceRecord).filter(
        UserPreferenceRecord.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="No saved preferences found.")

    return PreferenceResponse(
        user_id=current_user.id,
        preferred_titles=_json_load(record.preferred_titles_json),
        preferred_locations=_json_load(record.preferred_locations_json),
        preferred_workplace_types=_json_load(record.preferred_workplace_types_json),
        preferred_domains=_json_load(record.preferred_domains_json),
        preferred_seniority=record.preferred_seniority,
        min_score=record.min_score or 50,
    )


# -----------------------------
# Matching
# -----------------------------
@app.post(
    "/match",
    response_model=MatchResponse,
    tags=["Matching"],
    summary="Match a candidate to a job",
)
def match_candidate_to_job(payload: MatchRequest) -> MatchResponse:
    raw_candidate = payload.candidate.model_dump()
    job_features = payload.job.model_dump()

    candidate = parse_candidate_profile(raw_candidate)
    candidate_features = build_candidate_features(candidate)

    result = rank_candidate_for_job(job_features, candidate_features)

    return MatchResponse(**result)


# -----------------------------
# Jobs
# -----------------------------
@app.get(
    "/jobs",
    response_model=JobsPreviewResponse,
    tags=["Jobs"],
    summary="Preview jobs from the latest dataset",
)
def preview_jobs(
    limit: int = Query(default=20, ge=1, le=500),
    dataset_path: Optional[str] = Query(default=None),
) -> JobsPreviewResponse:
    csv_path = _find_latest_jobs_dataset(dataset_path)
    jobs = _load_jobs_from_csv(csv_path, limit_jobs=limit)

    return JobsPreviewResponse(
        count=len(jobs),
        jobs=[JobInput(**job) for job in jobs],
        dataset_path=csv_path,
    )


# -----------------------------
# Recommendations
# -----------------------------
@app.post(
    "/recommendations",
    response_model=RecommendationResponse,
    tags=["Recommendations"],
    summary="Recommend top jobs for a candidate from provided job list",
)
def get_recommendations(payload: RecommendationRequest) -> RecommendationResponse:
    results = recommend_jobs_for_candidate(
        candidate_payload=payload.candidate.model_dump(),
        jobs_payload=[job.model_dump() for job in payload.jobs],
        preferences_payload=payload.preferences,
        top_k=payload.top_k,
    )

    return RecommendationResponse(
        count=len(results),
        recommendations=results,
    )


@app.post(
    "/recommendations/from_dataset",
    response_model=RecommendationResponse,
    tags=["Recommendations"],
    summary="Recommend top jobs for a candidate from latest dataset",
)
def get_recommendations_from_dataset(
    payload: DatasetRecommendationRequest,
) -> RecommendationResponse:
    csv_path = _find_latest_jobs_dataset(payload.dataset_path)
    jobs = _load_jobs_from_csv(csv_path, limit_jobs=payload.limit_jobs)

    results = recommend_jobs_for_candidate(
        candidate_payload=payload.candidate.model_dump(),
        jobs_payload=jobs,
        preferences_payload=payload.preferences,
        top_k=payload.top_k,
    )

    return RecommendationResponse(
        count=len(results),
        recommendations=results,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)