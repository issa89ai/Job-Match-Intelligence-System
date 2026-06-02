from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from src.utils.logger import get_logger
from src.ingestion.job_templates import find_template

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

        # ── Finance / Accounting ──────────────────────────────────────────
        "gaap", "ifrs", "sox", "sarbanes-oxley",
        "cpa", "cfa", "cma", "acca", "ca",
        "financial reporting", "financial modeling", "financial analysis",
        "financial statements", "financial planning",
        "budgeting", "budget management", "variance analysis",
        "forecasting", "cash flow", "cash flow management",
        "accounts payable", "accounts receivable", "general ledger",
        "month-end close", "year-end close", "reconciliation",
        "bank reconciliation", "journal entries", "accruals",
        "audit", "internal audit", "external audit", "audit preparation",
        "tax", "tax compliance", "tax filing", "corporate tax", "tax planning",
        "payroll", "payroll processing",
        "quickbooks", "sap", "oracle financials", "sage", "netsuite",
        "xero", "workday financials", "dynamics 365",
        "erp", "enterprise resource planning",
        "consolidations", "intercompany", "transfer pricing",
        "risk management", "financial risk", "credit risk",
        "valuation", "dcf", "discounted cash flow",
        "investment analysis", "portfolio management",
        "cost accounting", "management accounting", "fund accounting",
        "bookkeeping", "double entry", "chart of accounts",
        "accounts management", "billing", "invoicing",
        "bloomberg", "refinitiv",

        # ── Human Resources ───────────────────────────────────────────────
        "recruitment", "talent acquisition", "talent management",
        "onboarding", "offboarding", "hris",
        "workday", "bamboohr", "adp", "successfactors",
        "performance management", "performance review",
        "employee relations", "labour relations", "employment law",
        "compensation", "benefits administration", "total rewards",
        "succession planning", "learning and development",
        "diversity equity inclusion", "dei",
        "organizational development", "change management",

        # ── Marketing / Sales ─────────────────────────────────────────────
        "seo", "sem", "ppc", "google ads", "facebook ads",
        "social media marketing", "content marketing", "email marketing",
        "marketing automation", "hubspot", "marketo", "salesforce",
        "crm", "lead generation", "demand generation",
        "brand management", "digital marketing", "growth marketing",
        "affiliate marketing", "influencer marketing",
        "copywriting", "content creation", "content strategy",
        "market research", "competitive analysis",
        "b2b", "b2c", "account management", "customer success",

        # ── Legal / Compliance ────────────────────────────────────────────
        "contract management", "contract review", "contract drafting",
        "legal research", "litigation", "due diligence",
        "compliance", "regulatory compliance", "gdpr", "hipaa",
        "intellectual property", "patent", "trademark",
        "corporate law", "employment law", "mergers and acquisitions",
        "legal writing", "case management",

        # ── Healthcare / Clinical ─────────────────────────────────────────
        "patient care", "clinical assessment", "clinical research",
        "ehr", "emr", "epic", "meditech", "cerner",
        "hipaa", "icd-10", "cpt coding", "medical coding",
        "nursing", "pharmacology", "medication administration",
        "diagnosis", "treatment planning", "patient education",
        "clinical trials", "good clinical practice", "gcp",
        "phlebotomy", "vital signs", "medical terminology",

        # ── Operations / Supply Chain ─────────────────────────────────────
        "supply chain management", "logistics", "procurement",
        "inventory management", "warehouse management",
        "lean manufacturing", "six sigma", "kaizen",
        "process improvement", "operations management",
        "vendor management", "contract negotiation",
        "demand planning", "capacity planning",
        "sap mm", "sap sd", "sap wm",

        # ── Education / Training ──────────────────────────────────────────
        "curriculum development", "lesson planning", "instructional design",
        "e-learning", "lms", "learning management system",
        "classroom management", "student assessment", "differentiated instruction",
        "special education", "iep", "early childhood education",
        "adult learning", "training delivery", "facilitation",
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

    # Skills that require word-boundary matching because they are short or look
    # like common English words / substrings.  Without boundaries:
    #   "go"    → false-match inside "ongoing", "going", "undergo"
    #   "r"     → false-match everywhere
    #   "c"     → false-match everywhere
    #   "rag"   → false-match inside "fragile", "managing"  (no – but "rag" IS
    #              a substring of e.g. "rage", "brag", "rag-" tokens)
    #   "rds"   → false-match inside "records", "rewards", "procedures"
    #   "scala" → fine length-wise but "scale" ≠ "scala"; still safe to boundary
    _WORD_BOUNDARY_SKILLS = {
        # Very short programming language names
        "go", "r", "c", "c#", "c++",
        # Abbreviations & 3-char tokens that appear as substrings
        "rag", "rds", "ec2", "s3", "k8s", "vba",
        # Common short words used as skill names
        "sql", "git", "seo", "sem", "ppc", "erp", "crm", "ehr", "emr",
        "lms", "iep", "dei", "gcp", "aws", "rds",
    }

    # Pure-tech skills that must NOT appear on non-tech jobs (accounting,
    # HR, marketing, legal, healthcare, education, etc.).  We suppress these
    # when the inferred job domain is clearly non-tech.
    _TECH_ONLY_SKILLS = {
        # Languages
        "go", "golang", "rust", "scala", "kotlin", "swift", "perl",
        "haskell", "julia", "groovy", "dart", "assembly",
        # ML/AI
        "rag", "retrieval augmented generation", "langchain", "llm",
        "large language model", "generative ai", "transformers", "bert",
        "gpt", "llama", "hugging face", "spacy", "nltk", "opencv",
        "fastai", "mlops", "model deployment", "feature engineering",
        # Cloud infra
        "rds", "ec2", "s3", "sagemaker", "lambda", "athena",
        "kubernetes", "k8s", "helm", "terraform", "ansible",
        "prometheus", "grafana", "datadog",
        # Data engineering / streaming
        "apache kafka", "kafka", "apache flink", "flink",
        "hadoop", "hive", "presto", "trino", "luigi", "dbt",
        "apache airflow", "airflow", "apache spark",
        # DevOps
        "jenkins", "github actions", "gitlab ci", "circleci",
        "docker", "ci/cd",
    }

    # Job title keywords that signal the posting is NOT a tech role.
    # When matched, _TECH_ONLY_SKILLS will be excluded from results.
    _NON_TECH_TITLE_SIGNALS = {
        "accountant", "bookkeeper", "controller", "accounts payable",
        "accounts receivable", "payroll", "auditor", "tax",
        "nurse", "nursing", "physician", "doctor", "therapist",
        "pharmacist", "dentist", "radiologist", "clinician",
        "teacher", "educator", "instructor", "lecturer", "professor",
        "recruiter", "hr manager", "human resources", "talent acquisition",
        "marketing", "copywriter", "content writer", "seo specialist",
        "social media",
        "lawyer", "attorney", "paralegal", "solicitor",
        "operations manager", "supply chain", "logistics", "procurement",
        "hotel", "restaurant", "chef", "retail", "real estate",
        "financial analyst", "finance manager", "banker", "trader",
        "investment analyst", "credit analyst",
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

        # Detect whether this is a non-tech job based on the job title field.
        job_title_lower = cls._safe_str(job.get("job_title", "")).lower()
        is_non_tech = any(sig in job_title_lower for sig in cls._NON_TECH_TITLE_SIGNALS)

        # ── Pass 1: vocabulary scan (multi-word first to avoid sub-matches) ─
        for skill in sorted(cls.KNOWN_SKILLS_VOCAB, key=len, reverse=True):
            # Skip pure-tech skills for clearly non-tech jobs
            if is_non_tech and skill in cls._TECH_ONLY_SKILLS:
                continue
            # Short/ambiguous terms: require word boundaries to avoid false
            # positives from substring matches (e.g. "rds" inside "records")
            if skill in cls._WORD_BOUNDARY_SKILLS:
                if re.search(r"\b" + re.escape(skill) + r"\b", combined_lower):
                    found.add(skill)
            else:
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
        # ── Tech ──────────────────────────────────────────────────────────
        "machine learning":     ["machine learning", "ml engineer", "ai engineer",
                                 "deep learning", "nlp engineer", "computer vision"],
        "data science":         ["data scientist", "data science"],
        "data engineering":     ["data engineer", "data pipeline", "etl", "elt"],
        "analytics":            ["data analyst", "business analyst", "analytics engineer",
                                 "bi developer", "business intelligence"],
        "software engineering": ["software engineer", "software developer", "backend engineer",
                                 "frontend engineer", "full stack", "fullstack", "web developer",
                                 "mobile developer", "ios developer", "android developer",
                                 "embedded engineer", "firmware engineer"],
        "devops":               ["devops", "sre", "site reliability", "platform engineer",
                                 "cloud engineer", "infrastructure engineer", "mlops"],
        "cybersecurity":        ["security engineer", "cybersecurity", "information security",
                                 "soc analyst", "penetration tester", "security analyst"],
        "product management":   ["product manager", "product owner", "program manager",
                                 "technical product"],
        "design":               ["ux designer", "ui designer", "graphic designer",
                                 "product designer", "visual designer", "interaction designer",
                                 "motion designer", "art director", "creative director"],

        # ── Finance & Accounting ───────────────────────────────────────────
        "accounting":           ["accountant", "bookkeeper", "controller", "comptroller",
                                 "accounts payable", "accounts receivable", "cpa", "ca",
                                 "management accountant", "cost accountant", "fund accountant"],
        "finance":              ["financial analyst", "finance manager", "banker", "trader",
                                 "actuary", "investment analyst", "portfolio manager",
                                 "treasury", "cfo", "budget analyst", "financial planner",
                                 "wealth manager", "credit analyst", "risk analyst"],
        "audit":                ["auditor", "internal auditor", "external auditor",
                                 "audit manager", "compliance auditor", "it auditor"],

        # ── Healthcare & Clinical ──────────────────────────────────────────
        "nursing":              ["nurse", "registered nurse", "rn", "lpn", "np",
                                 "nurse practitioner", "clinical nurse"],
        "medicine":             ["doctor", "physician", "surgeon", "specialist",
                                 "gp", "general practitioner", "resident", "fellow"],
        "allied health":        ["therapist", "physiotherapist", "occupational therapist",
                                 "speech therapist", "pharmacist", "dentist", "dental",
                                 "radiologist", "lab technician", "medical lab",
                                 "dietitian", "nutritionist", "optometrist"],
        "mental health":        ["psychologist", "psychiatrist", "counsellor", "counselor",
                                 "social worker", "mental health", "behavioural therapist"],
        "healthcare admin":     ["healthcare administrator", "medical office", "clinical coordinator",
                                 "health information", "patient coordinator", "medical secretary"],

        # ── Education ─────────────────────────────────────────────────────
        "teaching":             ["teacher", "educator", "instructor", "lecturer",
                                 "professor", "tutor", "teaching assistant"],
        "education admin":      ["principal", "vice principal", "school administrator",
                                 "curriculum coordinator", "education director"],
        "early childhood":      ["early childhood", "ece", "daycare", "childcare",
                                 "preschool", "kindergarten"],
        "corporate training":   ["trainer", "training specialist", "facilitator",
                                 "learning and development", "instructional designer",
                                 "e-learning developer"],

        # ── Human Resources ────────────────────────────────────────────────
        "hr":                   ["recruiter", "hr manager", "human resources",
                                 "talent acquisition", "people operations", "hrbp",
                                 "hr business partner", "hr generalist", "hr coordinator",
                                 "compensation", "benefits specialist", "payroll specialist"],

        # ── Marketing & Communications ─────────────────────────────────────
        "marketing":            ["marketing", "digital marketing", "content marketing",
                                 "seo specialist", "sem specialist", "content writer",
                                 "copywriter", "brand manager", "marketing manager",
                                 "communications", "public relations", "pr specialist",
                                 "social media manager", "email marketing"],
        "advertising":          ["media buyer", "media planner", "account director",
                                 "advertising", "campaign manager", "creative strategist"],

        # ── Sales ──────────────────────────────────────────────────────────
        "sales":                ["sales", "account executive", "account manager",
                                 "business development", "customer success", "sales manager",
                                 "sales representative", "inside sales", "outside sales",
                                 "territory manager", "channel sales"],

        # ── Legal ──────────────────────────────────────────────────────────
        "legal":                ["lawyer", "attorney", "solicitor", "barrister",
                                 "paralegal", "legal counsel", "corporate counsel",
                                 "compliance officer", "legal analyst", "notary",
                                 "legal assistant", "contracts manager"],

        # ── Operations & Supply Chain ──────────────────────────────────────
        "operations":           ["operations manager", "operations analyst", "operations coordinator",
                                 "business operations", "process improvement"],
        "supply chain":         ["supply chain", "logistics", "procurement", "purchasing",
                                 "inventory", "warehouse", "distribution", "import export",
                                 "freight", "customs", "demand planning"],
        "project management":   ["project manager", "project coordinator", "pmo",
                                 "delivery manager", "scrum master", "agile coach"],

        # ── Construction & Engineering ─────────────────────────────────────
        "civil engineering":    ["civil engineer", "structural engineer", "geotechnical",
                                 "site engineer", "construction manager", "site manager"],
        "mechanical engineering":["mechanical engineer", "manufacturing engineer",
                                 "process engineer", "maintenance engineer"],
        "electrical engineering":["electrical engineer", "electronics engineer",
                                 "control systems", "instrumentation"],

        # ── Hospitality & Retail ───────────────────────────────────────────
        "hospitality":          ["hotel", "restaurant", "chef", "cook", "bartender",
                                 "front desk", "concierge", "food and beverage",
                                 "catering", "hospitality manager"],
        "retail":               ["retail", "store manager", "merchandiser", "buyer",
                                 "visual merchandiser", "retail associate", "cashier"],

        # ── Real Estate ────────────────────────────────────────────────────
        "real estate":          ["real estate", "realtor", "property manager",
                                 "leasing agent", "mortgage", "appraisal",
                                 "real estate analyst"],

        # ── Research & Science ─────────────────────────────────────────────
        "research":             ["researcher", "research scientist", "research analyst",
                                 "biologist", "chemist", "physicist", "lab scientist",
                                 "r&d", "clinical researcher", "epidemiologist"],
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

        For each job:
          1. Extract skills via NLP (vocab scan + regex patterns)
          2. Look up the job title in JOB_TEMPLATES and merge the canonical
             skill baseline — guarantees correct skills even when the posting
             is sparse, badly written, or uses unusual phrasing.
          3. Return the unified job dict ready for the matching engine.
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

            # ── Step 1: NLP extraction ───────────────────────────────────────
            required_skills = self._extract_skills_from_text(job, description)
            preferred_skills: List[str] = []

            # ── Step 2: Template merge ───────────────────────────────────────
            # Look up the canonical skill baseline for this job title.
            # The template guarantees the right skills for every profession
            # even when the posting is sparse or badly written.
            # NLP-extracted skills are kept on top (union, deduped, sorted).
            job_title_str = self._safe_str(job.get("job_title"))
            template = find_template(job_title_str)
            if template:
                merged_req = set(required_skills) | {
                    s.lower() for s in template.get("required_skills", [])
                }
                required_skills = sorted(merged_req)

                merged_pref = set(preferred_skills) | {
                    s.lower() for s in template.get("preferred_skills", [])
                }
                preferred_skills = sorted(merged_pref)

            # ── Employment / workplace type ──────────────────────────────────
            emp_type = self._safe_str(job.get("job_employment_type")).lower()
            is_remote = bool(job.get("job_is_remote"))
            if is_remote:
                workplace_type = "remote"
            elif "hybrid" in description.lower():
                workplace_type = "hybrid"
            else:
                workplace_type = "onsite" if emp_type else ""

            # ── Location ─────────────────────────────────────────────────────
            city    = self._safe_str(job.get("job_city"))
            state   = self._safe_str(job.get("job_state"))
            country = self._safe_str(job.get("job_country"))
            location_parts = [p for p in [city, state, country] if p]
            location = ", ".join(location_parts) if location_parts else "Not specified"

            normalized.append(
                {
                    # Identifiers
                    "job_id":         job_id,
                    "title":          self._safe_str(job.get("job_title")),
                    "company":        self._safe_str(job.get("employer_name")),
                    "location":       location,
                    "workplace_type": workplace_type,

                    # Skills (template-backed + NLP-extracted)
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
                    "source_url":          self._safe_str(
                        job.get("job_apply_link") or job.get("job_google_link")
                    ),
                    "employer_logo":       self._safe_str(job.get("employer_logo")),
                    "description_snippet": description[:500],
                    "date_posted":         self._safe_str(job.get("job_posted_at_datetime_utc")),
                    "search_query":        search_query,
                }
            )

        return normalized
