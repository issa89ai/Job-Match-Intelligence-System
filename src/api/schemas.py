from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class CandidateProfileInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "candidate_id": "cand_001",
                "full_name": "Ahmad",
                "current_title": "Senior Data Scientist",
                "location": "Ottawa",
                "education": "Master",
                "years_experience": 6,
                "skills": ["python", "sql", "machine learning", "ai"],
                "tools": ["pandas"],
                "domains": ["ai"],
                "certifications": [],
                "projects": [],
                "seniority": "",
                "summary": "Built end-to-end machine learning and analytics projects."
            }
        }
    )

    candidate_id: str = Field(default="candidate_001", description="Unique candidate identifier.")
    full_name: str = Field(default="", description="Candidate full name.")
    current_title: str = Field(default="", description="Candidate current or most recent job title.")
    location: str = Field(default="", description="Candidate location.")
    education: Optional[str] = Field(default=None, description="Education level: high_school, associate, bachelor, master, phd.")
    years_experience: Optional[int] = Field(default=None, description="Total years of professional experience.")

    skills: List[str] = Field(default_factory=list, description="Core candidate skills.")
    tools: List[str] = Field(default_factory=list, description="Tools and technologies used by candidate.")
    domains: List[str] = Field(default_factory=list, description="Candidate domain areas.")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications.")
    projects: List[str] = Field(default_factory=list, description="Relevant projects.")
    seniority: Optional[str] = Field(default=None, description="Optional explicit seniority: intern, entry, mid, senior, manager.")
    summary: str = Field(default="", description="Short candidate summary.")


class JobFeaturesInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_uid": "test_job",
                "title_raw": "Account Executive, AI Sales",
                "required_skills": ["enterprise", "sales"],
                "preferred_skills": [],
                "other_skills_found": ["ai", "communication"],
                "years_experience_extracted": 10,
                "education_extracted": None,
                "seniority_inferred": "senior"
            }
        }
    )

    job_uid: str = Field(default="job_001", description="Unique job identifier.")
    title_raw: str = Field(default="", description="Original job title.")
    required_skills: List[str] = Field(default_factory=list, description="Required job skills.")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred or nice-to-have skills.")
    other_skills_found: List[str] = Field(default_factory=list, description="Other detected skills from extraction.")
    years_experience_extracted: Optional[int] = Field(default=None, description="Minimum years of experience required.")
    education_extracted: Optional[str] = Field(default=None, description="Minimum education requirement.")
    seniority_inferred: Optional[str] = Field(default=None, description="Inferred seniority level from job extraction.")


class MatchRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job": {
                    "job_uid": "test_job",
                    "title_raw": "Account Executive, AI Sales",
                    "required_skills": ["enterprise", "sales"],
                    "preferred_skills": [],
                    "other_skills_found": ["ai", "communication"],
                    "years_experience_extracted": 10,
                    "education_extracted": None,
                    "seniority_inferred": "senior"
                },
                "candidate": {
                    "candidate_id": "cand_001",
                    "full_name": "Ahmad",
                    "current_title": "Senior Data Scientist",
                    "location": "Ottawa",
                    "education": "Master",
                    "years_experience": 6,
                    "skills": ["python", "sql", "machine learning", "ai"],
                    "tools": ["pandas"],
                    "domains": ["ai"],
                    "certifications": [],
                    "projects": [],
                    "seniority": "",
                    "summary": "Built end-to-end machine learning and analytics projects."
                }
            }
        }
    )

    job: JobFeaturesInput
    candidate: CandidateProfileInput


class HealthResponse(BaseModel):
    status: str
    message: str


class MatchResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "test_job",
                "candidate_id": "cand_001",
                "hard_filters": {
                    "passed": False,
                    "skill_check": {
                        "required_skills_total": 2,
                        "required_skills_matched": [],
                        "required_skills_missing": ["enterprise", "sales"],
                        "passed": False
                    },
                    "experience_check": {
                        "job_years_required": 10,
                        "candidate_years": 6,
                        "passed": False,
                        "gap": -4
                    },
                    "education_check": {
                        "job_education": None,
                        "candidate_education": "master",
                        "passed": True
                    }
                },
                "match_score": {
                    "score": 52.0,
                    "fit_label": "Partial Fit",
                    "component_scores": {
                        "required_skill_score": 0.0,
                        "preferred_skill_score": 1.0,
                        "experience_score": 0.6,
                        "education_score": 1.0,
                        "seniority_score": 1.0
                    },
                    "weights": {
                        "required_skill_score": 0.4,
                        "preferred_skill_score": 0.15,
                        "experience_score": 0.2,
                        "education_score": 0.1,
                        "seniority_score": 0.15
                    }
                },
                "explanation": {
                    "matched_required_skills": [],
                    "missing_required_skills": ["enterprise", "sales"],
                    "matched_preferred_skills": [],
                    "missing_preferred_skills": [],
                    "gaps": [
                        "Missing required skills: enterprise, sales",
                        "Experience gap: candidate has 6 years vs required 10"
                    ],
                    "recommendations": [
                        "Develop or highlight these required skills: enterprise, sales",
                        "Target roles with slightly lower experience requirements or strengthen project evidence."
                    ]
                }
            }
        }
    )

    job_id: Optional[str]
    candidate_id: Optional[str]
    hard_filters: Dict[str, Any]
    match_score: Dict[str, Any]
    explanation: Dict[str, Any]