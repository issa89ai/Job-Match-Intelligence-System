from __future__ import annotations

from typing import Any, Dict, List, Optional

# Convert parsed candidate profile into matching-ready features.
from src.candidate.feature_builder import build_candidate_features

# Parse and normalize raw candidate input.
from src.candidate.parser import parse_candidate_profile

# Reuse the single-job matching engine.
from src.matching.ranking import rank_candidate_for_job


def _normalize_text(value: Optional[str]) -> str:
    """
    Normalize text for preference comparison.
    """
    return (value or "").strip().lower()


def _normalize_list(values: Optional[List[str]]) -> List[str]:
    """
    Normalize preference/job list values.
    """
    if not values:
        return []

    return [
        str(v).strip().lower()
        for v in values
        if str(v).strip()
    ]


def _title_matches_preferences(
    job_title: str,
    preferred_titles: List[str],
) -> bool:
    """
    Check if job title matches any preferred title.
    """

    # If user has no preferred titles, do not filter by title.
    if not preferred_titles:
        return True

    title_norm = _normalize_text(job_title)

    for preferred_title in preferred_titles:
        pref_norm = _normalize_text(preferred_title)

        # Partial match:
        # "data scientist" matches "senior data scientist"
        if pref_norm and pref_norm in title_norm:
            return True

    return False


def _job_matches_preferences(
    job: Dict[str, Any],
    score: float,
    preferences: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Return True if job passes preference filtering.
    """

    # No preferences means accept all jobs.
    if not preferences:
        return True

    # Normalize preference fields.
    preferred_titles = _normalize_list(
        preferences.get("preferred_titles")
    )

    preferred_locations = _normalize_list(
        preferences.get("preferred_locations")
    )

    preferred_workplace_types = _normalize_list(
        preferences.get("preferred_workplace_types")
    )

    preferred_domains = _normalize_list(
        preferences.get("preferred_domains")
    )

    preferred_seniority = _normalize_text(
        preferences.get("preferred_seniority")
    )

    min_score = preferences.get("min_score", 0) or 0

    # Normalize job fields.
    job_title = _normalize_text(job.get("title"))
    job_location = _normalize_text(job.get("location"))
    job_workplace_type = _normalize_text(job.get("workplace_type"))
    job_seniority = _normalize_text(job.get("seniority"))
    job_domains = _normalize_list(job.get("domains"))

    # Filter by minimum score.
    if score < min_score:
        return False

    # Filter by preferred title.
    if preferred_titles and not _title_matches_preferences(
        job_title,
        preferred_titles,
    ):
        return False

    # Filter by exact location.
    if preferred_locations and job_location not in preferred_locations:
        return False

    # Filter by exact workplace type.
    if preferred_workplace_types and job_workplace_type not in preferred_workplace_types:
        return False

    # Filter by exact seniority.
    if preferred_seniority and job_seniority != preferred_seniority:
        return False

    # Filter by domain overlap.
    if preferred_domains:
        if not any(domain in preferred_domains for domain in job_domains):
            return False

    return True


def recommend_jobs_for_candidate(
    candidate_payload: Dict[str, Any],
    jobs_payload: List[Dict[str, Any]],
    preferences_payload: Optional[Dict[str, Any]] = None,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Rank many jobs for one candidate using the existing matching engine,
    then filter by user preferences and return top results.
    """

    # Step 1: Parse raw candidate profile.
    candidate = parse_candidate_profile(candidate_payload)

    # Step 2: Build matching-ready candidate features.
    candidate_features = build_candidate_features(candidate)

    results: List[Dict[str, Any]] = []

    # Step 3: Match candidate against each job.
    for job in jobs_payload:
        try:
            match_result = rank_candidate_for_job(
                job,
                candidate_features,
            )

            score = match_result.get("match_score", {}).get("score", 0)

            # Step 4: Apply user preference filters.
            if not _job_matches_preferences(
                job,
                score,
                preferences_payload,
            ):
                continue

            # Step 5: Build simplified recommendation item.
            recommendation = {
                "job_id": job.get("job_id", ""),
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "workplace_type": job.get("workplace_type", ""),
                "score": score,
                "fit_label": match_result.get("match_score", {}).get(
                    "fit_label",
                    "Unknown",
                ),
                "hard_filters_passed": match_result.get(
                    "hard_filters",
                    {},
                ).get("passed", False),
                "matched_required_skills": match_result.get(
                    "explanation",
                    {},
                ).get("matched_required_skills", []),
                "missing_required_skills": match_result.get(
                    "explanation",
                    {},
                ).get("missing_required_skills", []),
                "recommendations": match_result.get(
                    "explanation",
                    {},
                ).get("recommendations", []),

                # Keep full result for debugging/details.
                "full_result": match_result,
            }

            results.append(recommendation)

        except Exception:
            # If one job fails, skip it and continue ranking others.
            continue

    # Step 6: Sort jobs by highest score.
    results.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    # Step 7: Return only top K jobs.
    return results[:top_k]