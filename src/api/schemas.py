from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    message: str


class CandidateInput(BaseModel):
    candidate_id: str
    full_name: str
    current_title: str
    location: str
    education: Optional[str] = None
    years_experience: int = Field(..., ge=0)
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    seniority: Optional[str] = None
    summary: Optional[str] = None


class JobInput(BaseModel):
    job_id: str
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    workplace_type: Optional[str] = None
    domains: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    other_skills: List[str] = Field(default_factory=list)
    years_experience_required: Optional[int] = None
    education_required: Optional[str] = None
    seniority: Optional[str] = None


class MatchRequest(BaseModel):
    candidate: CandidateInput
    job: JobInput


class MatchResponse(BaseModel):
    job_id: Optional[str] = None
    candidate_id: Optional[str] = None
    hard_filters: Dict[str, Any]
    match_score: Dict[str, Any]
    explanation: Dict[str, Any]


class RecommendationRequest(BaseModel):
    candidate: CandidateInput
    jobs: List[JobInput]
    preferences: Optional[Dict[str, Any]] = None
    top_k: int = Field(default=10, ge=1, le=100)


class DatasetRecommendationRequest(BaseModel):
    candidate: CandidateInput
    preferences: Optional[Dict[str, Any]] = None
    top_k: int = Field(default=10, ge=1, le=100)
    limit_jobs: Optional[int] = Field(default=None, ge=1)
    dataset_path: Optional[str] = None


class RecommendationItem(BaseModel):
    job_id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    workplace_type: str = ""
    score: float = 0
    fit_label: str = "Unknown"
    hard_filters_passed: bool = False
    matched_required_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    full_result: Dict[str, Any] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    count: int
    recommendations: List[RecommendationItem]


class JobsPreviewResponse(BaseModel):
    count: int
    jobs: List[JobInput]
    dataset_path: str