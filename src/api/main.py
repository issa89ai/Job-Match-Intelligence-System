from __future__ import annotations

import json
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.api.schemas import HealthResponse, MatchRequest, MatchResponse
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

security = HTTPBearer()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Job Match Intelligence API",
    description="""
An explainable API for matching candidates to jobs, with user accounts,
saved profiles, and saved preferences.
""",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Auth", "description": "User registration and login."},
        {"name": "Profile", "description": "Save and load candidate profile."},
        {"name": "Preferences", "description": "Save and load job preferences."},
        {"name": "Matching", "description": "Core job-candidate matching endpoints."},
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
# 1. Register
# 2. Login
# 3. Get Me
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
# 4. Save Profile
# 5. Load Profile
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
# 6. Save Preferences
# 7. Load Preferences
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
# 8. Match
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)