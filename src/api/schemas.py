from __future__ import annotations

from typing import Any, Dict, List, Optional

# Pydantic is used for validation and serialization.
from pydantic import BaseModel, Field


# =========================================================
# Health Response
# =========================================================

class HealthResponse(BaseModel):
    """
    Response schema used by health-check endpoints.
    """

    status: str
    message: str


# =========================================================
# Candidate Input Schema
# =========================================================

class CandidateInput(BaseModel):
    """
    Standard candidate payload used by matching endpoints.
    """

    candidate_id: str

    full_name: str

    current_title: str

    location: str

    education: Optional[str] = None

    # Candidate years of experience.
    # ge=0 means value must be >= 0.
    years_experience: int = Field(..., ge=0)

    # Skills and profile attributes.
    skills: List[str] = Field(default_factory=list)

    tools: List[str] = Field(default_factory=list)

    domains: List[str] = Field(default_factory=list)

    certifications: List[str] = Field(default_factory=list)

    projects: List[str] = Field(default_factory=list)

    seniority: Optional[str] = None

    summary: Optional[str] = None


# =========================================================
# Job Input Schema
# =========================================================

class JobInput(BaseModel):
    """
    Standard job payload used by matching endpoints.
    """

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


# =========================================================
# Single Match Request
# =========================================================

class MatchRequest(BaseModel):
    """
    Request body for single candidate-job matching.
    """

    candidate: CandidateInput

    job: JobInput


# =========================================================
# Single Match Response
# =========================================================

class MatchResponse(BaseModel):
    """
    Response returned after matching candidate to one job.
    """

    job_id: Optional[str] = None

    candidate_id: Optional[str] = None

    # Hard filter results.
    hard_filters: Dict[str, Any]

    # Weighted score results.
    match_score: Dict[str, Any]

    # Human-readable explanations.
    explanation: Dict[str, Any]


# =========================================================
# Recommendation Request
# =========================================================

class RecommendationRequest(BaseModel):
    """
    Request body for ranking candidate against provided jobs.
    """

    candidate: CandidateInput

    jobs: List[JobInput]

    # Optional user preferences.
    preferences: Optional[Dict[str, Any]] = None

    # Number of top jobs to return.
    top_k: int = Field(default=10, ge=1, le=100)


# =========================================================
# Dataset Recommendation Request
# =========================================================

class DatasetRecommendationRequest(BaseModel):
    """
    Request body for ranking candidate against dataset jobs.

    Supply either a structured ``candidate`` object OR raw ``resume_text``.
    If both are provided, ``candidate`` takes precedence.
    """

    # Structured candidate (preferred).
    candidate: Optional[CandidateInput] = None

    # Raw resume text — backend will extract structured fields from it.
    resume_text: Optional[str] = None

    preferences: Optional[Dict[str, Any]] = None

    top_k: int = Field(default=10, ge=1, le=100)

    # Optional limit for dataset size.
    limit_jobs: Optional[int] = Field(default=None, ge=1)

    # Optional custom dataset path.
    dataset_path: Optional[str] = None


# =========================================================
# Recommendation Item
# =========================================================

class RecommendationItem(BaseModel):
    """
    One ranked recommendation result.
    """

    job_id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    workplace_type: str = ""

    # Final weighted score.
    score: float = 0
    fit_label: str = "Unknown"
    hard_filters_passed: bool = False

    matched_required_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Live job fields (populated when source is JSearch)
    source_url: str = ""
    employer_logo: str = ""
    description_snippet: str = ""
    date_posted: str = ""

    # Full detailed matching output.
    full_result: Dict[str, Any] = Field(default_factory=dict)


# =========================================================
# Recommendation Response
# =========================================================

class RecommendationResponse(BaseModel):
    """
    Response schema for recommendation endpoint.
    """

    count: int
    recommendations: List[RecommendationItem]
    dataset_path: str = ""


# =========================================================
# Jobs Preview Response
# =========================================================

class JobsPreviewResponse(BaseModel):
    """
    Response schema for previewing dataset jobs.
    """

    count: int

    jobs: List[JobInput]

    dataset_path: str


# =========================================================
# Live Recommendation Request
# =========================================================

class LiveRecommendationRequest(BaseModel):
    """
    Request body for live job recommendations via JSearch.

    The backend fetches real-time jobs from the web matching
    the search_query, then scores them against the candidate.
    """

    candidate: CandidateInput

    # Job title / keywords to search for live, e.g. "data scientist"
    search_query: str = Field(..., min_length=1)

    # Optional location filter, e.g. "New York" or "remote"
    location: str = ""

    # Optional preference filters (same as dataset recommendations)
    preferences: Optional[Dict[str, Any]] = None

    # How many top results to return
    top_k: int = Field(default=10, ge=1, le=50)

    # Date posted filter: "all", "today", "3days", "week", "month"
    date_posted: str = "all"