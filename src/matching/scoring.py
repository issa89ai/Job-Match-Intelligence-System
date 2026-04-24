from __future__ import annotations

from typing import Any, Dict, List


SENIORITY_ORDER = {
    "intern": 1,
    "entry": 2,
    "junior": 2,
    "mid": 3,
    "senior": 4,
    "manager": 5,
}


EDUCATION_ORDER = {
    "high_school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
}


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _to_set(values) -> set:
    if not values:
        return set()
    return {str(v).strip().lower() for v in values if str(v).strip()}


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def score_required_skills(job_required_skills: List[str], candidate_skills: List[str]) -> float:
    required = _to_set(job_required_skills)
    candidate = _to_set(candidate_skills)

    if not required:
        return 1.0

    matched_count = len(required & candidate)
    total_required = len(required)

    base_score = matched_count / total_required

    # Stronger penalty when required skills are missing
    if matched_count == 0:
        return 0.0

    if base_score < 0.5:
        return base_score * 0.75

    return base_score


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

    try:
        job_years_required = float(job_years_required)
        candidate_years = float(candidate_years)
    except Exception:
        return 0.0

    if job_years_required <= 0:
        return 1.0

    if candidate_years >= job_years_required:
        return 1.0

    gap = job_years_required - candidate_years
    ratio = candidate_years / job_years_required

    # Small gap is acceptable, large gap is penalized harder
    if gap <= 1:
        return max(0.75, ratio)

    if gap <= 3:
        return max(0.50, ratio * 0.9)

    return max(0.0, ratio * 0.75)


def score_education(job_education, candidate_education) -> float:
    if not job_education:
        return 1.0

    if not candidate_education:
        return 0.0

    jr = EDUCATION_ORDER.get(_normalize_text(job_education))
    cr = EDUCATION_ORDER.get(_normalize_text(candidate_education))

    if jr is None or cr is None:
        return 0.5

    if cr >= jr:
        return 1.0

    diff = jr - cr
    return max(0.0, 1.0 - 0.35 * diff)


def score_seniority(job_seniority, candidate_seniority) -> float:
    if not job_seniority:
        return 1.0

    if not candidate_seniority:
        return 0.5

    jr = SENIORITY_ORDER.get(_normalize_text(job_seniority))
    cr = SENIORITY_ORDER.get(_normalize_text(candidate_seniority))

    if jr is None or cr is None:
        return 0.5

    if cr >= jr:
        return 1.0

    diff = jr - cr
    return max(0.0, 1.0 - 0.4 * diff)


def score_domain_alignment(job_domains: List[str], candidate_domains: List[str]) -> float:
    job_domain_set = _to_set(job_domains)
    candidate_domain_set = _to_set(candidate_domains)

    if not job_domain_set:
        return 1.0

    if not candidate_domain_set:
        return 0.5

    return len(job_domain_set & candidate_domain_set) / len(job_domain_set)


def compute_match_score(job_features: Dict, candidate_features: Dict) -> Dict:
    job_years_required = _first_present(
        job_features.get("years_experience_required"),
        job_features.get("years_experience_extracted"),
    )

    job_education_required = _first_present(
        job_features.get("education_required"),
        job_features.get("education_extracted"),
    )

    job_seniority = _first_present(
        job_features.get("seniority"),
        job_features.get("seniority_inferred"),
    )

    required_skill_score = score_required_skills(
        job_features.get("required_skills", []),
        candidate_features.get("skills", []),
    )

    preferred_skill_score = score_preferred_skills(
        job_features.get("preferred_skills", []),
        candidate_features.get("skills", []),
    )

    experience_score = score_experience(
        job_years_required,
        candidate_features.get("years_experience"),
    )

    education_score = score_education(
        job_education_required,
        candidate_features.get("education"),
    )

    seniority_score = score_seniority(
        job_seniority,
        candidate_features.get("seniority"),
    )

    domain_score = score_domain_alignment(
        job_features.get("domains", []),
        candidate_features.get("domains", []),
    )

    weights = {
        "required_skill_score": 0.38,
        "preferred_skill_score": 0.12,
        "experience_score": 0.20,
        "education_score": 0.08,
        "seniority_score": 0.12,
        "domain_score": 0.10,
    }

    weighted_score = (
        required_skill_score * weights["required_skill_score"]
        + preferred_skill_score * weights["preferred_skill_score"]
        + experience_score * weights["experience_score"]
        + education_score * weights["education_score"]
        + seniority_score * weights["seniority_score"]
        + domain_score * weights["domain_score"]
    )

    final_score = round(weighted_score * 100, 2)

    # Extra penalty if required skills are very weak
    if required_skill_score == 0:
        final_score = min(final_score, 45.0)
    elif required_skill_score < 0.5:
        final_score = min(final_score, 60.0)

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
            "domain_score": round(domain_score, 4),
        },
        "weights": weights,
    }