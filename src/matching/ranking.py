from __future__ import annotations

from typing import Dict

# Import hard-filter engine.
from src.matching.hard_filters import run_hard_filters

# Import weighted scoring engine.
from src.matching.scoring import compute_match_score

# Import explanation generator.
from src.matching.explanations import build_match_explanation


def rank_candidate_for_job(
    job_features: Dict,
    candidate_features: Dict,
) -> Dict:
    """
    Run the full matching pipeline for a candidate-job pair.
    """

    # ----------------------------------------
    # Step 1:
    # Run strict pass/fail validation.
    # ----------------------------------------
    hard_filter_results = run_hard_filters(
        job_features,
        candidate_features,
    )

    # ----------------------------------------
    # Step 2:
    # Compute weighted similarity score.
    # ----------------------------------------
    scoring_results = compute_match_score(
        job_features,
        candidate_features,
    )

    # ----------------------------------------
    # Step 3:
    # Generate human-readable explanations.
    # ----------------------------------------
    explanation_results = build_match_explanation(
        job_features,
        candidate_features,
    )

    # ----------------------------------------
    # Step 4:
    # Combine everything into one unified result.
    # ----------------------------------------
    return {

        # Job identifier.
        "job_id": (
            job_features.get("job_uid")
            or
            job_features.get("job_id")
        ),

        # Candidate identifier.
        "candidate_id": candidate_features.get(
            "candidate_id"
        ),

        # Pass/fail validation results.
        "hard_filters": hard_filter_results,

        # Weighted score + fit label.
        "match_score": scoring_results,

        # Human-readable explanations.
        "explanation": explanation_results,
    }