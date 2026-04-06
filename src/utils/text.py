from __future__ import annotations

import hashlib
import json
import re
from typing import Iterable

import pandas as pd


WHITESPACE_PATTERN = re.compile(r"\s+")
NON_WORD_KEEP_PLUS_HASH_DOT_PATTERN = re.compile(r"[^\w\s+#.]")
YEAR_EXPERIENCE_PATTERN = re.compile(
    r"(?P<years>\d+)\+?\s*(?:years|year|yrs|yr)\s+(?:of\s+)?experience",
    re.IGNORECASE,
)


def is_missing(value: object) -> bool:
    """
    Check if a value should be treated as missing.
    """
    if value is None:
        return True
    try:
        return pd.isna(value)
    except Exception:
        return False


def clean_text(text: object) -> str:
    """
    Standard text cleaning used across the platform.
    """
    if is_missing(text):
        return ""

    text = str(text)
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = WHITESPACE_PATTERN.sub(" ", text)
    return text.strip()


def normalize_text_basic(text: object) -> str:
    """
    Lowercase and remove most punctuation while preserving +, #, and .
    Useful for NLP matching.
    """
    text = clean_text(text).lower()
    text = NON_WORD_KEEP_PLUS_HASH_DOT_PATTERN.sub(" ", text)
    text = WHITESPACE_PATTERN.sub(" ", text)
    return text.strip()


def normalize_location_text(location: object) -> str:
    """
    Simple location normalization placeholder.
    """
    if is_missing(location):
        return ""

    location_text = clean_text(location)

    replacements = {
        "remote - united states": "remote, united states",
        "remote - canada": "remote, canada",
        "new york ny": "new york, ny",
        "san francisco ca": "san francisco, ca",
    }

    key = location_text.lower().replace(".", "")
    return replacements.get(key, location_text)


def stable_hash(text: object) -> str:
    """
    Compute a stable SHA256 hash for text.
    """
    normalized = clean_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def safe_json_string(value: object) -> str:
    """
    Convert a value to a JSON string safely.
    """
    if is_missing(value):
        return "{}"

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    return str(value)


def unique_preserve_order(items: Iterable[str]) -> list[str]:
    """
    Deduplicate while preserving order.
    """
    seen: set[str] = set()
    output: list[str] = []

    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)

    return output


def extract_min_years_experience(text: object) -> int | None:
    """
    Extract a simple minimum years-of-experience signal from text.
    Returns the first detected integer if found.
    """
    normalized = clean_text(text)
    match = YEAR_EXPERIENCE_PATTERN.search(normalized)
    if not match:
        return None

    return int(match.group("years"))