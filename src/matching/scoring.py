from __future__ import annotations

from typing import Dict, List


SENIORITY_ORDER = {
    "intern": 1,
    "entry": 2,
    "mid": 3,
    "senior": 4,
    "manager": 5,
}


def _to_set(values) -> set:
    if not values:
        return set()
    return {str(v).strip().lower() for v in values if str(v).strip()}


def score_required_skills(job_required_skills: List[str], candidate_skills: List[str]) -> float:
    required = _to_set(job_required_skills)
    candidate = _to_set(candidate_skills)

    if not required:
        return 1.0

    return len(required & candidate) / len(required)


def score_preferred_skills(job_preferred_skills: List[str], candidate_skills: List[str]) -> float:
    preferred = _to_set(job_preferred_skills)
    candidate = _to_set(candidate_skills)

    if not preferred:
        return 1.0

    return len(preferred & candidate) / len(preferred)


def score_experience(job_years_required, candidate_years) -> float:
    if job_years_required is None:
        return 1.0
    if candidate_years is None:
        return 0.0

    if candidate_years >= job_years_required:
        return 1.0

    ratio = candidate_years / max(job_years_required, 1)
    return max(0.0, min(ratio, 1.0))


def score_education(job_education, candidate_education) -> float:
    order = {
        "high_school": 1,
        "associate": 2,
        "bachelor": 3,
        "master": 4,
        "phd": 5,
    }

    if not job_education:
        return 1.0
    if not candidate_education:
        return 0.0

    jr = order.get(str(job_education).lower())
    cr = order.get(str(candidate_education).lower())

    if jr is None or cr is None:
        return 0.0

    if cr >= jr:
        return 1.0

    diff = jr - cr
    return max(0.0, 1.0 - 0.35 * diff)


def score_seniority(job_seniority, candidate_seniority) -> float:
    if not job_seniority:
        return 1.0
    if not candidate_seniority:
        return 0.0

    jr = SENIORITY_ORDER.get(str(job_seniority).lower())
    cr = SENIORITY_ORDER.get(str(candidate_seniority).lower())

    if jr is None or cr is None:
        return 0.0

    if cr >= jr:
        return 1.0

    diff = jr - cr
    return max(0.0, 1.0 - 0.4 * diff)


def compute_match_score(job_features: Dict, candidate_features: Dict) -> Dict:
    required_skill_score = score_required_skills(
        job_features.get("required_skills", []),
        candidate_features.get("skills", []),
    )

    preferred_skill_score = score_preferred_skills(
        job_features.get("preferred_skills", []),
        candidate_features.get("skills", []),
    )

    experience_score = score_experience(
        job_features.get("years_experience_extracted"),
        candidate_features.get("years_experience"),
    )

    education_score = score_education(
        job_features.get("education_extracted"),
        candidate_features.get("education"),
    )

    seniority_score = score_seniority(
        job_features.get("seniority_inferred"),
        candidate_features.get("seniority"),
    )

    weights = {
        "required_skill_score": 0.40,
        "preferred_skill_score": 0.15,
        "experience_score": 0.20,
        "education_score": 0.10,
        "seniority_score": 0.15,
    }

    weighted_score = (
        required_skill_score * weights["required_skill_score"]
        + preferred_skill_score * weights["preferred_skill_score"]
        + experience_score * weights["experience_score"]
        + education_score * weights["education_score"]
        + seniority_score * weights["seniority_score"]
    )

    final_score = round(weighted_score * 100, 2)

    if final_score >= 85:
        fit_label = "Strong Fit"
    elif final_score >= 70:
        fit_label = "Good Fit"
    elif final_score >= 50:
        fit_label = "Partial Fit"
    else:
        fit_label = "Weak Fit"

    return {
        "score": final_score,
        "fit_label": fit_label,
        "component_scores": {
            "required_skill_score": round(required_skill_score, 4),
            "preferred_skill_score": round(preferred_skill_score, 4),
            "experience_score": round(experience_score, 4),
            "education_score": round(education_score, 4),
            "seniority_score": round(seniority_score, 4),
        },
        "weights": weights,
    }