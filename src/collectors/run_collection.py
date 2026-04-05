import json
import os
import pandas as pd

from greenhouse_collector import GreenhouseCollector
from lever_collector import LeverCollector


def ensure_dirs():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)


def load_sources(path: str = "data/company_sources.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def deduplicate_jobs(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    # Prefer URL + title dedupe
    df = df.drop_duplicates(subset=["source", "company_slug", "job_id"], keep="first")

    # Fallback dedupe for edge cases
    if "absolute_url" in df.columns and "title" in df.columns:
        df = df.drop_duplicates(subset=["absolute_url", "title"], keep="first")

    return df


def main():
    ensure_dirs()
    sources = load_sources()

    greenhouse_boards = sources.get("greenhouse_boards", [])
    lever_companies = sources.get("lever_companies", [])

    greenhouse_df = GreenhouseCollector(greenhouse_boards).collect_all()
    lever_df = LeverCollector(lever_companies).collect_all()

    combined_df = pd.concat([greenhouse_df, lever_df], ignore_index=True)
    combined_df = deduplicate_jobs(combined_df)

    raw_path_csv = "data/raw/jobs_raw.csv"
    raw_path_json = "data/raw/jobs_raw.json"

    combined_df.to_csv(raw_path_csv, index=False, encoding="utf-8")
    combined_df.to_json(raw_path_json, orient="records", indent=2, force_ascii=False)

    print(f"\nSaved {len(combined_df)} jobs")
    print(f"CSV:  {raw_path_csv}")
    print(f"JSON: {raw_path_json}")

    print("\nSample columns:")
    print(combined_df.columns.tolist())

    print("\nSample rows:")
    print(combined_df[[
        "source", "company_slug", "title", "location", "absolute_url"
    ]].head(10))


if __name__ == "__main__":
    main()