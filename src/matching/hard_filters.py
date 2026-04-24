from __future__ import annotations

from typing import Any, Dict, List


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


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_list(values) -> List[str]:
    if not values:
        return []
    return sorted(set(str(v).strip().lower() for v in values if str(v).strip()))


def check_required_skills(job_required_skills: List[str], candidate_skills: List[str]) -> Dict:
    job_required = set(_normalize_list(job_required_skills))
    candidate = set(_normalize_list(candidate_skills))

    matched = sorted(job_required & candidate)
    missing = sorted(job_required - candidate)

    return {
        "required_skills_total": len(job_required),
        "required_skills_matched": matched,
        "required_skills_missing": missing,
        "passed": len(missing) == 0,
    }


def check_experience(job_years_required, candidate_years) -> Dict:
    if job_years_required is None:
        return {
            "job_years_required": None,
            "candidate_years": candidate_years,
            "passed": True,
            "gap": 0,
        }

    if candidate_years is None:
        return {
            "job_years_required": job_years_required,
            "candidate_years": None,
            "passed": False,
            "gap": job_years_required,
        }

    try:
        job_years_required = float(job_years_required)
        candidate_years = float(candidate_years)
    except Exception:
        return {
            "job_years_required": job_years_required,
            "candidate_years": candidate_years,
            "passed": False,
            "gap": None,
        }

    gap = candidate_years - job_years_required

    return {
        "job_years_required": job_years_required,
        "candidate_years": candidate_years,
        "passed": candidate_years >= job_years_required,
        "gap": gap,
    }


def check_education(job_education, candidate_education) -> Dict:
    if not job_education:
        return {
            "job_education": None,
            "candidate_education": candidate_education,
            "passed": True,
        }

    if not candidate_education:
        return {
            "job_education": job_education,
            "candidate_education": None,
            "passed": False,
        }

    job_rank = EDUCATION_ORDER.get(_normalize_text(job_education))
    candidate_rank = EDUCATION_ORDER.get(_normalize_text(candidate_education))

    if job_rank is None or candidate_rank is None:
        return {
            "job_education": job_education,
            "candidate_education": candidate_education,
            "passed": False,
        }

    return {
        "job_education": job_education,
        "candidate_education": candidate_education,
        "passed": candidate_rank >= job_rank,
    }


def run_hard_filters(job_features: Dict, candidate_features: Dict) -> Dict:
    job_years_required = _first_present(
        job_features.get("years_experience_required"),
        job_features.get("years_experience_extracted"),
    )

    job_education_required = _first_present(
        job_features.get("education_required"),
        job_features.get("education_extracted"),
    )

    skill_check = check_required_skills(
        job_features.get("required_skills", []),
        candidate_features.get("skills", []),
    )

    experience_check = check_experience(
        job_years_required,
        candidate_features.get("years_experience"),
    )

    education_check = check_education(
        job_education_required,
        candidate_features.get("education"),
    )

    overall_pass = (
        skill_check["passed"]
        and experience_check["passed"]
        and education_check["passed"]
    )

    return {
        "passed": overall_pass,
        "skill_check": skill_check,
        "experience_check": experience_check,
        "education_check": education_check,
    }