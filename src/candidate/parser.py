from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# Import schema and valid vocabularies.
from src.candidate.profile_schema import (
    CandidateProfile,
    VALID_EDUCATION_LEVELS,
    VALID_SENIORITY_LEVELS,
)


def _normalize_text(value: Any) -> str:
    """
    Normalize generic text fields.
    """

    # Handle None safely.
    if value is None:
        return ""

    # Convert to string and trim whitespace.
    value = str(value).strip()

    # Collapse multiple spaces.
    value = re.sub(r"\s+", " ", value)

    return value


def _normalize_list(values: Any) -> List[str]:
    """
    Normalize list-like candidate fields.
    """

    if values is None:
        return []

    # Handle comma-separated string input.
    if isinstance(values, str):

        # Split using common separators.
        parts = re.split(r"[;,|/]+", values)

        # Normalize and lowercase values.
        cleaned = [
            _normalize_text(p).lower()
            for p in parts
            if _normalize_text(p)
        ]

        # Remove duplicates and sort.
        return sorted(set(cleaned))

    # Handle actual Python lists.
    if isinstance(values, list):

        cleaned = [
            _normalize_text(v).lower()
            for v in values
            if _normalize_text(v)
        ]

        return sorted(set(cleaned))

    return []


def _normalize_education(value: Any) -> Optional[str]:
    """
    Normalize education level into canonical vocabulary.
    """

    value = _normalize_text(value).lower()

    if not value:
        return None

    # Map education aliases to canonical values.
    mapping = {
        "high school": "high_school",
        "high_school": "high_school",
        "secondary": "high_school",

        "associate": "associate",
        "associate degree": "associate",

        "bachelor": "bachelor",
        "bachelors": "bachelor",
        "bachelor's": "bachelor",
        "bs": "bachelor",
        "ba": "bachelor",
        "bsc": "bachelor",

        "master": "master",
        "masters": "master",
        "master's": "master",
        "ms": "master",
        "msc": "master",
        "mba": "master",

        "phd": "phd",
        "ph.d": "phd",
        "doctorate": "phd",
    }

    normalized = mapping.get(value, value)

    # Only return valid controlled vocabulary values.
    return normalized if normalized in VALID_EDUCATION_LEVELS else None


def _normalize_seniority(value: Any) -> Optional[str]:
    """
    Normalize seniority level into canonical vocabulary.
    """

    value = _normalize_text(value).lower()

    if not value:
        return None

    # Map title aliases into simplified taxonomy.
    mapping = {
        "intern": "intern",

        "junior": "entry",
        "entry": "entry",
        "entry-level": "entry",
        "entry level": "entry",

        "mid": "mid",
        "mid-level": "mid",
        "mid level": "mid",

        "senior": "senior",
        "lead": "senior",
        "staff": "senior",

        "manager": "manager",
        "director": "manager",
        "principal": "manager",
        "head": "manager",
        "vp": "manager",
    }

    normalized = mapping.get(value, value)

    # Return only valid taxonomy values.
    return normalized if normalized in VALID_SENIORITY_LEVELS else None


def _normalize_years_experience(value: Any) -> Optional[int]:
    """
    Normalize years of experience into integer.
    """

    # Handle missing values.
    if value is None or value == "":
        return None

    # If already integer, ensure non-negative.
    if isinstance(value, int):
        return max(0, value)

    text = _normalize_text(value).lower()

    if not text:
        return None

    # Extract first integer from text.
    match = re.search(r"(\d+)", text)

    if match:
        return int(match.group(1))

    return None


def parse_candidate_profile(raw_profile: Dict[str, Any]) -> CandidateProfile:
    """
    Parse and normalize raw candidate input into CandidateProfile schema.
    """

    candidate = CandidateProfile(

        # Candidate ID with fallback default.
        candidate_id=
        _normalize_text(raw_profile.get("candidate_id", ""))
        or "candidate_001",

        # Basic profile fields.
        full_name=
        _normalize_text(raw_profile.get("full_name", "")),

        current_title=
        _normalize_text(raw_profile.get("current_title", "")),

        location=
        _normalize_text(raw_profile.get("location", "")),

        # Normalize education vocabulary.
        education=
        _normalize_education(raw_profile.get("education")),

        # Normalize experience value.
        years_experience=
        _normalize_years_experience(
            raw_profile.get("years_experience")
        ),

        # Normalize structured list fields.
        skills=
        _normalize_list(raw_profile.get("skills")),

        tools=
        _normalize_list(raw_profile.get("tools")),

        domains=
        _normalize_list(raw_profile.get("domains")),

        certifications=
        _normalize_list(raw_profile.get("certifications")),

        projects=
        _normalize_list(raw_profile.get("projects")),

        # Normalize seniority taxonomy.
        seniority=
        _normalize_seniority(raw_profile.get("seniority")),

        # Normalize summary text.
        summary=
        _normalize_text(raw_profile.get("summary", "")),

        # Preserve original raw payload.
        raw_input=raw_profile,
    )

    return candidate