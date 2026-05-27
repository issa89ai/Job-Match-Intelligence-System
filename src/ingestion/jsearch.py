from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from src.utils.logger import get_logger

logger = get_logger(__name__)


class JSearchClient:
    """
    Client for the JSearch API (via RapidAPI).

    JSearch aggregates real-time job postings from LinkedIn, Indeed,
    Glassdoor, ZipRecruiter, and many other major job boards.

    Each search query returns live job listings exactly as they appear
    on the original websites.
    """

    def __init__(
        self,
        api_key: str,
        host: str = "jsearch.p.rapidapi.com",
        base_url: str = "https://jsearch.p.rapidapi.com",
        request_timeout_seconds: int = 15,
        max_results_per_query: int = 10,
    ) -> None:
        self.api_key = api_key
        self.host = host
        self.base_url = base_url.rstrip("/")
        self.request_timeout_seconds = request_timeout_seconds
        self.max_results_per_query = max_results_per_query

    def _build_headers(self) -> Dict[str, str]:
        return {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host,
        }

    def search_jobs(
        self,
        query: str,
        location: str = "",
        num_pages: int = 1,
        employment_types: Optional[str] = None,
        date_posted: str = "all",
    ) -> List[Dict[str, Any]]:
        """
        Search for live jobs using a query string.

        Args:
            query:            Job title or keywords, e.g. "data scientist"
            location:         City/country filter, e.g. "New York" or "remote"
            num_pages:        Number of result pages (1 page ≈ 10 results)
            employment_types: e.g. "FULLTIME,PARTTIME" — None means all
            date_posted:      "all", "today", "3days", "week", "month"

        Returns:
            List of raw JSearch job dictionaries.
        """

        # Build the combined search query.
        full_query = query.strip()
        if location.strip():
            full_query = f"{full_query} in {location.strip()}"

        params: Dict[str, Any] = {
            "query": full_query,
            "page": "1",
            "num_pages": str(num_pages),
            "date_posted": date_posted,
        }

        if employment_types:
            params["employment_types"] = employment_types

        url = f"{self.base_url}/search"

        logger.info("JSearch query='%s'", full_query)

        try:
            response = requests.get(
                url,
                headers=self._build_headers(),
                params=params,
                timeout=self.request_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.Timeout:
            logger.error("JSearch request timed out for query='%s'", full_query)
            return []

        except requests.exceptions.HTTPError as exc:
            logger.error(
                "JSearch HTTP error %s for query='%s'",
                exc.response.status_code if exc.response else "unknown",
                full_query,
            )
            return []

        except Exception as exc:
            logger.error("JSearch unexpected error: %s", str(exc))
            return []

        jobs = data.get("data", [])
        logger.info("JSearch returned %s jobs for query='%s'", len(jobs), full_query)

        # Respect per-query limit.
        return jobs[: self.max_results_per_query]

    @staticmethod
    def _safe_str(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _extract_skills_from_highlights(job: Dict[str, Any]) -> List[str]:
        """
        Pull skill-like keywords out of JSearch highlight/qualification fields.
        These are the closest thing JSearch provides to explicit skill lists.
        """
        import re

        KNOWN_SKILLS = {
            "python", "sql", "java", "javascript", "typescript", "react",
            "node.js", "nodejs", "machine learning", "deep learning", "nlp",
            "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
            "docker", "kubernetes", "aws", "azure", "gcp", "google cloud",
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "fastapi", "django", "flask", "spring", "spark", "kafka",
            "power bi", "tableau", "excel", "r", "scala", "git", "linux",
            "bash", "c++", "go", "rust", "swift", "statistics",
            "data visualization", "data analysis", "data engineering",
            "machine learning engineering", "llm", "generative ai",
        }

        # Gather all text from highlight fields.
        text_parts = []

        highlights = job.get("job_highlights", {}) or {}
        for section_items in highlights.values():
            if isinstance(section_items, list):
                text_parts.extend(section_items)

        qualifications = job.get("job_required_skills") or []
        if isinstance(qualifications, list):
            text_parts.extend(qualifications)

        combined = " ".join(str(p) for p in text_parts).lower()

        found = [skill for skill in KNOWN_SKILLS if skill in combined]
        return sorted(set(found))

    @staticmethod
    def _extract_required_exp(job: Dict[str, Any]) -> Optional[int]:
        """Extract years of experience from JSearch experience fields."""
        exp = job.get("job_required_experience") or {}
        if isinstance(exp, dict):
            months = exp.get("required_experience_in_months")
            if months:
                try:
                    return max(0, int(int(months) / 12))
                except (ValueError, TypeError):
                    pass
        return None

    @staticmethod
    def _extract_education(job: Dict[str, Any]) -> Optional[str]:
        """Map JSearch education level to our controlled vocabulary."""
        edu = job.get("job_required_education") or {}
        if not isinstance(edu, dict):
            return None

        level = (edu.get("required_education_level") or "").lower()

        mapping = {
            "bachelors degree": "bachelor",
            "bachelor": "bachelor",
            "masters degree": "master",
            "master": "master",
            "postdoctoral": "phd",
            "doctorate": "phd",
            "phd": "phd",
            "associate": "associate",
            "high school": "high_school",
        }

        for key, value in mapping.items():
            if key in level:
                return value

        return None

    def normalize_jobs(
        self,
        jobs: List[Dict[str, Any]],
        search_query: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Convert raw JSearch API results into the unified job schema
        that the matching engine already understands.

        This is the same shape used by _load_jobs_from_csv() in main.py,
        so the entire matching pipeline works without any further changes.
        """
        normalized: List[Dict[str, Any]] = []

        for job in jobs:
            job_id = self._safe_str(job.get("job_id"))
            if not job_id:
                continue

            # Build a combined description for skill extraction.
            description_parts = [
                self._safe_str(job.get("job_description")),
            ]
            highlights = job.get("job_highlights", {}) or {}
            for items in highlights.values():
                if isinstance(items, list):
                    description_parts.extend(str(i) for i in items)

            description = " ".join(p for p in description_parts if p)

            # Skills: use dedicated field first, then extract from text.
            required_skills = self._extract_skills_from_highlights(job)
            preferred_skills: List[str] = []

            # Employment / workplace type.
            emp_type = self._safe_str(job.get("job_employment_type")).lower()
            is_remote = bool(job.get("job_is_remote"))
            if is_remote:
                workplace_type = "remote"
            elif "hybrid" in description.lower():
                workplace_type = "hybrid"
            else:
                workplace_type = "onsite" if emp_type else ""

            # Location string.
            city = self._safe_str(job.get("job_city"))
            state = self._safe_str(job.get("job_state"))
            country = self._safe_str(job.get("job_country"))
            location_parts = [p for p in [city, state, country] if p]
            location = ", ".join(location_parts) if location_parts else "Not specified"

            normalized.append(
                {
                    # Identifiers
                    "job_id": job_id,
                    "title": self._safe_str(job.get("job_title")),
                    "company": self._safe_str(job.get("employer_name")),
                    "location": location,
                    "workplace_type": workplace_type,

                    # Skills
                    "required_skills": required_skills,
                    "preferred_skills": preferred_skills,
                    "other_skills": [],

                    # Requirements
                    "years_experience_required": self._extract_required_exp(job),
                    "education_required": self._extract_education(job),
                    "seniority": None,  # inferred by matching engine

                    # Domains (empty — matching engine handles missing gracefully)
                    "domains": [],

                    # Extra metadata for display in UI
                    "source_url": self._safe_str(job.get("job_apply_link")
                                                  or job.get("job_google_link")),
                    "employer_logo": self._safe_str(job.get("employer_logo")),
                    "description_snippet": description[:500],
                    "date_posted": self._safe_str(job.get("job_posted_at_datetime_utc")),
                    "search_query": search_query,
                }
            )

        return normalized
