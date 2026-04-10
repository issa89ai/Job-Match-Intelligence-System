from __future__ import annotations

from fastapi import FastAPI

from src.api.schemas import HealthResponse, MatchRequest, MatchResponse
from src.candidate.feature_builder import build_candidate_features
from src.candidate.parser import parse_candidate_profile
from src.matching.ranking import rank_candidate_for_job


app = FastAPI(
    title="Job Match Intelligence API",
    description="""
An explainable API for matching candidates to jobs.

## Main capability
Submit:
- a structured job profile
- a structured candidate profile

Receive:
- hard filter results
- match score
- fit label
- skill gaps
- recommendations

Use the **/match** endpoint below.
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Matching",
            "description": "Core endpoint for explainable job-candidate matching."
        }
    ],
)


@app.get("/", response_model=HealthResponse, include_in_schema=False)
def root() -> HealthResponse:
    return HealthResponse(
        status="ok",
        message="Job Match Intelligence API is running."
    )


@app.get("/health", response_model=HealthResponse, include_in_schema=False)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        message="Service healthy."
    )


@app.post(
    "/match",
    response_model=MatchResponse,
    tags=["Matching"],
    summary="Match a candidate to a job",
    description="""
Runs the full matching pipeline and returns:

- hard filter checks
- overall match score
- fit label
- matched and missing skills
- gap analysis
- recommendations
""",
)
def match_candidate_to_job(payload: MatchRequest) -> MatchResponse:
    raw_candidate = payload.candidate.model_dump()
    job_features = payload.job.model_dump()

    candidate = parse_candidate_profile(raw_candidate)
    candidate_features = build_candidate_features(candidate)

    result = rank_candidate_for_job(job_features, candidate_features)

    return MatchResponse(**result)