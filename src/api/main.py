from __future__ import annotations

import ast
import glob
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import File, UploadFile

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.api.schemas import (
    DatasetRecommendationRequest,
    HealthResponse,
    JobsPreviewResponse,
    JobInput,
    LiveRecommendationRequest,
    MatchRequest,
    MatchResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from src.api.user_schemas import (
    AuthResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    PreferenceRequest,
    PreferenceResponse,
    ProfileListItem,
    ProfileListResponse,
    RegisterRequest,
    ResetPasswordRequest,
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
from src.db.models import CandidateProfileRecord, PasswordResetToken, User, UserPreferenceRecord
from src.candidate.resume_extractor import parse_resume, compute_profile_completeness
from src.api.email_service import send_password_reset_email
from src.ingestion.jsearch import JSearchClient
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
        {"name": "Live", "description": "Real-time job search and matching via JSearch."},
        {"name": "Resume", "description": "Resume upload, parsing, and profile completeness."},
    ],
)

# CORS — allow Streamlit Cloud and local dev.
# Set ALLOWED_ORIGINS env var on Render to your Streamlit Cloud URL
# e.g. "https://yourapp.streamlit.app" (comma-separated for multiple).
import os as _os
_raw_origins = _os.environ.get("ALLOWED_ORIGINS", "*")
_origins = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


