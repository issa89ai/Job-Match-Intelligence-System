from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


VALID_EDUCATION_LEVELS = {
    "high_school",
    "associate",
    "bachelor",
    "master",
    "phd",
}

VALID_SENIORITY_LEVELS = {
    "intern",
    "entry",
    "mid",
    "senior",
    "manager",
}


@dataclass
class CandidateProfile:
    candidate_id: str
    full_name: str = ""
    current_title: str = ""
    location: str = ""
    education: Optional[str] = None
    years_experience: Optional[int] = None

    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)

    seniority: Optional[str] = None
    summary: str = ""

    raw_input: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)