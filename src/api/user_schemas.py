from __future__ import annotations

from typing import List, Optional

# BaseModel = Pydantic schema base class
# EmailStr = validates email format
# Field = adds validation constraints
# field_validator = custom validation logic
from pydantic import BaseModel, EmailStr, Field, field_validator


# =========================================================
# Register Request
# =========================================================

class RegisterRequest(BaseModel):
    """
    Request schema for creating a new user account.
    """

    # EmailStr validates proper email format.
    email: EmailStr

    # Password must be between 8 and 128 characters.
    password: str = Field(..., min_length=8, max_length=128)

    # Full name must be between 2 and 100 characters.
    full_name: str = Field(..., min_length=2, max_length=100)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        """
        Remove spaces and ensure name is not empty.
        """
        value = value.strip()

        if not value:
            raise ValueError("Full name cannot be empty.")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        Remove spaces and validate password length.
        """
        value = value.strip()

        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters.")

        return value


# =========================================================
# Login Request
# =========================================================

class LoginRequest(BaseModel):
    """
    Request schema for user login.
    """

    email: EmailStr

    # Login password only needs to be non-empty.
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        Ensure password is not blank.
        """
        value = value.strip()

        if not value:
            raise ValueError("Password cannot be empty.")

        return value


# =========================================================
# Auth Response
# =========================================================

class AuthResponse(BaseModel):
    """
    Response returned after login/register.
    """

    # JWT token returned to frontend.
    access_token: str

    # Token type used in Authorization header.
    token_type: str = "bearer"

    user_email: str

    full_name: str


# =========================================================
# Current User Response
# =========================================================

class UserMeResponse(BaseModel):
    """
    Response for /me endpoint.
    """

    id: int
    email: str
    full_name: str


# =========================================================
# Saved Candidate Profile Request
# =========================================================

class SavedProfileRequest(BaseModel):
    """
    Request schema for saving candidate profile.
    """

    candidate_id: str = Field(default="", max_length=100)
    full_name: str = Field(default="", max_length=100)
    current_title: str = Field(default="", max_length=100)
    location: str = Field(default="", max_length=100)

    education: Optional[str] = None

    # Experience must be between 0 and 60.
    years_experience: int = Field(default=0, ge=0, le=60)

    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)

    seniority: Optional[str] = None
    summary: Optional[str] = None

    @field_validator(
        "candidate_id",
        "full_name",
        "current_title",
        "location",
        mode="before",
    )
    @classmethod
    def strip_optional_text(cls, value) -> str:
        """
        Convert None to empty string and strip spaces.
        """
        if value is None:
            return ""

        return str(value).strip()

    @field_validator(
        "education",
        "seniority",
        "summary",
        mode="before",
    )
    @classmethod
    def strip_optional_nullable_text(cls, value):
        """
        Convert blank nullable fields to None.
        """
        if value is None:
            return None

        value = str(value).strip()

        return value if value else None


# =========================================================
# Saved Candidate Profile Response
# =========================================================

class SavedProfileResponse(BaseModel):
    """
    Response returned after saving/loading candidate profile.
    """

    user_id: int
    candidate_id: str
    full_name: str
    current_title: str
    location: str
    education: Optional[str] = None
    years_experience: int

    skills: List[str]
    tools: List[str]
    domains: List[str]
    certifications: List[str]
    projects: List[str]

    seniority: Optional[str] = None
    summary: Optional[str] = None


# =========================================================
# Preference Request
# =========================================================

class PreferenceRequest(BaseModel):
    """
    Request schema for saving job recommendation preferences.
    """

    preferred_titles: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    preferred_workplace_types: List[str] = Field(default_factory=list)
    preferred_domains: List[str] = Field(default_factory=list)

    preferred_seniority: Optional[str] = None

    # Minimum match score must be 0–100.
    min_score: int = Field(default=50, ge=0, le=100)

    @field_validator("preferred_seniority", mode="before")
    @classmethod
    def strip_optional_preferred_seniority(cls, value):
        """
        Convert blank preferred seniority to None.
        """
        if value is None:
            return None

        value = str(value).strip()

        return value if value else None


# =========================================================
# Preference Response
# =========================================================

class PreferenceResponse(BaseModel):
    """
    Response returned after saving/loading preferences.
    """

    user_id: int
    preferred_titles: List[str]
    preferred_locations: List[str]
    preferred_workplace_types: List[str]
    preferred_domains: List[str]
    preferred_seniority: Optional[str] = None
    min_score: int