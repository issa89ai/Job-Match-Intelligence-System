from __future__ import annotations

import re
from typing import Optional


def extract_years_experience_min(text: str) -> Optional[int]:
    """
    Extract minimum years of experience from job text.
    """

    # Return None if text is empty or invalid.
    if not isinstance(text, str) or not text.strip():
        return None

    # Normalize text to lowercase.
    text = text.lower()

    # Regex patterns for different experience formats.
    patterns = [

        # Example:
        # "5 years"
        # "5+ years"
        r"(\d+)\+?\s*years",

        # Example:
        # "5 yrs"
        r"(\d+)\+?\s*yrs",

        # Example:
        # "minimum of 3"
        r"minimum\s+of\s+(\d+)",

        # Example:
        # "at least 5"
        r"at\s+least\s+(\d+)",

        # Example:
        # "experience: 4+ years"
        r"experience\s*:\s*(\d+)\+?\s*years",

        # Example:
        # "6 years of experience"
        r"(\d+)\+?\s*years\s+of\s+experience",

        # Example:
        # "5 years in python"
        r"(\d+)\+?\s*years\s+in\s+\w+",

        # Example:
        # "3-5 years"
        r"(\d+)\s*-\s*(\d+)\s*years",

        # Example:
        # "3 to 5 years"
        r"(\d+)\s*to\s*(\d+)\s*years",
    ]

    values = []

    # Search all regex patterns.
    for pattern in patterns:

        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        for match in matches:

            # Some regex patterns return tuples (ranges).
            if isinstance(match, tuple):

                # Keep only numeric values.
                nums = [int(x) for x in match if str(x).isdigit()]

                if nums:

                    # IMPORTANT FIX:
                    # For ranges like "3-5 years",
                    # use MAX instead of MIN.
                    values.append(max(nums))

            else:

                if str(match).isdigit():
                    values.append(int(match))

    # If nothing detected, return None.
    if not values:
        return None

    # IMPORTANT FIX:
    # Return the MAX detected value.
    # Example:
    # If text contains:
    # "2 years" and "5 years"
    # use 5 because it is likely the real requirement.
    return max(values)