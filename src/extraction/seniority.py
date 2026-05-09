from __future__ import annotations

from typing import Optional


def infer_seniority(
    title: str,
    description: str,
    years_exp: Optional[int] = None,
) -> Optional[str]:
    """
    Infer seniority level from title, description, and years of experience.
    """

    # Normalize text to lowercase.
    title = (title or "").lower()
    description = (description or "").lower()

    # Detect internship roles.
    if "intern" in title or "internship" in description:
        return "intern"

    # Detect junior / entry-level roles.
    if (
        "junior" in title
        or "entry-level" in title
        or "entry level" in title
    ):
        return "entry"

    # Detect management-level roles.
    if (
        "manager" in title
        or "director" in title
        or "head" in title
        or "vp" in title
        or "principal" in title
    ):
        return "manager"

    # Detect senior-level roles.
    if (
        "senior" in title
        or "sr" in title
        or "lead" in title
        or "staff" in title
    ):
        return "senior"

    # Fallback:
    # Infer seniority using years of experience.
    if years_exp is not None:

        # 8+ years → senior
        if years_exp >= 8:
            return "senior"

        # 4–7 years → mid
        if years_exp >= 4:
            return "mid"

        # 0–3 years → entry
        return "entry"

    # If no signals found, return None.
    return None