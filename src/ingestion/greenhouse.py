from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup

from src.utils.logger import get_logger


# Create a logger for this module.
logger = get_logger(__name__)


@dataclass
class GreenhouseClient:
    # Timeout for API requests.
    request_timeout_seconds: int = 20

    # User-Agent sent with the API request.
    user_agent: str = "job-match-intelligence/1.0"

    # Base Greenhouse API endpoint.
    BASE_URL: str = "https://boards-api.greenhouse.io/v1/boards"

    def _build_headers(self) -> dict[str, str]:
        # Headers sent to Greenhouse API.
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

    @staticmethod
    def html_to_text(html: str | None) -> str:
        # Convert Greenhouse HTML job description into plain text.
        if not html:
            return ""

        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator=" ", strip=True)

    def fetch_jobs(self, board_token: str) -> list[dict[str, Any]]:
        """
        Fetch published jobs from a Greenhouse board.
        """

        # Example:
        # https://boards-api.greenhouse.io/v1/boards/stripe/jobs
        url = f"{self.BASE_URL}/{board_token}/jobs"

        # content=true includes the full job description HTML.
        params = {"content": "true"}

        logger.info("Fetching Greenhouse jobs for board='%s'", board_token)

        response = requests.get(
            url,
            params=params,
            headers=self._build_headers(),
            timeout=self.request_timeout_seconds,
        )

        # Raise an exception if the request failed.
        response.raise_for_status()

        # Convert JSON response into Python dictionary.
        payload = response.json()

        # Greenhouse stores jobs under the "jobs" key.
        jobs = payload.get("jobs", [])

        logger.info(
            "Greenhouse board='%s' returned %s jobs",
            board_token,
            len(jobs),
        )

        return jobs

    def normalize_jobs(
        self,
        jobs: list[dict[str, Any]],
        board_token: str,
        pipeline_version: str,
        ingested_at: str,
    ) -> list[dict[str, Any]]:
        """
        Convert Greenhouse API jobs into unified staging records.
        """

        normalized: list[dict[str, Any]] = []

        for job in jobs:
            # Original Greenhouse job description is HTML.
            content_html = job.get("content", "")

            # Convert HTML description to clean plain text.
            content_text = self.html_to_text(content_html)

            # Greenhouse metadata is usually a list of name/value pairs.
            metadata = job.get("metadata", []) or []

            # Flatten metadata into a simple dictionary.
            metadata_flat: dict[str, Any] = {}

            for item in metadata:
                name = item.get("name")
                value = item.get("value")

                if name:
                    metadata_flat[name] = value

            # Departments and offices are lists in Greenhouse.
            departments = job.get("departments") or []
            offices = job.get("offices") or []

            # Convert Greenhouse format into your unified staging schema.
            normalized.append(
                {
                    "job_uid": f"greenhouse::{board_token}::{job.get('id')}",
                    "source": "greenhouse",
                    "source_company": board_token,
                    "source_job_id": str(job.get("id")) if job.get("id") is not None else "",
                    "source_url": job.get("absolute_url", ""),
                    "ingested_at": ingested_at,
                    "source_updated_at": job.get("updated_at", ""),
                    "pipeline_version": pipeline_version,

                    # Raw title from Greenhouse.
                    "title_raw": job.get("title", ""),

                    # These are left empty here.
                    # They will be filled later during normalization.
                    "title_normalized": "",
                    "job_family": "",
                    "job_function": "",
                    "seniority_level": "",

                    "employment_type": "",
                    "workplace_type": "",

                    # Raw location from Greenhouse.
                    "location_raw": (job.get("location") or {}).get("name", ""),

                    # These are filled later by location normalization.
                    "location_normalized": "",
                    "country": "",
                    "region": "",

                    # Store both original HTML and cleaned text.
                    "description_raw": content_html,
                    "description_clean": content_text,

                    "language": "",
                    "description_hash": "",
                    "dedupe_key": "",

                    # First department name if available.
                    "department": departments[0].get("name", "") if departments else "",

                    "team": "",

                    # Empty placeholders for later extraction.
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

                    # Location/workplace flags filled later.
                    "is_remote": False,
                    "is_hybrid": False,
                    "is_onsite": False,

                    # Preserve flattened metadata for traceability.
                    "metadata_raw": metadata_flat,
                }
            )

        return normalized