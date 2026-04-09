from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from src.candidate.profile_schema import (
    CandidateProfile,
    VALID_EDUCATION_LEVELS,
    VALID_SENIORITY_LEVELS,
)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def _normalize_list(values: Any) -> List[str]:
    if values is None:
        return []

    if isinstance(values, str):
        parts = re.split(r"[;,|/]+", values)
        cleaned = [_normalize_text(p).lower() for p in parts if _normalize_text(p)]
        return sorted(set(cleaned))

    if isinstance(values, list):
        cleaned = [_normalize_text(v).lower() for v in values if _normalize_text(v)]
        return sorted(set(cleaned))

    return []


def _normalize_education(value: Any) -> Optional[str]:
    value = _normalize_text(value).lower()
    if not value:
        return None

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
    return normalized if normalized in VALID_EDUCATION_LEVELS else None


def _normalize_seniority(value: Any) -> Optional[str]:
    value = _normalize_text(value).lower()
    if not value:
        return None

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
    return normalized if normalized in VALID_SENIORITY_LEVELS else None


def _normalize_years_experience(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None

    if isinstance(value, int):
        return max(0, value)

    text = _normalize_text(value).lower()
    if not text:
        return None

    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))

    return None


def parse_candidate_profile(raw_profile: Dict[str, Any]) -> CandidateProfile:
    candidate = CandidateProfile(
        candidate_id=_normalize_text(raw_profile.get("candidate_id", "")) or "candidate_001",
        full_name=_normalize_text(raw_profile.get("full_name", "")),
        current_title=_normalize_text(raw_profile.get("current_title", "")),
        location=_normalize_text(raw_profile.get("location", "")),
        education=_normalize_education(raw_profile.get("education")),
        years_experience=_normalize_years_experience(raw_profile.get("years_experience")),
        skills=_normalize_list(raw_profile.get("skills")),
        tools=_normalize_list(raw_profile.get("tools")),
        domains=_normalize_list(raw_profile.get("domains")),
        certifications=_normalize_list(raw_profile.get("certifications")),
        projects=_normalize_list(raw_profile.get("projects")),
        seniority=_normalize_seniority(raw_profile.get("seniority")),
        summary=_normalize_text(raw_profile.get("summary", "")),
        raw_input=raw_profile,
    )

    return candidate