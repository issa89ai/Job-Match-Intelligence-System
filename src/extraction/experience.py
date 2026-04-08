from __future__ import annotations

import re
from typing import Optional


def extract_years_experience_min(text: str) -> Optional[int]:
    if not isinstance(text, str) or not text.strip():
        return None

    text = text.lower()

    patterns = [
        r"(\d+)\+?\s*years",
        r"(\d+)\+?\s*yrs",
        r"minimum\s+of\s+(\d+)",
        r"at\s+least\s+(\d+)",
        r"experience\s*:\s*(\d+)\+?\s*years",
        r"(\d+)\+?\s*years\s+of\s+experience",
        r"(\d+)\+?\s*years\s+in\s+\w+",
        r"(\d+)\s*-\s*(\d+)\s*years",
        r"(\d+)\s*to\s*(\d+)\s*years",
    ]

    values = []

    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                nums = [int(x) for x in match if str(x).isdigit()]
                if nums:
                    values.append(max(nums))  # 🔥 FIX: use MAX for ranges
            else:
                if str(match).isdigit():
                    values.append(int(match))

    if not values:
        return None

    # 🔥 FIX: use MAX instead of MIN
    return max(values)