from __future__ import annotations

import json

from src.candidate.parser import parse_candidate_profile
from src.candidate.feature_builder import build_candidate_features


def main() -> None:
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
    features = build_candidate_features(candidate)

    print("[Phase 5] Candidate parsing completed.")
    print(json.dumps(features, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()