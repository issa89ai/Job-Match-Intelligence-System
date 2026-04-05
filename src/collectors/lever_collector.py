import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Dict, Any


class LeverCollector:
    """
    Collect public job postings from Lever Postings API.

    We use:
    GET https://api.lever.co/v0/postings/{company}?mode=json
    """

    BASE_URL = "https://api.lever.co/v0/postings"

    def __init__(self, company_slugs: List[str]):
        self.company_slugs = company_slugs

    @staticmethod
    def html_to_text(html: str) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator=" ", strip=True)

    def fetch_company_jobs(self, company_slug: str) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/{company_slug}"
        params = {"mode": "json"}

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            postings = response.json()
        except Exception as e:
            print(f"[Lever] Failed for {company_slug}: {e}")
            return []

        normalized_jobs = []

        for job in postings:
            description_html = job.get("descriptionPlain", "") or job.get("description", "")
            additional_html = job.get("additionalPlain", "") or job.get("additional", "")
            lists_html = job.get("listsPlain", "") or ""

            combined_text = " ".join([
                str(description_html or ""),
                str(additional_html or ""),
                str(lists_html or "")
            ]).strip()

            categories = job.get("categories", {}) or {}

            normalized_jobs.append({
                "source": "lever",
                "company_slug": company_slug,
                "job_id": job.get("id"),
                "internal_job_id": None,
                "title": job.get("text"),
                "location": categories.get("location"),
                "absolute_url": job.get("hostedUrl"),
                "updated_at": job.get("createdAt"),
                "requisition_id": None,
                "department": categories.get("team"),
                "office": categories.get("location"),
                "content_html": None,
                "content_text": combined_text,
                "metadata": {
                    "commitment": categories.get("commitment"),
                    "team": categories.get("team"),
                    "department": categories.get("department"),
                    "workplaceType": categories.get("workplaceType")
                }
            })

        return normalized_jobs

    def collect_all(self) -> pd.DataFrame:
        all_jobs = []

        for company_slug in self.company_slugs:
            jobs = self.fetch_company_jobs(company_slug)
            print(f"[Lever] {company_slug}: {len(jobs)} jobs")
            all_jobs.extend(jobs)

        df = pd.DataFrame(all_jobs)
        return df