def _parse_resume_text(text: str) -> dict:
    """
    Extract a best-effort CandidateInput dict from raw resume text.

    Uses simple regex heuristics — good enough for quick matching from a
    text paste. Falls back gracefully when fields cannot be detected.
    """
    import re

    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    text_lower = text.lower()

    # ── Name & title from first line ───────────────────────────────────
    full_name = ""
    current_title = ""
    if lines:
        first = lines[0]
        for sep in [" — ", " – ", " - ", " | ", ":"]:
            if sep in first:
                parts = first.split(sep, 1)
                full_name = parts[0].strip()
                current_title = parts[1].strip()
                break
        else:
            full_name = first

    # ── Location: scan first 5 lines ───────────────────────────────────
    location = ""
    location_hints = [
        "ottawa", "toronto", "vancouver", "montreal", "calgary", "edmonton",
        "remote", "canada", "new york", "san francisco", "london", "berlin",
        "seattle", "boston", "austin", "chicago",
    ]
    for ln in lines[:5]:
        ln_low = ln.lower()
        if any(h in ln_low for h in location_hints):
            location = ln.split("|")[0].strip()
            break

    # ── Education ──────────────────────────────────────────────────────
    education = None
    edu_map = [
        (r"\bph\.?d\b|\bdoctorate\b", "phd"),
        (r"\bmaster'?s?\b|\bmsc\b|\bmba\b|\bm\.s\b", "master"),
        (r"\bbachelor'?s?\b|\bbsc\b|\bb\.s\b|\bb\.a\b", "bachelor"),
        (r"\bassociate\b", "associate"),
        (r"\bhigh school\b|\bsecondary\b", "high_school"),
    ]
    for pattern, level in edu_map:
        if re.search(pattern, text_lower):
            education = level
            break

    # ── Years of experience ────────────────────────────────────────────
    years_experience = 0
    exp_match = re.search(r"(\d+)\s*\+?\s*years?\s*(?:of\s+)?(?:experience|exp)", text_lower)
    if exp_match:
        years_experience = int(exp_match.group(1))

    # ── Seniority: derive from years, then override from title keywords ─
    seniority = None
    if years_experience >= 5:
        seniority = "senior"
    elif years_experience >= 3:
        seniority = "mid"
    elif years_experience >= 1:
        seniority = "entry"

    title_lower = current_title.lower()
    for kw in ["senior", "lead", "principal", "staff", "head", "vp"]:
        if kw in title_lower:
            seniority = "senior"
            break
    for kw in ["junior", "entry"]:
        if kw in title_lower:
            seniority = "entry"
            break
    if "mid" in title_lower:
        seniority = "mid"

    # ── Skills / tools / domains: look for labelled lines first ────────
    def _extract_labelled_list(label: str) -> List[str]:
        m = re.search(rf"{label}\s*[:\-]\s*([^\n]+)", text, re.IGNORECASE)
        if m:
            return [s.strip().lower() for s in m.group(1).split(",") if s.strip()]
        return []

    skills = _extract_labelled_list("skills?")
    tools = _extract_labelled_list("tools?")
    domains = _extract_labelled_list("domains?")

    # If no explicit Skills: line, scan for common tech keywords in the full text
    if not skills:
        known_skills = [
            "python", "sql", "java", "javascript", "typescript", "react", "node.js",
            "machine learning", "deep learning", "nlp", "pandas", "numpy",
            "scikit-learn", "tensorflow", "pytorch", "keras",
            "docker", "kubernetes", "aws", "azure", "gcp",
            "postgresql", "mysql", "mongodb", "redis",
            "fastapi", "django", "flask", "spring",
            "power bi", "tableau", "excel", "r", "scala", "spark", "kafka",
            "git", "linux", "bash", "c++", "go", "rust", "swift",
            "statistics", "data visualization", "data analysis",
        ]
        skills = [s for s in known_skills if s in text_lower]

    return {
        "candidate_id": "candidate_001",
        "full_name": full_name or "Candidate",
        "current_title": current_title or "",
        "location": location or "",
        "education": education,
        "years_experience": years_experience,
        "skills": skills,
        "tools": tools,
        "domains": domains,
        "certifications": [],
        "projects": [],
        "seniority": seniority,
        "summary": text[:500],
    }


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
    email_lower = payload.email.strip().lower()
    existing = db.query(User).filter(User.email == email_lower).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = User(
        email=email_lower,
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
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()

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
# Password Reset (forgot password)
# -----------------------------

@app.post(
    "/auth/forgot-password",
    tags=["Auth"],
    summary="Request a password reset email",
    status_code=200,
)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Generates a one-time reset token and emails it to the user.
    Always returns 200 — we never reveal whether the email exists
    (prevents user enumeration).
    """
    import hashlib
    import secrets
    from datetime import datetime, timedelta, timezone

    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        # Invalidate any existing unused tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
        ).delete()
        db.flush()

        # Generate a secure random token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used=False,
        )
        db.add(reset_record)
        db.commit()

        # Send email — log outcome clearly to the backend terminal
        email_ok = False
        email_error = ""
        try:
            send_password_reset_email(to_email=user.email, token=raw_token)
            email_ok = True
            print(f"\n[PASSWORD RESET] Email sent to {user.email}")
        except Exception as exc:
            email_error = str(exc)
            # Always print the token to the terminal so it can be used even
            # when email is not configured yet (development convenience).
            print(f"\n{'='*60}")
            print(f"[PASSWORD RESET] Email delivery failed: {email_error}")
            print(f"[PASSWORD RESET] Use this token manually for {user.email}:")
            print(f"  TOKEN: {raw_token}")
            print(f"{'='*60}\n")

        if email_ok:
            return {"message": "Reset link sent — check your inbox (also your spam folder)."}
        else:
            # Return the token directly so the user can paste it immediately.
            # In production you would remove the token from the response and
            # fix the email config instead.
            return {
                "message": (
                    "⚠️ Email could not be sent (email not configured). "
                    "Copy the token below and paste it into the reset form."
                ),
                "dev_token": raw_token,
                "error_detail": email_error,
            }

    return {"message": "If that email is registered, a reset link has been sent."}


@app.post(
    "/auth/reset-password",
    tags=["Auth"],
    summary="Reset password using token from email",
    status_code=200,
)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Validates the reset token and sets a new password.
    Token must be unused and not expired.
    """
    import hashlib
    from datetime import datetime, timezone

    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()

    record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
    ).first()

    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    if record.used:
        raise HTTPException(status_code=400, detail="This reset token has already been used.")

    now = datetime.now(timezone.utc)
    expires = record.expires_at
    # Make timezone-aware for comparison if needed
    if expires.tzinfo is None:
        from datetime import timezone as tz
        expires = expires.replace(tzinfo=tz.utc)

    if now > expires:
        raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new one.")

    # Update password
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token.")

    user.password_hash = hash_password(payload.new_password)
    record.used = True
    db.commit()

    return {"message": "Password updated successfully. You can now log in with your new password."}


