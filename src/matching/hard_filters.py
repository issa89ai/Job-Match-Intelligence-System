from __future__ import annotations

from typing import Any, Dict, List


# Education ranking used to compare candidate education with job requirement.
# Higher number = higher education level.
EDUCATION_ORDER = {
    "high_school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
}


def _first_present(*values: Any) -> Any:
    """
    Return the first value that is not None and not empty.
    Used because different pipeline stages may use different column names.
    """

    for value in values:
        if value is not None and value != "":
            return value

    return None


def _normalize_text(value: Any) -> str:
    """
    Normalize text for comparison.
    """

    return str(value or "").strip().lower()


def _normalize_list(values) -> List[str]:
    """
    Normalize list values: lowercase, trim, remove duplicates, sort.
    """

    if not values:
        return []

    return sorted(
        set(
            str(v).strip().lower()
            for v in values
            if str(v).strip()
        )
    )


def check_required_skills(
    job_required_skills: List[str],
    candidate_skills: List[str],
) -> Dict:
    """
    Check whether candidate has all required skills.
    """

    # Normalize both job required skills and candidate skills.
    job_required = set(_normalize_list(job_required_skills))
    candidate = set(_normalize_list(candidate_skills))

    # Skills that exist in both sets.
    matched = sorted(job_required & candidate)

    # Skills required by job but missing from candidate.
    missing = sorted(job_required - candidate)

    return {
        "required_skills_total": len(job_required),
        "required_skills_matched": matched,
        "required_skills_missing": missing,

        # Pass only if no required skills are missing.
        "passed": len(missing) == 0,
    }


def check_experience(job_years_required, candidate_years) -> Dict:
    """
    Check whether candidate has enough years of experience.
    """

    # If job does not specify experience, pass automatically.
    if job_years_required is None:
        return {
            "job_years_required": None,
            "candidate_years": candidate_years,
            "passed": True,
            "gap": 0,
        }

    # If candidate has no experience value but job requires it, fail.
    if candidate_years is None:
        return {
            "job_years_required": job_years_required,
            "candidate_years": None,
            "passed": False,
            "gap": job_years_required,
        }

    try:
        # Convert values to numbers.
        job_years_required = float(job_years_required)
        candidate_years = float(candidate_years)

    except Exception:
        # If conversion fails, fail safely.
        return {
            "job_years_required": job_years_required,
            "candidate_years": candidate_years,
            "passed": False,
            "gap": None,
        }

    # Positive gap means candidate has more years than required.
    # Negative gap means candidate is short.
    gap = candidate_years - job_years_required

    return {
        "job_years_required": job_years_required,
        "candidate_years": candidate_years,
        "passed": candidate_years >= job_years_required,
        "gap": gap,
    }


def check_education(job_education, candidate_education) -> Dict:
    """
    Check whether candidate education meets the job education requirement.
    """

    # If job does not specify education, pass automatically.
    if not job_education:
        return {
            "job_education": None,
            "candidate_education": candidate_education,
            "passed": True,
        }

    # If job requires education but candidate has none, fail.
    if not candidate_education:
        return {
            "job_education": job_education,
            "candidate_education": None,
            "passed": False,
        }

    # Convert education levels to numeric ranks.
    job_rank = EDUCATION_ORDER.get(_normalize_text(job_education))
    candidate_rank = EDUCATION_ORDER.get(_normalize_text(candidate_education))

    # Unknown values fail safely.
    if job_rank is None or candidate_rank is None:
        return {
            "job_education": job_education,
            "candidate_education": candidate_education,
            "passed": False,
        }

    return {
        "job_education": job_education,
        "candidate_education": candidate_education,

        # Candidate passes if candidate education is equal or higher.
        "passed": candidate_rank >= job_rank,
    }


def run_hard_filters(job_features: Dict, candidate_features: Dict) -> Dict:
    """
    Run all hard filter checks and return combined result.
    """

    # Support both manually provided jobs and extracted jobs.
    job_years_required = _first_present(
        job_features.get("years_experience_required"),
        job_features.get("years_experience_extracted"),
    )

    # Support both manually provided jobs and extracted jobs.
    job_education_required = _first_present(
        job_features.get("education_required"),
        job_features.get("education_extracted"),
    )

    # Required skill filter.
    skill_check = check_required_skills(
        job_features.get("required_skills", []),
        candidate_features.get("skills", []),
    )

    # Experience filter.
    experience_check = check_experience(
        job_years_required,
        candidate_features.get("years_experience"),
    )

    # Education filter.
    education_check = check_education(
        job_education_required,
        candidate_features.get("education"),
    )

    # Overall pass only if ALL hard filters pass.
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