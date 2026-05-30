from __future__ import annotations

from typing import Any, Dict, List


# Seniority ranking hierarchy.
SENIORITY_ORDER = {
    "intern": 1,
    "entry": 2,
    "junior": 2,
    "mid": 3,
    "senior": 4,
    "manager": 5,
}


# Education ranking hierarchy.
EDUCATION_ORDER = {
    "high_school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
}


def _first_present(*values: Any) -> Any:
    """
    Return first non-empty value.
    """

    for value in values:
        if value is not None and value != "":
            return value

    return None


def _to_set(values) -> set:
    """
    Normalize list into lowercase unique set.
    """

    if not values:
        return set()

    return {
        str(v).strip().lower()
        for v in values
        if str(v).strip()
    }


def _normalize_text(value: Any) -> str:
    """
    Normalize text safely.
    """

    return str(value or "").strip().lower()


def score_required_skills(
    job_required_skills: List[str],
    candidate_skills: List[str],
) -> float:
    """
    Score required skill coverage.
    """

    required = _to_set(job_required_skills)
    candidate = _to_set(candidate_skills)

    # No required skills listed → we cannot verify a match.
    # Return a neutral score (not perfect) to reflect the uncertainty.
    if not required:
        return 0.65

    matched_count = len(required & candidate)
    total_required = len(required)

    # Basic coverage ratio.
    base_score = matched_count / total_required

    # Severe penalty if candidate matches none.
    if matched_count == 0:
        return 0.0

    # Additional penalty if coverage is weak.
    if base_score < 0.5:
        return base_score * 0.75

    return base_score


def score_preferred_skills(
    job_preferred_skills: List[str],
    candidate_skills: List[str],
) -> float:
    """
    Score preferred skill coverage.
    """

    preferred = _to_set(job_preferred_skills)
    candidate = _to_set(candidate_skills)

    # No preferred skills → neutral uncertainty score.
    if not preferred:
        return 0.65

    return len(preferred & candidate) / len(preferred)


def score_experience(job_years_required, candidate_years) -> float:
    """
    Score experience alignment.
    """

    # No requirement means perfect score.
    if job_years_required is None:
        return 1.0

    # Missing candidate experience fails.
    if candidate_years is None:
        return 0.0

    try:
        job_years_required = float(job_years_required)
        candidate_years = float(candidate_years)

    except Exception:
        return 0.0

    if job_years_required <= 0:
        return 1.0

    # Candidate satisfies requirement.
    if candidate_years >= job_years_required:
        return 1.0

    # Candidate under requirement.
    gap = job_years_required - candidate_years
    ratio = candidate_years / job_years_required

    # Small gap tolerated.
    if gap <= 1:
        return max(0.75, ratio)

    # Medium gap penalized moderately.
    if gap <= 3:
        return max(0.50, ratio * 0.9)

    # Large gap heavily penalized.
    return max(0.0, ratio * 0.75)


def score_education(job_education, candidate_education) -> float:
    """
    Score education alignment.
    """

    if not job_education:
        return 1.0

    if not candidate_education:
        return 0.0

    jr = EDUCATION_ORDER.get(_normalize_text(job_education))
    cr = EDUCATION_ORDER.get(_normalize_text(candidate_education))

    # Unknown values → partial uncertainty score.
    if jr is None or cr is None:
        return 0.5

    # Candidate satisfies or exceeds requirement.
    if cr >= jr:
        return 1.0

    # Penalize education gap.
    diff = jr - cr

    return max(0.0, 1.0 - 0.35 * diff)


def score_seniority(job_seniority, candidate_seniority) -> float:
    """
    Score seniority alignment.
    """

    if not job_seniority:
        return 1.0

    if not candidate_seniority:
        return 0.5

    jr = SENIORITY_ORDER.get(_normalize_text(job_seniority))
    cr = SENIORITY_ORDER.get(_normalize_text(candidate_seniority))

    if jr is None or cr is None:
        return 0.5

    # Candidate meets/exceeds required seniority.
    if cr >= jr:
        return 1.0

    # Penalize lower seniority.
    diff = jr - cr

    return max(0.0, 1.0 - 0.4 * diff)


def score_domain_alignment(
    job_domains: List[str],
    candidate_domains: List[str],
) -> float:
    """
    Score industry/domain overlap.
    """

    job_domain_set = _to_set(job_domains)
    candidate_domain_set = _to_set(candidate_domains)

    # Job has no declared domains → neutral uncertainty, not perfection.
    if not job_domain_set:
        return 0.5

    if not candidate_domain_set:
        return 0.5

    return len(job_domain_set & candidate_domain_set) / len(job_domain_set)


# ─────────────────────────────────────────────────────────────
# Professional domain detection for title-level relevance
# ─────────────────────────────────────────────────────────────

