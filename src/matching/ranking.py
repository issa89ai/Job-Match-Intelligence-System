from __future__ import annotations

from typing import Dict

from src.matching.explanations import build_match_explanation
from src.matching.hard_filters import run_hard_filters
from src.matching.scoring import compute_match_score


def rank_candidate_for_job(job_features: Dict, candidate_features: Dict) -> Dict:
    hard_filter_results = run_hard_filters(job_features, candidate_features)
    scoring_results = compute_match_score(job_features, candidate_features)
    explanation_results = build_match_explanation(job_features, candidate_features)

    return {
        "job_id": job_features.get("job_uid") or job_features.get("job_id"),
        "candidate_id": candidate_features.get("candidate_id"),
        "hard_filters": hard_filter_results,
        "match_score": scoring_results,
        "explanation": explanation_results,
    }