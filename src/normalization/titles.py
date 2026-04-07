from __future__ import annotations

import re
from typing import Any

from src.utils.text import clean_text, normalize_text_basic


SENIORITY_PATTERNS = {
    "intern": [
        r"\bintern\b",
        r"\binternship\b",
    ],
    "junior": [
        r"\bjunior\b",
        r"\bentry level\b",
        r"\bjr\b",
        r"\bjr\.\b",
    ],
    "mid": [
        r"\bmid\b",
        r"\bmid level\b",
    ],
    "senior": [
        r"\bsenior\b",
        r"\bsr\b",
        r"\bsr\.\b",
        r"\bstaff\b",
        r"\blead\b",
        r"\bprincipal\b",
    ],
    "manager": [
        r"\bmanager\b",
        r"\bdirector\b",
        r"\bhead of\b",
        r"\bvp\b",
        r"\bvice president\b",
    ],
}

TITLE_RULES = [
    {
        "normalized_title": "data_scientist",
        "job_family": "data_science",
        "patterns": [
            r"\bdata scientist\b",
        ],
    },
    {
        "normalized_title": "machine_learning_engineer",
        "job_family": "machine_learning",
        "patterns": [
            r"\bmachine learning engineer\b",
            r"\bml engineer\b",
            r"\bai engineer\b",
        ],
    },
    {
        "normalized_title": "data_analyst",
        "job_family": "analytics",
        "patterns": [
            r"\bdata analyst\b",
            r"\bbusiness analyst\b",
            r"\bbi analyst\b",
            r"\bbusiness intelligence analyst\b",
        ],
    },
    {
        "normalized_title": "data_engineer",
        "job_family": "data_engineering",
        "patterns": [
            r"\bdata engineer\b",
            r"\banalytics engineer\b",
        ],
    },
    {
        "normalized_title": "software_engineer",
        "job_family": "software_engineering",
        "patterns": [
            r"\bsoftware engineer\b",
            r"\bbackend engineer\b",
            r"\bfrontend engineer\b",
            r"\bfull stack engineer\b",
            r"\bfullstack engineer\b",
        ],
    },
    {
        "normalized_title": "account_executive",
        "job_family": "sales",
        "patterns": [
            r"\baccount executive\b",
        ],
    },
    {
        "normalized_title": "product_manager",
        "job_family": "product",
        "patterns": [
            r"\bproduct manager\b",
        ],
    },
]


def infer_seniority_level(title_raw: Any) -> str:
    """
    Infer a coarse seniority level from a raw title.
    """
    text = normalize_text_basic(title_raw)

    for seniority, patterns in SENIORITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return seniority

    return ""


def normalize_title(title_raw: Any) -> tuple[str, str]:
    """
    Normalize job title into a canonical form and infer job family.
    Returns (title_normalized, job_family).
    """
    text = normalize_text_basic(title_raw)

    for rule in TITLE_RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return rule["normalized_title"], rule["job_family"]

    # fallback heuristic
    cleaned = clean_text(title_raw).lower().strip()
    fallback = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")
    return fallback, ""


def infer_job_function(title_normalized: str, job_family: str) -> str:
    """
    Infer broader functional area.
    """
    if job_family in {"data_science", "machine_learning", "analytics", "data_engineering"}:
        return "data"
    if job_family in {"software_engineering"}:
        return "engineering"
    if job_family in {"sales"}:
        return "go_to_market"
    if job_family in {"product"}:
        return "product"
    return ""


def normalize_title_record(title_raw: Any) -> dict[str, str]:
    """
    Normalize all title-related fields at once.
    """
    title_normalized, job_family = normalize_title(title_raw)
    seniority_level = infer_seniority_level(title_raw)
    job_function = infer_job_function(title_normalized, job_family)

    return {
        "title_normalized": title_normalized,
        "job_family": job_family,
        "job_function": job_function,
        "seniority_level": seniority_level,
    }