# Map of broad professional domain → title/keyword signals
_PROFESSIONAL_DOMAINS = {
    "tech":        ["engineer", "developer", "programmer", "architect", "devops",
                    "sre", "backend", "frontend", "fullstack", "software", "cloud",
                    "platform", "infrastructure", "cybersecurity", "security"],
    "data":        ["data scientist", "data analyst", "data engineer", "data science",
                    "machine learning", "ml engineer", "ai engineer", "analytics",
                    "business intelligence", "bi developer", "statistician",
                    "quantitative", "nlp", "computer vision"],
    "education":   ["teacher", "educator", "instructor", "professor", "tutor",
                    "coach", "trainer", "principal", "curriculum", "teaching",
                    "childcare", "daycare", "preschool", "school", "lecturer"],
    "healthcare":  ["nurse", "doctor", "physician", "therapist", "pharmacist",
                    "dentist", "surgeon", "medical", "clinical", "caregiver",
                    "paramedic", "radiologist", "psychologist"],
    "finance":     ["accountant", "auditor", "banker", "trader", "financial analyst",
                    "actuary", "economist", "bookkeeper", "controller", "treasurer"],
    "marketing":   ["marketer", "seo", "content writer", "copywriter", "brand",
                    "advertising", "social media", "growth hacker", "email marketing"],
    "sales":       ["sales", "account executive", "account manager",
                    "business development", "customer success", "sales engineer"],
    "hr":          ["recruiter", "hr manager", "human resources", "talent acquisition",
                    "people operations", "hrbp"],
    "legal":       ["lawyer", "attorney", "paralegal", "legal counsel",
                    "compliance", "solicitor", "barrister"],
    "operations":  ["operations manager", "supply chain", "logistics", "warehouse",
                    "procurement", "project manager", "program manager"],
    "design":      ["designer", "ux designer", "ui designer", "graphic designer",
                    "product designer", "creative director", "art director"],
    "research":    ["researcher", "biologist", "chemist", "physicist",
                    "lab scientist", "r&d", "clinical researcher"],
    "management":  ["manager", "director", "executive", "ceo", "cto", "cfo",
                    "vp ", "vice president", "head of", "chief"],
}

# Domains that are compatible when combined (e.g. a tech manager is fine for a tech role)
_COMPATIBLE_PAIRS = {
    frozenset(["tech", "management"]),
    frozenset(["data", "management"]),
    frozenset(["tech", "data"]),
    frozenset(["sales", "management"]),
    frozenset(["operations", "management"]),
    frozenset(["finance", "management"]),
    frozenset(["marketing", "management"]),
}


def _detect_professional_domain(title: str) -> str:
    """Return the most likely professional domain for a job/candidate title."""
    title_lower = (title or "").lower()
    for domain, keywords in _PROFESSIONAL_DOMAINS.items():
        if any(kw in title_lower for kw in keywords):
            return domain
    return ""


def score_title_relevance(job_title: str, candidate_title: str) -> float:
    """
    Detect whether the job and candidate are in the same professional domain.

    Returns:
        1.0  — same domain or compatible domains
        0.7  — one or both titles are undetectable
        0.1  — clearly different, incompatible domains (e.g. Teacher vs Data Scientist)
    """
    job_domain = _detect_professional_domain(job_title)
    candidate_domain = _detect_professional_domain(candidate_title)

    # Can't determine domain for one or both → neutral
    if not job_domain or not candidate_domain:
        return 0.7

    # Same domain → perfect
    if job_domain == candidate_domain:
        return 1.0

    # Compatible pair → good
    if frozenset([job_domain, candidate_domain]) in _COMPATIBLE_PAIRS:
        return 0.85

    # Completely different domains → heavy penalty
    return 0.1


def compute_match_score(
    job_features: Dict,
    candidate_features: Dict,
) -> Dict:
    """
    Compute overall weighted candidate-job match score.
    """

    # Support both extracted and manual job fields.
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

    # Compute component scores.
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

    title_relevance_score = score_title_relevance(
        job_features.get("title", ""),
        candidate_features.get("current_title", ""),
    )

    # Relative importance of each component.
    # Title relevance carries 15% — it gates completely wrong-field jobs.
    weights = {
        "required_skill_score":  0.33,
        "preferred_skill_score": 0.10,
        "experience_score":      0.18,
        "education_score":       0.07,
        "seniority_score":       0.10,
        "domain_score":          0.07,
        "title_relevance_score": 0.15,
    }

    # Weighted average score.
    weighted_score = (
        required_skill_score  * weights["required_skill_score"]
        + preferred_skill_score * weights["preferred_skill_score"]
        + experience_score      * weights["experience_score"]
        + education_score       * weights["education_score"]
        + seniority_score       * weights["seniority_score"]
        + domain_score          * weights["domain_score"]
        + title_relevance_score * weights["title_relevance_score"]
    )

    # Convert to percentage.
    final_score = round(weighted_score * 100, 2)

    # Extra penalty if required skill coverage is weak.
    if required_skill_score == 0:
        final_score = min(final_score, 45.0)
    elif required_skill_score < 0.5:
        final_score = min(final_score, 60.0)

    # Hard cap: if title relevance detects a completely different profession,
    # the job should never score high regardless of other components.
    if title_relevance_score <= 0.1:
        final_score = min(final_score, 25.0)

    # Convert numeric score into human-readable label.
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

        # Individual component scores for explainability.
        "component_scores": {
            "required_skill_score":  round(required_skill_score, 4),
            "preferred_skill_score": round(preferred_skill_score, 4),
            "experience_score":      round(experience_score, 4),
            "education_score":       round(education_score, 4),
            "seniority_score":       round(seniority_score, 4),
            "domain_score":          round(domain_score, 4),
            "title_relevance_score": round(title_relevance_score, 4),
        },

        # Store weights for transparency/debugging.
        "weights": weights,
    }