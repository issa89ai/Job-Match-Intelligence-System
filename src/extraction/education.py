from __future__ import annotations

import re
from typing import Optional


# Ranking order for education levels.
# Higher number = higher education level.
EDUCATION_ORDER = {
    "high_school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
}


# Regex patterns used to detect education levels.
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
    """
    Extract minimum education requirement from job text.
    """

    # Return None if text is invalid or empty.
    if not isinstance(text, str) or not text.strip():
        return None

    # Normalize text.
    text = text.lower()

    # Store detected education levels.
    found = []

    # Search all education patterns.
    for level, patterns in EDUCATION_PATTERNS.items():

        for pattern in patterns:

            # If pattern is found in text,
            # add the education level.
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.append(level)

                # Stop checking more patterns for same level.
                break

    # If no education requirement detected.
    if not found:
        return None

    # IMPORTANT:
    # Return the MINIMUM education level found.
    #
    # Example:
    # "Bachelor's or Master's degree"
    #
    # Return:
    # bachelor
    #
    # because it is the minimum acceptable requirement.
    return min(found, key=lambda x: EDUCATION_ORDER[x])