from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Full name cannot be empty.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Password cannot be empty.")
        return value


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: str
    full_name: str


class UserMeResponse(BaseModel):
    id: int
    email: str
    full_name: str


class SavedProfileRequest(BaseModel):
    candidate_id: str = Field(default="", max_length=100)
    full_name: str = Field(default="", max_length=100)
    current_title: str = Field(default="", max_length=100)
    location: str = Field(default="", max_length=100)
    education: Optional[str] = None
    years_experience: int = Field(default=0, ge=0, le=60)
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    seniority: Optional[str] = None
    summary: Optional[str] = None

    @field_validator("candidate_id", "full_name", "current_title", "location", mode="before")
    @classmethod
    def strip_optional_text(cls, value) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("education", "seniority", "summary", mode="before")
    @classmethod
    def strip_optional_nullable_text(cls, value):
        if value is None:
            return None
        value = str(value).strip()
        return value if value else None


class SavedProfileResponse(BaseModel):
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


class PreferenceRequest(BaseModel):
    preferred_titles: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    preferred_workplace_types: List[str] = Field(default_factory=list)
    preferred_domains: List[str] = Field(default_factory=list)
    preferred_seniority: Optional[str] = None
    min_score: int = Field(default=50, ge=0, le=100)

    @field_validator("preferred_seniority", mode="before")
    @classmethod
    def strip_optional_preferred_seniority(cls, value):
        if value is None:
            return None
        value = str(value).strip()
        return value if value else None


class PreferenceResponse(BaseModel):
    user_id: int
    preferred_titles: List[str]
    preferred_locations: List[str]
    preferred_workplace_types: List[str]
    preferred_domains: List[str]
    preferred_seniority: Optional[str] = None
    min_score: int