@app.post(
    "/auth/change-password",
    tags=["Auth"],
    summary="Change password (must be logged in)",
    status_code=200,
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Allows an authenticated user to change their password.
    Requires current password for verification.
    """
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must be different from your current password.")

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password changed successfully."}


# -----------------------------
# Profiles (multi-profile per user)
# -----------------------------

def _record_to_response(user_id: int, record: CandidateProfileRecord) -> SavedProfileResponse:
    """Convert a DB record into the SavedProfileResponse schema."""
    return SavedProfileResponse(
        user_id=user_id,
        candidate_id=record.candidate_id,
        profile_name=record.profile_name or "My Profile",
        full_name=record.full_name or "",
        current_title=record.current_title or "",
        location=record.location or "",
        education=record.education,
        years_experience=record.years_experience or 0,
        skills=_json_load(record.skills_json),
        tools=_json_load(record.tools_json),
        domains=_json_load(record.domains_json),
        certifications=_json_load(record.certifications_json),
        projects=_json_load(record.projects_json),
        seniority=record.seniority,
        summary=record.summary or "",
    )


@app.get(
    "/profiles",
    response_model=ProfileListResponse,
    tags=["Profile"],
    summary="List all candidate profiles for current user",
)
def list_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileListResponse:
    records = db.query(CandidateProfileRecord).filter(
        CandidateProfileRecord.user_id == current_user.id
    ).all()

    items = [
        ProfileListItem(
            candidate_id=r.candidate_id,
            profile_name=r.profile_name or "My Profile",
            current_title=r.current_title or "",
            full_name=r.full_name or "",
        )
        for r in records
    ]

    return ProfileListResponse(count=len(items), profiles=items)


@app.post(
    "/profiles",
    response_model=SavedProfileResponse,
    tags=["Profile"],
    summary="Create a new candidate profile (system assigns candidate_id)",
    status_code=201,
)
def create_profile(
    payload: SavedProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedProfileResponse:
    import uuid as _uuid

    record = CandidateProfileRecord(
        user_id=current_user.id,
        candidate_id=str(_uuid.uuid4()),   # system-generated, never editable
        profile_name=payload.profile_name,
        full_name=payload.full_name,
        current_title=payload.current_title,
        location=payload.location,
        education=payload.education,
        years_experience=payload.years_experience,
        skills_json=_json_dump(payload.skills),
        tools_json=_json_dump(payload.tools),
        domains_json=_json_dump(payload.domains),
        certifications_json=_json_dump(payload.certifications),
        projects_json=_json_dump(payload.projects),
        seniority=payload.seniority,
        summary=payload.summary,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return _record_to_response(current_user.id, record)


@app.get(
    "/profiles/{candidate_id}",
    response_model=SavedProfileResponse,
    tags=["Profile"],
    summary="Load a specific candidate profile by its ID",
)
def get_profile(
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedProfileResponse:
    record = db.query(CandidateProfileRecord).filter(
        CandidateProfileRecord.candidate_id == candidate_id,
        CandidateProfileRecord.user_id == current_user.id,
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return _record_to_response(current_user.id, record)


@app.put(
    "/profiles/{candidate_id}",
    response_model=SavedProfileResponse,
    tags=["Profile"],
    summary="Update an existing candidate profile",
)
def update_profile(
    candidate_id: str,
    payload: SavedProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedProfileResponse:
    record = db.query(CandidateProfileRecord).filter(
        CandidateProfileRecord.candidate_id == candidate_id,
        CandidateProfileRecord.user_id == current_user.id,
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # candidate_id is never updated — it is immutable
    record.profile_name = payload.profile_name
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

    return _record_to_response(current_user.id, record)


@app.delete(
    "/profiles/{candidate_id}",
    tags=["Profile"],
    summary="Delete a candidate profile",
    status_code=204,
    response_class=Response,
)
def delete_profile(
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    record = db.query(CandidateProfileRecord).filter(
        CandidateProfileRecord.candidate_id == candidate_id,
        CandidateProfileRecord.user_id == current_user.id,
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Profile not found.")

    db.delete(record)
    db.commit()
    return Response(status_code=204)


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
    # Resolve candidate payload: structured object takes precedence over raw text.
    if payload.candidate is not None:
        candidate_payload = payload.candidate.model_dump()
    elif payload.resume_text:
        candidate_payload = _parse_resume_text(payload.resume_text)
    else:
        raise HTTPException(
            status_code=422,
            detail="Provide either 'candidate' (structured) or 'resume_text' (raw text).",
        )

    csv_path = _find_latest_jobs_dataset(payload.dataset_path)
    jobs = _load_jobs_from_csv(csv_path, limit_jobs=payload.limit_jobs)

    results = recommend_jobs_for_candidate(
        candidate_payload=candidate_payload,
        jobs_payload=jobs,
        preferences_payload=payload.preferences,
        top_k=payload.top_k,
    )

    return RecommendationResponse(
        count=len(results),
        recommendations=results,
    )


# -----------------------------
# Resume
# -----------------------------

@app.post(
    "/resume/parse",
    tags=["Resume"],
    summary="Upload a resume (PDF / DOCX / TXT) and extract candidate profile fields",
)
async def parse_resume_upload(
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """
    Accepts a resume file, extracts all candidate fields, and returns:
    - extracted_profile: structured candidate data ready to fill the profile form
    - completeness: score (0-100) + list of missing fields
    - raw_text_preview: first 800 chars of extracted text (for debugging)
    """
    allowed = {".pdf", ".docx", ".txt"}
    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{suffix}'. Please upload PDF, DOCX, or TXT.",
        )

    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    if len(file_bytes) > 10 * 1024 * 1024:   # 10 MB limit
        raise HTTPException(status_code=422, detail="File too large. Maximum size is 10 MB.")

    try:
        result = parse_resume(file_bytes, file.filename or "resume.pdf")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {exc}")

    return result


@app.post(
    "/profile/completeness",
    tags=["Resume"],
    summary="Compute completeness score for a candidate profile (0–100)",
)
def profile_completeness(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pass any candidate profile dict and receive back:
    - score (0–100)
    - filled list
    - missing list with labels and weights
    """
    return compute_profile_completeness(payload)


# -----------------------------
# Live Jobs (JSearch)
# -----------------------------

def _get_jsearch_client() -> JSearchClient:
    """
    Load JSearch config from sources.yaml and return a ready client.
    Raises HTTPException if JSearch is not configured or disabled.
    """
    import yaml

    try:
        with open("configs/sources.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="configs/sources.yaml not found.")

    jsearch_cfg = config.get("sources", {}).get("jsearch", {})

    if not jsearch_cfg.get("enabled", False):
        raise HTTPException(
            status_code=503,
            detail="JSearch is disabled. Set sources.jsearch.enabled: true in configs/sources.yaml.",
        )

    import os
    api_key = os.environ.get("JSEARCH_API_KEY", "").strip() or jsearch_cfg.get("api_key", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="JSearch API key is missing.",
        )

    return JSearchClient(
        api_key=api_key,
        host=jsearch_cfg.get("host", "jsearch.p.rapidapi.com"),
        base_url=jsearch_cfg.get("base_url", "https://jsearch.p.rapidapi.com"),
        request_timeout_seconds=jsearch_cfg.get("request_timeout_seconds", 15),
        max_results_per_query=jsearch_cfg.get("max_results_per_query", 10),
    )


@app.post(
    "/recommendations/live",
    response_model=RecommendationResponse,
    tags=["Live"],
    summary="Fetch real-time jobs and rank them for a candidate",
)
def get_live_recommendations(payload: LiveRecommendationRequest) -> RecommendationResponse:
    """
    1. Calls JSearch API with the candidate's search_query + location.
    2. Normalizes the live job results into the unified schema.
    3. Runs the full matching engine against the candidate profile.
    4. Returns results sorted by match score descending.
    """
    try:
        return _live_recommendations_inner(payload)
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        print(f"\n[/recommendations/live ERROR]\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")


def _live_recommendations_inner(payload: LiveRecommendationRequest) -> RecommendationResponse:
    client = _get_jsearch_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Live job search is not configured. Check sources.yaml → jsearch section.",
        )

    raw_jobs = client.search_jobs(
        query=payload.search_query,
        location=payload.location or "",
        date_posted=payload.date_posted or "all",
        num_pages=1,
    )
    jobs = client.normalize_jobs(raw_jobs)

    if not jobs:
        return RecommendationResponse(count=0, recommendations=[], dataset_path="live")

    prefs = payload.preferences.dict() if payload.preferences else None
    top_k = payload.top_k or 5

    # recommend_jobs_for_candidate handles parsing internally and returns
    # flat dicts with all fields already set (score, fit_label, skills, etc.)
    results = recommend_jobs_for_candidate(
        candidate_payload=payload.candidate.dict(),
        jobs_payload=jobs,
        preferences_payload=prefs,
        top_k=top_k,
    )

    # Results are already flat — pass them directly to the response schema
    items = results

    return RecommendationResponse(
        count=len(items),
        recommendations=items,
        dataset_path="live",
    )
