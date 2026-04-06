from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup


from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GreenhouseClient:
    request_timeout_seconds: int = 20
    user_agent: str = "job-match-intelligence/1.0"

    BASE_URL: str = "https://boards-api.greenhouse.io/v1/boards"

    def _build_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

    @staticmethod
    def html_to_text(html: str | None) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator=" ", strip=True)

    def fetch_jobs(self, board_token: str) -> list[dict[str, Any]]:
        """
        Fetch published jobs from a Greenhouse board.
        """
        url = f"{self.BASE_URL}/{board_token}/jobs"
        params = {"content": "true"}

        logger.info("Fetching Greenhouse jobs for board='%s'", board_token)

        response = requests.get(
            url,
            params=params,
            headers=self._build_headers(),
            timeout=self.request_timeout_seconds,
        )
        response.raise_for_status()

        payload = response.json()
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
            content_html = job.get("content", "")
            content_text = self.html_to_text(content_html)

            metadata = job.get("metadata", []) or []
            metadata_flat: dict[str, Any] = {}
            for item in metadata:
                name = item.get("name")
                value = item.get("value")
                if name:
                    metadata_flat[name] = value

            departments = job.get("departments") or []
            offices = job.get("offices") or []

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
                    "title_raw": job.get("title", ""),
                    "title_normalized": "",
                    "job_family": "",
                    "job_function": "",
                    "seniority_level": "",
                    "employment_type": "",
                    "workplace_type": "",
                    "location_raw": (job.get("location") or {}).get("name", ""),
                    "location_normalized": "",
                    "country": "",
                    "region": "",
                    "description_raw": content_html,
                    "description_clean": content_text,
                    "language": "",
                    "description_hash": "",
                    "dedupe_key": "",
                    "department": departments[0].get("name", "") if departments else "",
                    "team": "",
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
                    "metadata_raw": metadata_flat,
                }
            )

        return normalized