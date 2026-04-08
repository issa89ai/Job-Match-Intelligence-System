from __future__ import annotations

from typing import Optional


def infer_seniority(title: str, description: str, years_exp: Optional[int] = None) -> Optional[str]:
    title = (title or "").lower()
    description = (description or "").lower()

    if "intern" in title or "internship" in description:
        return "intern"

    if "junior" in title or "entry-level" in title or "entry level" in title:
        return "entry"

    if "manager" in title or "director" in title or "head" in title or "vp" in title or "principal" in title:
        return "manager"

    if "senior" in title or "sr" in title or "lead" in title or "staff" in title:
        return "senior"

    if years_exp is not None:
        if years_exp >= 8:
            return "senior"
        if years_exp >= 4:
            return "mid"
        return "entry"

    return None