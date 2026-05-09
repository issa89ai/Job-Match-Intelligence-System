from __future__ import annotations

import re
from typing import Dict, List, Optional

from src.candidate.profile_schema import CandidateProfile


# Ranking used to compare candidate education with job education requirement.
EDUCATION_ORDER = {
    "high_school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
}


# Ranking used to compare candidate seniority with job seniority requirement.
SENIORITY_ORDER = {
    "intern": 1,
    "entry": 2,
    "mid": 3,
    "senior": 4,
    "manager": 5,
}


def _infer_seniority_from_title(title: str) -> Optional[str]:
    """
    Infer candidate seniority from current job title.
    """

    title = (title or "").lower()

    if "intern" in title:
        return "intern"

    if "junior" in title or "entry" in title:
        return "entry"

    if (
        "manager" in title
        or "director" in title
        or "head" in title
        or "principal" in title
        or "vp" in title
    ):
        return "manager"

    if (
        "senior" in title
        or "sr" in title
        or "lead" in title
        or "staff" in title
    ):
        return "senior"

    return None


def _infer_seniority_from_years(years_experience: Optional[int]) -> Optional[str]:
    """
    Infer candidate seniority from years of experience.
    """

    if years_experience is None:
        return None

    if years_experience >= 10:
        return "manager"

    if years_experience >= 8:
        return "senior"

    if years_experience >= 4:
        return "mid"

    if years_experience >= 0:
        return "entry"

    return None


def _merge_unique(*lists: List[str]) -> List[str]:
    """
    Merge multiple lists, lowercase items, remove duplicates, and preserve order.
    """

    merged = []
    seen = set()

    for lst in lists:
        for item in lst:
            val = str(item).strip().lower()

            if val and val not in seen:
                seen.add(val)
                merged.append(val)

    return merged


def build_candidate_features(candidate: CandidateProfile) -> Dict:
    """
    Build matching-ready features from a CandidateProfile object.
    """

    # Infer seniority from title.
    title_based_seniority = _infer_seniority_from_title(
        candidate.current_title
    )

    # Infer seniority from years of experience.
    years_based_seniority = _infer_seniority_from_years(
        candidate.years_experience
    )

    # Choose final seniority using priority:
    # 1. User-provided seniority
    # 2. Title-based seniority
    # 3. Years-based seniority
    final_seniority = (
        candidate.seniority
        or title_based_seniority
        or years_based_seniority
    )

    # Merge skills and tools together because both can satisfy job requirements.
    normalized_skills = _merge_unique(
        candidate.skills,
        candidate.tools,
    )

    # Normalize list-based fields.
    normalized_domains = _merge_unique(candidate.domains)
    normalized_projects = _merge_unique(candidate.projects)
    normalized_certifications = _merge_unique(candidate.certifications)

    # Convert education level into numeric rank.
    education_rank = (
        EDUCATION_ORDER.get(candidate.education)
        if candidate.education
        else None
    )

    # Convert seniority into numeric rank.
    seniority_rank = (
        SENIORITY_ORDER.get(final_seniority)
        if final_seniority
        else None
    )

    # Combine important candidate text into one searchable blob.
    keyword_blob_parts = [
        candidate.current_title,
        candidate.summary,
        " ".join(normalized_skills),
        " ".join(normalized_domains),
        " ".join(normalized_projects),
        " ".join(normalized_certifications),
    ]

    # Join non-empty text parts.
    keyword_blob = " ".join([p for p in keyword_blob_parts if p]).lower()

    # Normalize whitespace.
    keyword_blob = re.sub(r"\s+", " ", keyword_blob).strip()

    # Return final candidate feature dictionary.
    return {
        "candidate_id": candidate.candidate_id,
        "full_name": candidate.full_name,
        "current_title": candidate.current_title,
        "location": candidate.location,

        "education": candidate.education,
        "education_rank": education_rank,

        "years_experience": candidate.years_experience,

        "seniority": final_seniority,
        "seniority_rank": seniority_rank,

        "skills": normalized_skills,
        "tools": candidate.tools,
        "domains": normalized_domains,
        "certifications": normalized_certifications,
        "projects": normalized_projects,

        "summary": candidate.summary,

        # Useful for future semantic search or keyword matching.
        "keyword_blob": keyword_blob,
    }