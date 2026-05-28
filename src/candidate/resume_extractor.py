from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────
# File-format text extraction
# ─────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a PDF file using pdfplumber."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages).strip()
    except Exception as exc:
        raise ValueError(f"Could not read PDF: {exc}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from a Word (.docx) file."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs).strip()
    except Exception as exc:
        raise ValueError(f"Could not read DOCX: {exc}")


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Route to the correct extractor based on file extension."""
    name = filename.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    elif name.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore").strip()
    else:
        raise ValueError(f"Unsupported file type: {filename}. Please upload PDF, DOCX, or TXT.")


# ─────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────

def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _find_section(text: str, *headers: str) -> str:
    """
    Return the text block that follows any of the given section headers.
    Stops at the next capitalised section heading or after 20 lines.
    """
    pattern = r"(?i)(?:" + "|".join(re.escape(h) for h in headers) + r")\s*[:\-]?\s*\n(.*?)(?=\n[A-Z][A-Z /&]+[\s]*[:\n]|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _extract_items_from_block(block: str) -> List[str]:
    """Split a section block into individual items (bullets, commas, newlines)."""
    if not block:
        return []
    # Split on bullets, newlines, commas, semicolons, pipes
    parts = re.split(r"[•·▪\-–,;|\n]+", block)
    return [_norm(p).lower() for p in parts if len(_norm(p)) > 1]


# ─────────────────────────────────────────────
# Individual field extractors
# ─────────────────────────────────────────────

def _extract_name(lines: List[str]) -> str:
    """First non-empty line is usually the candidate's name."""
    for line in lines[:5]:
        line = _norm(line)
        # Skip lines that look like contact info or titles
        if line and not re.search(r"[@|/\\]|http|linkedin|github|\d{3}", line, re.I):
            if len(line.split()) <= 5:
                return line
    return ""


def _extract_title(lines: List[str], text: str) -> str:
    """Second meaningful line or a line matching common title patterns."""
    title_keywords = [
        "engineer", "scientist", "analyst", "developer", "manager",
        "architect", "consultant", "specialist", "director", "lead",
        "designer", "researcher", "intern",
    ]
    for line in lines[1:8]:
        line = _norm(line)
        if any(kw in line.lower() for kw in title_keywords) and len(line) < 80:
            return line
    return ""


def _extract_email(text: str) -> str:
    m = re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else ""


def _extract_location(lines: List[str]) -> str:
    location_hints = [
        "ottawa", "toronto", "vancouver", "montreal", "calgary",
        "remote", "canada", "new york", "san francisco", "london",
        "berlin", "seattle", "boston", "austin", "chicago",
        "dubai", "paris", "sydney", "melbourne",
    ]
    for line in lines[:10]:
        ln = _norm(line).lower()
        if any(h in ln for h in location_hints):
            return _norm(line).split("|")[0].split("·")[0].strip()
    return ""


def _extract_education(text: str) -> Optional[str]:
    edu_map = [
        (r"\bph\.?d\b|\bdoctorate\b", "phd"),
        (r"\bmaster'?s?\b|\bmsc\b|\bmba\b|\bm\.s\.?\b|\bm\.eng\b", "master"),
        (r"\bbachelor'?s?\b|\bbsc\b|\bb\.s\.?\b|\bb\.a\.?\b|\bb\.eng\b", "bachelor"),
        (r"\bassociate'?s?\b|\bassociate degree\b", "associate"),
        (r"\bhigh school\b|\bsecondary school\b|\bdipl[oô]me\b", "high_school"),
    ]
    for pattern, level in edu_map:
        if re.search(pattern, text, re.IGNORECASE):
            return level
    return None


