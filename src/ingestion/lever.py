from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LeverClient:
    # Timeout for API calls
    request_timeout_seconds: int = 20

    # User-Agent header for requests
    user_agent: str = "job-match-intelligence/1.0"

    # Lever API base URL
    BASE_URL: str = "https://api.lever.co/v0/postings"

    def _build_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

    def fetch_jobs(self, company_slug: str) -> list[dict[str, Any]]:
        """
        Fetch published jobs from a Lever company postings endpoint.
        """

        # Example:
        # https://api.lever.co/v0/postings/netflix
        url = f"{self.BASE_URL}/{company_slug}"

        # Lever requires mode=json
        params = {"mode": "json"}

        logger.info("Fetching Lever jobs for company='%s'", company_slug)

        response = requests.get(
            url,
            params=params,
            headers=self._build_headers(),
            timeout=self.request_timeout_seconds,
        )

        response.raise_for_status()

        # Lever directly returns list (not wrapped like Greenhouse)
        jobs = response.json()

        logger.info(
            "Lever company='%s' returned %s jobs",
            company_slug,
            len(jobs),
        )

        return jobs

    def normalize_jobs(
        self,
        jobs: list[dict[str, Any]],
        company_slug: str,
        pipeline_version: str,
        ingested_at: str,
    ) -> list[dict[str, Any]]:
        """
        Convert Lever API jobs into unified staging records.
        """

        normalized: list[dict[str, Any]] = []

        for job in jobs:

            # Lever stores structured info inside "categories"
            categories = job.get("categories", {}) or {}

            # Lever provides multiple plain-text fields
            description_plain = job.get("descriptionPlain", "") or ""
            additional_plain = job.get("additionalPlain", "") or ""
            lists_plain = job.get("listsPlain", "") or ""

            # Combine all text into one field
            combined_text = " ".join(
                part.strip()
                for part in [description_plain, additional_plain, lists_plain]
                if part and str(part).strip()
            )

            normalized.append(
                {
                    # Unique identifier (same pattern as Greenhouse)
                    "job_uid": f"lever::{company_slug}::{job.get('id')}",

                    "source": "lever",
                    "source_company": company_slug,

                    "source_job_id": str(job.get("id")) if job.get("id") is not None else "",

                    # Lever job URL
                    "source_url": job.get("hostedUrl", ""),

                    "ingested_at": ingested_at,

                    # Lever uses createdAt instead of updated_at
                    "source_updated_at": job.get("createdAt", ""),

                    "pipeline_version": pipeline_version,

                    # Raw job title
                    "title_raw": job.get("text", ""),

                    # Filled later
                    "title_normalized": "",
                    "job_family": "",
                    "job_function": "",
                    "seniority_level": "",

                    # Lever provides structured fields here
                    "employment_type": categories.get("commitment", "") or "",
                    "workplace_type": categories.get("workplaceType", "") or "",
                    "location_raw": categories.get("location", "") or "",

                    "location_normalized": "",
                    "country": "",
                    "region": "",

                    # Raw HTML version
                    "description_raw": job.get("description", "") or "",

                    # Clean text version (combined fields)
                    "description_clean": combined_text,

                    "language": "",
                    "description_hash": "",
                    "dedupe_key": "",

                    "department": categories.get("department", "") or "",
                    "team": categories.get("team", "") or "",

                    # Empty placeholders for next stages
                    "skills_required": [],
                    "skills_preferred": [],
                    "tools_required": [],
                    "tools_preferred": [],
                    "domains": [],
                    "responsibilities": [],

                    "years_experience_min": None,
                    "years_experience_preferred": None,
                    "education_min": "",
                    "certifications": [],

                    "is_remote": False,
                    "is_hybrid": False,
                    "is_onsite": False,

                    # Store raw categories for traceability
                    "metadata_raw": categories,
                }
            )

        return normalized