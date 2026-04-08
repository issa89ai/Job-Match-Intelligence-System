from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml

from src.extraction.education import extract_education_min
from src.extraction.experience import extract_years_experience_min
from src.extraction.seniority import infer_seniority
from src.extraction.skills import extract_skills_section_aware


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURATED_DIR = PROJECT_ROOT / "data" / "curated" / "requirements"
ENRICHED_DIR = PROJECT_ROOT / "data" / "curated" / "requirements_enriched"
CONFIG_DIR = PROJECT_ROOT / "configs"


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_latest_curated_file() -> Path:
    files = sorted(CURATED_DIR.glob("jobs_curated_*.csv"))
    if not files:
        raise FileNotFoundError(f"No curated files found in {CURATED_DIR}")
    return files[-1]


def ensure_output_dir() -> None:
    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)


def clean_html(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&amp;|&lt;|&gt;|&#39;|&quot;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_job_text(row: pd.Series) -> str:
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
    text = " ".join(str(x) for x in fields if pd.notna(x))
    return clean_html(text.strip())


def extract_row_requirements(row: pd.Series, skill_aliases: Dict[str, List[str]]) -> dict:
    title = str(row.get("title", "") or row.get("title_raw", "") or "")
    text = build_job_text(row)

    required_skills, preferred_skills, other_skills_found = extract_skills_section_aware(text, skill_aliases)
    years_experience_extracted = extract_years_experience_min(text)
    education_extracted = extract_education_min(text)
    seniority_inferred = infer_seniority(title, text, years_experience_extracted)

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "other_skills_found": other_skills_found,
        "years_experience_extracted": years_experience_extracted,
        "education_extracted": education_extracted,
        "seniority_inferred": seniority_inferred,
    }


def run_requirement_extraction(input_path: Path | None = None) -> Path:
    ensure_output_dir()

    if input_path is None:
        input_path = find_latest_curated_file()

    skills_config = load_yaml(CONFIG_DIR / "skills.yaml")
    skill_aliases = skills_config.get("skills", skills_config)

    df = pd.read_csv(input_path)

    extracted_records = []
    for _, row in df.iterrows():
        extracted = extract_row_requirements(row, skill_aliases)
        extracted_records.append(extracted)

    extracted_df = pd.DataFrame(extracted_records)
    output_df = pd.concat([df.reset_index(drop=True), extracted_df.reset_index(drop=True)], axis=1)

    for col in ["required_skills", "preferred_skills", "other_skills_found"]:
        output_df[col] = output_df[col].apply(lambda x: json.dumps(x, ensure_ascii=False))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = ENRICHED_DIR / f"jobs_requirements_enriched_{timestamp}.csv"
    output_df.to_csv(output_path, index=False)

    print("[Phase 4] Requirement extraction completed.")
    print(f"[Phase 4] Input:  {input_path}")
    print(f"[Phase 4] Output: {output_path}")
    print(f"[Phase 4] Rows:   {len(output_df)}")

    return output_path


if __name__ == "__main__":
    run_requirement_extraction()