def _extract_years_experience(text: str) -> Optional[int]:
    # Explicit "X years of experience" pattern
    patterns = [
        r"(\d+)\s*\+?\s*years?\s+of\s+(?:professional\s+)?experience",
        r"(\d+)\s*\+?\s*years?\s+experience",
        r"experience\s+of\s+(\d+)\s*\+?\s*years?",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return int(m.group(1))

    # Fallback: infer from date ranges in work experience
    years = re.findall(r"\b(20\d{2})\b", text)
    if len(years) >= 2:
        years_int = sorted([int(y) for y in years])
        span = years_int[-1] - years_int[0]
        if 1 <= span <= 40:
            return span
    return None


def _extract_seniority(title: str, text: str, years: Optional[int]) -> Optional[str]:
    title_l = (title or "").lower()
    text_l = text.lower()

    if any(k in title_l for k in ["vp ", "vice president", "director", "head of", "principal", "chief"]):
        return "manager"
    if any(k in title_l for k in ["senior", "sr.", "sr ", "lead", "staff"]):
        return "senior"
    if any(k in title_l for k in ["junior", "jr.", "jr ", "entry"]):
        return "entry"
    if "intern" in title_l:
        return "intern"
    if "mid" in title_l or "mid-level" in title_l:
        return "mid"

    if years is not None:
        if years >= 10:
            return "manager"
        if years >= 7:
            return "senior"
        if years >= 3:
            return "mid"
        if years >= 0:
            return "entry"
    return None


KNOWN_SKILLS = [
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go",
    "rust", "swift", "kotlin", "ruby", "php", "scala", "r", "matlab",
    "bash", "shell", "perl", "dart",
    # ML / AI
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "reinforcement learning", "llm", "generative ai",
    "transformers", "bert", "gpt", "langchain", "rag",
    "scikit-learn", "tensorflow", "pytorch", "keras", "xgboost", "lightgbm",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    # Data
    "sql", "postgresql", "mysql", "sqlite", "mongodb", "redis",
    "elasticsearch", "cassandra", "dynamodb", "bigquery", "snowflake",
    "dbt", "airflow", "spark", "kafka", "hadoop", "hive",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
    "terraform", "ansible", "jenkins", "github actions", "ci/cd",
    "linux", "git",
    # Web & APIs
    "fastapi", "django", "flask", "spring", "node.js", "react",
    "vue.js", "angular", "graphql", "rest api",
    # BI & Analytics
    "power bi", "tableau", "looker", "excel", "google analytics",
    "statistics", "data visualization", "data analysis", "data engineering",
    "a/b testing", "hypothesis testing",
]

KNOWN_TOOLS = [
    "jupyter", "vscode", "pycharm", "git", "github", "gitlab",
    "jira", "confluence", "slack", "notion", "figma",
    "postman", "swagger", "linux", "windows", "macos",
    "excel", "google sheets", "power bi", "tableau",
    "docker", "kubernetes", "terraform",
]

KNOWN_DOMAINS = [
    "machine learning", "data science", "data engineering", "analytics",
    "software engineering", "backend", "frontend", "full stack",
    "devops", "cloud", "cybersecurity", "fintech", "healthtech",
    "e-commerce", "nlp", "computer vision", "ai", "artificial intelligence",
    "business intelligence", "product management",
]


def _extract_skills_smart(text: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Extract skills, tools and domains using:
    1. Explicit labelled sections first ("Skills:", "Technical Skills:", etc.)
    2. Full-text scan for known terms as fallback.

    Returns (skills, tools, domains).
    """
    text_lower = text.lower()

    # ── Try section-based extraction first ──────────────────
    skills_block = _find_section(
        text,
        "Technical Skills", "Skills", "Core Skills",
        "Compétences", "Technologies", "Tech Stack",
    )
    tools_block = _find_section(text, "Tools", "Software", "Technologies Used")
    domains_block = _find_section(text, "Domains", "Areas of Expertise", "Expertise")

    section_skills = _extract_items_from_block(skills_block)
    section_tools = _extract_items_from_block(tools_block)
    section_domains = _extract_items_from_block(domains_block)

    # Filter section items against known vocabularies
    skills = sorted(set(
        s for s in section_skills
        if any(k in s for k in KNOWN_SKILLS) or len(s) > 2
    ))
    tools = sorted(set(
        t for t in section_tools
        if any(k in t for k in KNOWN_TOOLS) or len(t) > 2
    ))
    domains = sorted(set(
        d for d in section_domains
        if any(k in d for k in KNOWN_DOMAINS) or len(d) > 2
    ))

    # ── Full-text scan for known skills not caught above ───
    scanned_skills = [s for s in KNOWN_SKILLS if s in text_lower and s not in skills]
    scanned_tools = [t for t in KNOWN_TOOLS if t in text_lower and t not in tools and t not in skills]
    scanned_domains = [d for d in KNOWN_DOMAINS if d in text_lower and d not in domains]

    skills = sorted(set(skills + scanned_skills))
    tools = sorted(set(tools + scanned_tools))
    domains = sorted(set(domains + scanned_domains))

    return skills, tools, domains


def _extract_summary(text: str) -> str:
    """Pull text from a Summary / Profile / Objective section."""
    block = _find_section(
        text,
        "Summary", "Professional Summary", "Profile",
        "About Me", "Objective", "Career Objective",
    )
    if block:
        return _norm(block)[:600]

    # Fallback: use the first substantial paragraph
    for para in text.split("\n\n"):
        para = _norm(para)
        if len(para) > 80:
            return para[:600]
    return ""


def _extract_certifications(text: str) -> List[str]:
    block = _find_section(
        text,
        "Certifications", "Certificates", "Licences",
        "Professional Certifications",
    )
    return _extract_items_from_block(block)


def _extract_projects(text: str) -> List[str]:
    block = _find_section(text, "Projects", "Personal Projects", "Key Projects", "Portfolio")
    items = _extract_items_from_block(block)
    # Keep only project-name-like items (short phrases)
    return [i for i in items if 2 < len(i.split()) <= 10][:8]


# ─────────────────────────────────────────────
# Profile completeness scorer
# ─────────────────────────────────────────────

COMPLETENESS_WEIGHTS: Dict[str, int] = {
    "skills":           25,
    "years_experience": 15,
    "current_title":    15,
    "education":        10,
    "seniority":        10,
    "domains":          10,
    "summary":          10,
    "location":          5,
}

COMPLETENESS_LABELS: Dict[str, str] = {
    "skills":           "Skills (list at least 3)",
    "years_experience": "Years of experience",
    "current_title":    "Current job title",
    "education":        "Education level",
    "seniority":        "Seniority level",
    "domains":          "Domain / industry",
    "summary":          "Professional summary",
    "location":         "Location",
}


def compute_profile_completeness(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a dict with:
      - score (0–100 int)
      - filled   list of filled field names
      - missing  list of (field_name, label, weight) for missing fields
    """
    filled = []
    missing = []

    def _has(key: str) -> bool:
        val = profile.get(key)
        if val is None or val == "" or val == 0:
            return False
        if isinstance(val, list):
            return len(val) >= 1
        return True

    def _skills_ok() -> bool:
        val = profile.get("skills", [])
        return isinstance(val, list) and len(val) >= 3

    checks = {
        "skills":           _skills_ok(),
        "years_experience": _has("years_experience"),
        "current_title":    _has("current_title"),
        "education":        _has("education"),
        "seniority":        _has("seniority"),
        "domains":          _has("domains"),
        "summary":          _has("summary"),
        "location":         _has("location"),
    }

    score = 0
    for field, ok in checks.items():
        if ok:
            score += COMPLETENESS_WEIGHTS[field]
            filled.append(field)
        else:
            missing.append({
                "field": field,
                "label": COMPLETENESS_LABELS[field],
                "weight": COMPLETENESS_WEIGHTS[field],
            })

    # Sort missing by weight descending so most impactful shows first
    missing.sort(key=lambda x: x["weight"], reverse=True)

    return {"score": score, "filled": filled, "missing": missing}


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────

def parse_resume(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Full pipeline:
      1. Extract raw text from the uploaded file
      2. Parse all candidate fields from the text
      3. Compute profile completeness
      4. Return structured result ready for the API response
    """
    raw_text = extract_text(file_bytes, filename)

    if not raw_text.strip():
        raise ValueError("The uploaded file appears to be empty or could not be read.")

    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

    full_name       = _extract_name(lines)
    current_title   = _extract_title(lines, raw_text)
    location        = _extract_location(lines)
    education       = _extract_education(raw_text)
    years_exp       = _extract_years_experience(raw_text)
    skills, tools, domains = _extract_skills_smart(raw_text)
    seniority       = _extract_seniority(current_title, raw_text, years_exp)
    summary         = _extract_summary(raw_text)
    certifications  = _extract_certifications(raw_text)
    projects        = _extract_projects(raw_text)

    profile = {
        "candidate_id":      "candidate_001",    # overwritten by active profile
        "full_name":         full_name,
        "current_title":     current_title,
        "location":          location,
        "education":         education,
        "years_experience":  years_exp or 0,
        "skills":            skills,
        "tools":             tools,
        "domains":           domains,
        "seniority":         seniority,
        "summary":           summary,
        "certifications":    certifications,
        "projects":          projects,
    }

    completeness = compute_profile_completeness(profile)

    return {
        "extracted_profile": profile,
        "completeness":      completeness,
        "raw_text_preview":  raw_text[:800],
    }
