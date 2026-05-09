from __future__ import annotations

# dataclass:
# Automatically generates constructor, repr, etc.
from dataclasses import dataclass, field, asdict

from typing import Any, Dict, List, Optional


# Allowed education levels used across the platform.
VALID_EDUCATION_LEVELS = {
    "high_school",
    "associate",
    "bachelor",
    "master",
    "phd",
}


# Allowed seniority levels used across the platform.
VALID_SENIORITY_LEVELS = {
    "intern",
    "entry",
    "mid",
    "senior",
    "manager",
}


@dataclass
class CandidateProfile:

    # Unique candidate identifier.
    candidate_id: str

    # Basic profile information.
    full_name: str = ""
    current_title: str = ""
    location: str = ""

    # Education level.
    education: Optional[str] = None

    # Total years of experience.
    years_experience: Optional[int] = None

    # Structured candidate attributes.
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)

    # Candidate seniority level.
    seniority: Optional[str] = None

    # Free-text candidate summary.
    summary: str = ""

    # Original raw payload before parsing/normalization.
    raw_input: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert dataclass object into dictionary.
        """

        return asdict(self)