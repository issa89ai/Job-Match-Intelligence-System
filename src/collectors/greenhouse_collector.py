import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Dict, Any


class GreenhouseCollector:
    """
    Collect public job postings from Greenhouse Job Board API.

    Notes:
    - Greenhouse Job Board API supports public GET endpoints.
    - We use:
      GET /v1/boards/{board_token}/jobs?content=true
    """

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, board_tokens: List[str]):
        self.board_tokens = board_tokens

    @staticmethod
    def html_to_text(html: str) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator=" ", strip=True)

    def fetch_board_jobs(self, board_token: str) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/{board_token}/jobs"
        params = {"content": "true"}

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except Exception as e:
            print(f"[Greenhouse] Failed for {board_token}: {e}")
            return []

        jobs = payload.get("jobs", [])
        normalized_jobs = []

        for job in jobs:
            content = job.get("content", "")
            text_content = self.html_to_text(content)

            metadata = job.get("metadata", []) or []
            metadata_flat = {}

            for item in metadata:
                name = item.get("name")
                value = item.get("value")
                if name:
                    metadata_flat[name] = value

            normalized_jobs.append({
                "source": "greenhouse",
                "company_slug": board_token,
                "job_id": job.get("id"),
                "internal_job_id": job.get("internal_job_id"),
                "title": job.get("title"),
                "location": (job.get("location") or {}).get("name"),
                "absolute_url": job.get("absolute_url"),
                "updated_at": job.get("updated_at"),
                "requisition_id": job.get("requisition_id"),
                "department": job.get("departments", [{}])[0].get("name") if job.get("departments") else None,
                "office": job.get("offices", [{}])[0].get("name") if job.get("offices") else None,
                "content_html": content,
                "content_text": text_content,
                "metadata": metadata_flat
            })

        return normalized_jobs

    def collect_all(self) -> pd.DataFrame:
        all_jobs = []

        for board_token in self.board_tokens:
            jobs = self.fetch_board_jobs(board_token)
            print(f"[Greenhouse] {board_token}: {len(jobs)} jobs")
            all_jobs.extend(jobs)

        df = pd.DataFrame(all_jobs)
        return df