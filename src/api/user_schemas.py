from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: EmailStr
    full_name: str = ""


class UserMeResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str = ""


class SavedProfileRequest(BaseModel):
    candidate_id: str = "candidate_001"
    full_name: str = ""
    current_title: str = ""
    location: str = ""
    education: Optional[str] = None
    years_experience: Optional[int] = None
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    seniority: Optional[str] = None
    summary: str = ""


class SavedProfileResponse(SavedProfileRequest):
    user_id: int


class PreferenceRequest(BaseModel):
    preferred_titles: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    preferred_workplace_types: List[str] = Field(default_factory=list)
    preferred_domains: List[str] = Field(default_factory=list)
    preferred_seniority: Optional[str] = None
    min_score: int = 50


class PreferenceResponse(PreferenceRequest):
    user_id: int