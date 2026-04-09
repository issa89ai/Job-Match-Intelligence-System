from __future__ import annotations

import json

from src.candidate.feature_builder import build_candidate_features
from src.candidate.parser import parse_candidate_profile
from src.matching.ranking import rank_candidate_for_job


def main() -> None:
    job_features = {
        "job_uid": "greenhouse::stripe::7532733",
        "title_raw": "Account Executive, AI Sales",
        "required_skills": ["enterprise", "sales"],
        "preferred_skills": [],
        "other_skills_found": ["ai", "communication", "negotiation", "presentation", "strategy"],
        "years_experience_extracted": 10,
        "education_extracted": None,
        "seniority_inferred": "senior",
    }

    raw_candidate = {
        "candidate_id": "cand_001",
        "full_name": "Ahmad Example",
        "current_title": "Senior Data Scientist",
        "location": "Ottawa, ON",
        "education": "Master",
        "years_experience": 6,
        "skills": [
            "python",
            "sql",
            "machine learning",
            "data analysis",
            "statistics",
            "ai",
            "communication",
            "strategy",
        ],
        "tools": [
            "pandas",
            "scikit-learn",
            "power bi",
            "git",
        ],
        "domains": [
            "ai",
            "data science",
            "analytics",
        ],
        "certifications": [
            "aws cloud practitioner",
        ],
        "projects": [
            "customer churn prediction deployment",
            "job match intelligence system",
        ],
        "seniority": "",
        "summary": "Built end-to-end machine learning and analytics projects using Python, SQL, FastAPI, Streamlit, and model deployment workflows.",
    }

    candidate = parse_candidate_profile(raw_candidate)
    candidate_features = build_candidate_features(candidate)

    result = rank_candidate_for_job(job_features, candidate_features)

    print("[Phase 6] Matching completed.")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()