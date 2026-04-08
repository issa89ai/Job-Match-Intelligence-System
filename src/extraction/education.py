from __future__ import annotations

import re
from typing import Optional


EDUCATION_ORDER = {
    "high_school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
}

EDUCATION_PATTERNS = {
    "high_school": [
        r"high school diploma",
        r"secondary school",
    ],
    "associate": [
        r"associate(?:'s)? degree",
    ],
    "bachelor": [
        r"bachelor(?:'s)? degree",
        r"bs degree",
        r"ba degree",
        r"b\.sc",
        r"\bbsc\b",
    ],
    "master": [
        r"master(?:'s)? degree",
        r"ms degree",
        r"m\.sc",
        r"\bmsc\b",
        r"\bmba\b",
    ],
    "phd": [
        r"\bphd\b",
        r"ph\.d",
        r"doctorate",
        r"doctoral degree",
    ],
}


def extract_education_min(text: str) -> Optional[str]:
    if not isinstance(text, str) or not text.strip():
        return None

    text = text.lower()
    found = []

    for level, patterns in EDUCATION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.append(level)
                break

    if not found:
        return None

    return min(found, key=lambda x: EDUCATION_ORDER[x])