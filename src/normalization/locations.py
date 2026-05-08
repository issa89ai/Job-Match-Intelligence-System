from __future__ import annotations

from typing import Any

from src.utils.text import clean_text, normalize_location_text


# Keywords used to infer country names from location text.
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


# Maps countries to larger geographic regions.
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
    """
    Infer country from normalized location text.
    """

    # Convert location to lowercase for matching.
    normalized = location_text.lower()

    # Search for country keywords.
    for keyword, country in COUNTRY_KEYWORDS.items():

        if keyword in normalized:
            return country

    # Return empty string if country not found.
    return ""


def infer_region(country: str) -> str:
    """
    Map country to broader geographic region.
    """

    return REGION_BY_COUNTRY.get(country, "")


def infer_workplace_type(location_raw: Any, description_clean: Any) -> tuple[bool, bool, bool, str]:
    """
    Infer remote / hybrid / onsite flags and workplace type string.
    """

    # Combine location text and description text.
    # Some jobs mention remote/hybrid only inside description.
    combined = f"{clean_text(location_raw)} {clean_text(description_clean)}".lower()

    # Detect remote jobs.
    is_remote = "remote" in combined

    # Detect hybrid jobs.
    is_hybrid = "hybrid" in combined

    # If neither remote nor hybrid, assume onsite.
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

    # Standardize location formatting.
    location_normalized = normalize_location_text(location_raw)

    # Infer country.
    country = infer_country(location_normalized)

    # Infer geographic region.
    region = infer_region(country)

    # Infer workplace type flags.
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