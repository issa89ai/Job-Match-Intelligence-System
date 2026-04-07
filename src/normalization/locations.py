from __future__ import annotations

from typing import Any

from src.utils.text import clean_text, normalize_location_text


COUNTRY_KEYWORDS = {
    "united states": "united states",
    "usa": "united states",
    "u.s.": "united states",
    "canada": "canada",
    "france": "france",
    "japan": "japan",
    "brazil": "brazil",
    "ireland": "ireland",
    "united kingdom": "united kingdom",
    "uk": "united kingdom",
    "england": "united kingdom",
    "india": "india",
    "singapore": "singapore",
    "germany": "germany",
}

REGION_BY_COUNTRY = {
    "united states": "north_america",
    "canada": "north_america",
    "france": "europe",
    "japan": "asia",
    "brazil": "south_america",
    "ireland": "europe",
    "united kingdom": "europe",
    "india": "asia",
    "singapore": "asia",
    "germany": "europe",
}


def infer_country(location_text: str) -> str:
    normalized = location_text.lower()
    for keyword, country in COUNTRY_KEYWORDS.items():
        if keyword in normalized:
            return country
    return ""


def infer_region(country: str) -> str:
    return REGION_BY_COUNTRY.get(country, "")


def infer_workplace_type(location_raw: Any, description_clean: Any) -> tuple[bool, bool, bool, str]:
    """
    Infer remote / hybrid / onsite flags and workplace type string.
    """
    combined = f"{clean_text(location_raw)} {clean_text(description_clean)}".lower()

    is_remote = "remote" in combined
    is_hybrid = "hybrid" in combined
    is_onsite = not is_remote and not is_hybrid

    workplace_type = ""
    if is_remote:
        workplace_type = "remote"
    elif is_hybrid:
        workplace_type = "hybrid"
    elif clean_text(location_raw):
        workplace_type = "onsite"

    return is_remote, is_hybrid, is_onsite, workplace_type


def normalize_location_record(location_raw: Any, description_clean: Any) -> dict[str, str | bool]:
    """
    Normalize all location-related fields at once.
    """
    location_normalized = normalize_location_text(location_raw)
    country = infer_country(location_normalized)
    region = infer_region(country)
    is_remote, is_hybrid, is_onsite, workplace_type = infer_workplace_type(
        location_raw=location_raw,
        description_clean=description_clean,
    )

    return {
        "location_normalized": location_normalized,
        "country": country,
        "region": region,
        "is_remote": is_remote,
        "is_hybrid": is_hybrid,
        "is_onsite": is_onsite,
        "workplace_type": workplace_type,
    }