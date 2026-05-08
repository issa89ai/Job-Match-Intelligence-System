from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml

# Extract education requirement from job text
from src.extraction.education import extract_education_min

# Extract minimum years of experience from job text
from src.extraction.experience import extract_years_experience_min

# Infer seniority level from title, text, and experience
from src.extraction.seniority import infer_seniority

# Extract required/preferred/other skills using section-aware logic
from src.extraction.skills import extract_skills_section_aware


# Project root path
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Input folder from Phase 3
CURATED_DIR = PROJECT_ROOT / "data" / "curated" / "requirements"

# Output folder for enriched requirement dataset
ENRICHED_DIR = PROJECT_ROOT / "data" / "curated" / "requirements_enriched"

# Config folder containing skills.yaml
CONFIG_DIR = PROJECT_ROOT / "configs"


def load_yaml(path: Path) -> dict:
    """
    Load YAML configuration file.
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_latest_curated_file() -> Path:
    """
    Find the latest curated jobs CSV from Phase 3.
    """
    files = sorted(CURATED_DIR.glob("jobs_curated_*.csv"))

    if not files:
        raise FileNotFoundError(f"No curated files found in {CURATED_DIR}")

    # Return the last file after sorting by filename.
    return files[-1]


def ensure_output_dir() -> None:
    """
    Ensure enriched output directory exists.
    """
    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)


def clean_html(text: str) -> str:
    """
    Remove HTML tags/entities and normalize whitespace.
    """
    if not isinstance(text, str):
        return ""

    # Remove HTML tags like <p>, <div>, etc.
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove common HTML entities
    text = re.sub(r"&nbsp;|&amp;|&lt;|&gt;|&#39;|&quot;", " ", text)

    # Normalize repeated whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def build_job_text(row: pd.Series) -> str:
    """
    Combine available job text fields into one text block for extraction.
    """

    # Collect possible text columns from different pipeline versions.
    fields = [
        row.get("title", ""),
        row.get("title_raw", ""),
        row.get("description", ""),
        row.get("description_raw", ""),
        row.get("description_clean", ""),
        row.get("description_normalized", ""),
        row.get("job_description", ""),
        row.get("requirements", ""),
    ]

    # Join all non-missing fields into one text string.
    text = " ".join(str(x) for x in fields if pd.notna(x))

    # Clean HTML and return final text.
    return clean_html(text.strip())


def extract_row_requirements(row: pd.Series, skill_aliases: Dict[str, List[str]]) -> dict:
    """
    Extract structured requirements from one job row.
    """

    # Prefer title column, fallback to title_raw.
    title = str(row.get("title", "") or row.get("title_raw", "") or "")

    # Build full searchable job text.
    text = build_job_text(row)

    # Extract skills into required/preferred/other.
    required_skills, preferred_skills, other_skills_found = extract_skills_section_aware(
        text,
        skill_aliases,
    )

    # Extract minimum years of experience.
    years_experience_extracted = extract_years_experience_min(text)

    # Extract minimum education requirement.
    education_extracted = extract_education_min(text)

    # Infer seniority level.
    seniority_inferred = infer_seniority(
        title,
        text,
        years_experience_extracted,
    )

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "other_skills_found": other_skills_found,
        "years_experience_extracted": years_experience_extracted,
        "education_extracted": education_extracted,
        "seniority_inferred": seniority_inferred,
    }


def run_requirement_extraction(input_path: Path | None = None) -> Path:
    """
    Run the full Phase 4 requirement extraction pipeline.
    """

    # Make sure output folder exists.
    ensure_output_dir()

    # If no input path is provided, use latest curated file.
    if input_path is None:
        input_path = find_latest_curated_file()

    # Load skill taxonomy from config.
    skills_config = load_yaml(CONFIG_DIR / "skills.yaml")

    # Get skills section if present.
    skill_aliases = skills_config.get("skills", skills_config)

    # Load curated job dataset.
    df = pd.read_csv(input_path)

    extracted_records = []

    # Extract requirements row by row.
    for _, row in df.iterrows():
        extracted = extract_row_requirements(row, skill_aliases)
        extracted_records.append(extracted)

    # Convert extracted dictionaries into DataFrame.
    extracted_df = pd.DataFrame(extracted_records)

    # Combine original curated data + extracted requirement fields.
    output_df = pd.concat(
        [df.reset_index(drop=True), extracted_df.reset_index(drop=True)],
        axis=1,
    )

    # Convert skill list columns into JSON strings for CSV storage.
    for col in ["required_skills", "preferred_skills", "other_skills_found"]:
        output_df[col] = output_df[col].apply(
            lambda x: json.dumps(x, ensure_ascii=False)
        )

    # Timestamped output file.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path = ENRICHED_DIR / f"jobs_requirements_enriched_{timestamp}.csv"

    # Save enriched dataset.
    output_df.to_csv(output_path, index=False)

    print("[Phase 4] Requirement extraction completed.")
    print(f"[Phase 4] Input:  {input_path}")
    print(f"[Phase 4] Output: {output_path}")
    print(f"[Phase 4] Rows:   {len(output_df)}")

    return output_path


if __name__ == "__main__":
    run_requirement_extraction()