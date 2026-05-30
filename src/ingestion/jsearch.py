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

    # ── Vocabulary: every skill/tool/technology we recognise ────────────
    KNOWN_SKILLS_VOCAB = [
        # Programming languages
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "go", "golang", "rust", "swift", "kotlin", "ruby", "php", "scala",
        "r", "matlab", "bash", "shell", "perl", "dart", "haskell", "julia",
        "groovy", "powershell", "vba", "assembly",
        # ML / AI / Data Science
        "machine learning", "deep learning", "nlp",
        "natural language processing", "computer vision",
        "reinforcement learning", "llm", "large language model",
        "generative ai", "transformers", "bert", "gpt", "llama",
        "langchain", "rag", "retrieval augmented generation",
        "feature engineering", "model deployment", "mlops",
        "time series", "forecasting", "anomaly detection",
        "recommendation systems", "a/b testing", "hypothesis testing",
        "statistical modeling", "bayesian", "regression", "classification",
        "clustering", "dimensionality reduction",
        # ML libraries
        "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras",
        "xgboost", "lightgbm", "catboost", "hugging face", "spacy",
        "nltk", "opencv", "pillow", "fastai",
        # Data manipulation
        "pandas", "numpy", "scipy", "polars", "dask",
        # Visualisation
        "matplotlib", "seaborn", "plotly", "bokeh", "altair", "d3.js",
        # SQL / Databases
        "sql", "postgresql", "mysql", "sqlite", "oracle", "sql server",
        "t-sql", "pl/sql", "nosql", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "couchdb", "neo4j", "influxdb",
        # Cloud / Data Warehouse
        "aws", "amazon web services", "azure", "gcp", "google cloud",
        "bigquery", "snowflake", "redshift", "databricks", "synapse",
        "athena", "s3", "lambda", "ec2", "rds", "sagemaker",
        # Data Engineering / Pipeline
        "dbt", "apache airflow", "airflow", "apache spark", "spark",
        "apache kafka", "kafka", "apache flink", "flink",
        "hadoop", "hive", "presto", "trino", "luigi",
        "data pipeline", "data warehouse", "data lake", "etl", "elt",
        "data modeling", "data engineering",
        # DevOps / MLOps / Cloud-native
        "docker", "kubernetes", "k8s", "terraform", "ansible",
        "jenkins", "github actions", "gitlab ci", "circleci",
        "ci/cd", "helm", "prometheus", "grafana", "datadog",
        "linux", "unix", "git", "github", "gitlab", "bitbucket",
        # Web / API
        "fastapi", "django", "flask", "spring", "spring boot",
        "node.js", "express.js", "react", "vue.js", "angular",
        "graphql", "rest api", "restful", "grpc", "websocket",
        "html", "css", "tailwind",
        # BI / Analytics
        "power bi", "tableau", "looker", "metabase", "superset",
        "excel", "google sheets", "google analytics", "mixpanel",
        "amplitude", "segment",
        # Data Analysis / Statistics
        "statistics", "statistical analysis", "data analysis",
        "data visualization", "reporting", "data storytelling",
        "exploratory data analysis", "eda",
        # Project / Collaboration tools
        "jira", "confluence", "notion", "asana", "trello",
        "agile", "scrum", "kanban",
        # Communication / Soft skills sometimes listed as requirements
        "communication", "problem solving", "critical thinking",
        "collaboration", "stakeholder management", "presentation",
    ]

    # ── Contextual patterns — extract skills from prose ──────────────────
    # These catch "experience with X", "knowledge of X", "proficiency in X"
    _REQUIREMENT_PATTERNS = [
        r"experience (?:with|in|using|of)\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"profici(?:ent|ency) (?:in|with)\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"knowledge of\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"famili(?:ar|arity) with\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"skilled (?:in|with)\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"expertise (?:in|with)\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"working knowledge of\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"hands[\-\s]on (?:experience )?(?:with|in)\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"understanding of\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"strong (?:background|foundation) in\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"ability to (?:use|work with|develop|build|implement)\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"(?:must|should) (?:have|know|be able to use)\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"(?:using|use of|built (?:with|on|using))\s+([\w][\w\s\.\+\#\/\-]{1,45}?)(?=[,;.\n]|$)",
        r"(?:tools?|technologies|stack|languages?|frameworks?)\s*(?:include|such as|like|:)\s*([\w][\w\s\.\+\#\/\-,]{1,120}?)(?=[.\n]|$)",
    ]

    # Words that are NOT skills and commonly appear after pattern matches
    _STOP_WORDS = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "up", "about", "into", "through",
        "our", "their", "your", "its", "this", "that", "these", "those",
        "ability", "experience", "knowledge", "skills", "years", "minimum",
        "least", "strong", "solid", "good", "excellent", "proven", "deep",
        "extensive", "broad", "technical", "professional", "relevant",
        "related", "similar", "equivalent", "bachelor", "master", "degree",
        "team", "teams", "company", "role", "position", "candidates",
        "work", "working", "us", "you", "we", "be", "is", "are", "will",
        "have", "has", "been", "should", "must", "can", "may",
    }

    @classmethod
    def _clean_extracted(cls, raw: str) -> List[str]:
        """Split a comma/slash/bullet separated string into individual skill terms."""
        import re
        parts = re.split(r"[,/|•·\n]+", raw)
        result = []
        for p in parts:
            p = p.strip().lower()
            # Remove leading bullets, dashes, numbers
            p = re.sub(r"^[\-–•*\d\.]+\s*", "", p).strip()
            # Remove trailing qualifiers like "(required)", "(preferred)"
            p = re.sub(r"\s*\((?:required|preferred|plus|nice to have|mandatory)[^)]*\)", "", p, flags=re.I).strip()
            # Remove trailing punctuation artifacts (e.g. "tableau." → "tableau")
            p = re.sub(r"[.,;:!?()\[\]]+$", "", p).strip()
            if (2 <= len(p) <= 50
                    and p not in cls._STOP_WORDS
                    and not p.isdigit()
                    and not all(c in " \t" for c in p)):
                result.append(p)
        return result

    @classmethod
    def _extract_skills_from_text(
        cls,
        job: Dict[str, Any],
        full_description: str = "",
    ) -> List[str]:
        """
        Read the ENTIRE job posting and build a skill list by:

        Pass 1 — structured API fields (job_required_skills, highlights)
        Pass 2 — full description scan against a 150+ term vocabulary
        Pass 3 — regex contextual patterns ("experience with X", "using X", etc.)
        Pass 4 — inline lists after "Technologies:", "Stack:", "Tools:" headers

        This ensures skills are extracted even when a posting describes
        requirements in prose rather than bullet points.
        """
        import re

        found: set = set()

        # ── Collect all text ─────────────────────────────────────────────
        text_parts: List[str] = []

        structured = job.get("job_required_skills") or []
        if isinstance(structured, list):
            text_parts.extend(str(s) for s in structured)

        highlights = job.get("job_highlights", {}) or {}
        for section_name, section_items in highlights.items():
            if isinstance(section_items, list):
                # Double-weight qualification/requirements sections
                if any(kw in section_name.lower()
                       for kw in ("qualif", "require", "skill", "experience", "must")):
                    text_parts.extend(str(i) for i in section_items)
                text_parts.extend(str(i) for i in section_items)

        if full_description:
            text_parts.append(full_description)

        combined      = " ".join(text_parts)
        combined_lower = combined.lower()

        # ── Pass 1: vocabulary scan (multi-word first to avoid sub-matches) ─
        for skill in sorted(cls.KNOWN_SKILLS_VOCAB, key=len, reverse=True):
            if skill in combined_lower:
                found.add(skill)

        # ── Pass 2: contextual requirement patterns ──────────────────────
        for pattern in cls._REQUIREMENT_PATTERNS:
            for match in re.finditer(pattern, combined, re.IGNORECASE | re.MULTILINE):
                raw = match.group(1)
                for term in cls._clean_extracted(raw):
                    # Only keep if it's in our vocab OR looks like a real tech term
                    term_lower = term.lower()
                    if (term_lower in cls.KNOWN_SKILLS_VOCAB
                            or re.search(r"[A-Z]{2,}|[A-Z][a-z]+[A-Z]|[\.\+\#]", term)):
                        found.add(term_lower)

        # ── Pass 3: inline tech lists after section headers ──────────────
        list_header_pattern = (
            r"(?:technologies?|tech stack|tools?|languages?|frameworks?|"
            r"libraries?|platforms?|skills? required|required skills?)\s*[:—]\s*"
            r"([\w][\w\s,\.\/\+\#\-]{5,200}?)(?:\n\n|\Z)"
        )
        for match in re.finditer(list_header_pattern, combined, re.IGNORECASE | re.DOTALL):
            for term in cls._clean_extracted(match.group(1)):
                term_lower = term.lower()
                if term_lower in cls.KNOWN_SKILLS_VOCAB or len(term_lower) >= 3:
                    found.add(term_lower)

        # Remove generic stop-words that slipped through
        found = {s for s in found if s not in cls._STOP_WORDS and len(s) >= 2}

        return sorted(found)

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


    # Broad domain vocabulary for job title classification
    _DOMAIN_KEYWORDS = {
        "machine learning":     ["machine learning", "ml engineer", "ai engineer", "deep learning", "nlp engineer"],
        "data science":         ["data scientist", "data science"],
        "data engineering":     ["data engineer", "data pipeline", "etl"],
        "analytics":            ["data analyst", "business analyst", "analytics engineer", "bi developer",
                                 "business intelligence"],
        "software engineering": ["software engineer", "software developer", "backend engineer",
                                 "frontend engineer", "full stack", "fullstack", "web developer",
                                 "mobile developer", "ios developer", "android developer"],
        "devops":               ["devops", "sre", "site reliability", "platform engineer",
                                 "cloud engineer", "infrastructure engineer"],
        "cybersecurity":        ["security engineer", "cybersecurity", "information security", "soc analyst"],
        "education":            ["teacher", "educator", "instructor", "professor", "tutor",
                                 "curriculum", "childcare", "daycare", "preschool", "school"],
        "healthcare":           ["nurse", "doctor", "physician", "therapist", "pharmacist",
                                 "dentist", "surgeon", "medical", "clinical", "caregiver"],
        "finance":              ["accountant", "auditor", "financial analyst", "banker",
                                 "trader", "actuary", "bookkeeper"],
        "marketing":            ["marketing", "seo specialist", "content writer", "copywriter",
                                 "growth", "brand manager"],
        "sales":                ["sales", "account executive", "business development",
                                 "customer success"],
        "hr":                   ["recruiter", "hr manager", "human resources",
                                 "talent acquisition", "people operations"],
        "product management":   ["product manager", "product owner", "program manager"],
        "design":               ["ux designer", "ui designer", "graphic designer",
                                 "product designer", "visual designer"],
    }

    @classmethod
    def _extract_domains(cls, job_title: str, description: str = "") -> List[str]:
        """
        Extract professional domains from job title (primary) and description.
        Returns a list of matching domain labels from our controlled vocabulary.
        """
        combined = (job_title + " " + description[:500]).lower()
        found = []
        for domain, keywords in sorted(
            cls._DOMAIN_KEYWORDS.items(),
            key=lambda kv: max(len(k) for k in kv[1]),
            reverse=True,
        ):
            if any(kw in combined for kw in keywords):
                found.append(domain)
                if len(found) >= 3:
                    break
        return found

    def normalize_jobs(
        self,
        jobs: List[Dict[str, Any]],
        search_query: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Convert raw JSearch API results into the unified job schema
        that the matching engine already understands.
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

            # Skills: scan structured fields + full description text.
            required_skills = self._extract_skills_from_text(job, description)
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
            city    = self._safe_str(job.get("job_city"))
            state   = self._safe_str(job.get("job_state"))
            country = self._safe_str(job.get("job_country"))
            location_parts = [p for p in [city, state, country] if p]
            location = ", ".join(location_parts) if location_parts else "Not specified"

            normalized.append(
                {
                    # Identifiers
                    "job_id":        job_id,
                    "title":         self._safe_str(job.get("job_title")),
                    "company":       self._safe_str(job.get("employer_name")),
                    "location":      location,
                    "workplace_type": workplace_type,

                    # Skills
                    "required_skills":  required_skills,
                    "preferred_skills": preferred_skills,
                    "other_skills":     [],

                    # Requirements
                    "years_experience_required": self._extract_required_exp(job),
                    "education_required":        self._extract_education(job),
                    "seniority":                 None,

                    # Domains
                    "domains": self._extract_domains(
                        job.get("job_title", ""),
                        description,
                    ),

                    # Extra metadata for display in UI
                    "source_url":         self._safe_str(job.get("job_apply_link")
                                                          or job.get("job_google_link")),
                    "employer_logo":      self._safe_str(job.get("employer_logo")),
                    "description_snippet": description[:500],
                    "date_posted":        self._safe_str(job.get("job_posted_at_datetime_utc")),
                    "search_query":       search_query,
                }
            )

        return normalized
