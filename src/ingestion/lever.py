from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LeverClient:
    request_timeout_seconds: int = 20
    user_agent: str = "job-match-intelligence/1.0"

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
        url = f"{self.BASE_URL}/{company_slug}"
        params = {"mode": "json"}

        logger.info("Fetching Lever jobs for company='%s'", company_slug)

        response = requests.get(
            url,
            params=params,
            headers=self._build_headers(),
            timeout=self.request_timeout_seconds,
        )
        response.raise_for_status()

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
            categories = job.get("categories", {}) or {}

            description_plain = job.get("descriptionPlain", "") or ""
            additional_plain = job.get("additionalPlain", "") or ""
            lists_plain = job.get("listsPlain", "") or ""

            combined_text = " ".join(
                part.strip()
                for part in [description_plain, additional_plain, lists_plain]
                if part and str(part).strip()
            )

            normalized.append(
                {
                    "job_uid": f"lever::{company_slug}::{job.get('id')}",
                    "source": "lever",
                    "source_company": company_slug,
                    "source_job_id": str(job.get("id")) if job.get("id") is not None else "",
                    "source_url": job.get("hostedUrl", ""),
                    "ingested_at": ingested_at,
                    "source_updated_at": job.get("createdAt", ""),
                    "pipeline_version": pipeline_version,
                    "title_raw": job.get("text", ""),
                    "title_normalized": "",
                    "job_family": "",
                    "job_function": "",
                    "seniority_level": "",
                    "employment_type": categories.get("commitment", "") or "",
                    "workplace_type": categories.get("workplaceType", "") or "",
                    "location_raw": categories.get("location", "") or "",
                    "location_normalized": "",
                    "country": "",
                    "region": "",
                    "description_raw": job.get("description", "") or "",
                    "description_clean": combined_text,
                    "language": "",
                    "description_hash": "",
                    "dedupe_key": "",
                    "department": categories.get("department", "") or "",
                    "team": categories.get("team", "") or "",
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
                    "metadata_raw": categories,
                }
            )

        return normalized