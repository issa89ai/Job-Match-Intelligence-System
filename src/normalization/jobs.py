from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.normalization.locations import normalize_location_record
from src.normalization.titles import normalize_title_record
from src.utils.io import (
    ensure_dir,
    read_dataframe_csv,
    timestamped_filename,
    write_dataframe_csv,
    write_dataframe_json,
)
from src.utils.logger import add_file_handler, get_logger
from src.utils.text import clean_text, stable_hash


logger = get_logger(__name__)
add_file_handler(logger, "logs/normalization.log")


class JobNormalizationPipeline:
    def __init__(
        self,
        staging_input_path: str,
        curated_output_dir: str = "data/curated/requirements",
        timestamp_str: str | None = None,
    ) -> None:
        self.staging_input_path = staging_input_path
        self.curated_output_dir = Path(curated_output_dir)
        ensure_dir(self.curated_output_dir)

        if timestamp_str is None:
            timestamp_str = pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        self.timestamp_str = timestamp_str

    def load_staging_jobs(self) -> pd.DataFrame:
        logger.info("Loading staging jobs from %s", self.staging_input_path)
        return read_dataframe_csv(self.staging_input_path)

    @staticmethod
    def normalize_description_text(df: pd.DataFrame) -> pd.DataFrame:
        df["description_clean"] = df["description_clean"].apply(clean_text)
        df["language"] = df["language"].fillna("").astype(str)

        df["description_normalized"] = (
            df["description_clean"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        return df

    @staticmethod
    def normalize_titles(df: pd.DataFrame) -> pd.DataFrame:
        title_records = df["title_raw"].apply(normalize_title_record)
        title_df = pd.json_normalize(title_records)

        for col in title_df.columns:
            df[col] = title_df[col]

        return df

    @staticmethod
    def normalize_locations(df: pd.DataFrame) -> pd.DataFrame:
        location_records = df.apply(
            lambda row: normalize_location_record(
                location_raw=row.get("location_raw", ""),
                description_clean=row.get("description_clean", ""),
            ),
            axis=1,
        )
        location_df = pd.json_normalize(location_records)

        for col in location_df.columns:
            df[col] = location_df[col]

        return df

    @staticmethod
    def compute_curated_hashes(df: pd.DataFrame) -> pd.DataFrame:
        df["curated_record_hash"] = df.apply(
            lambda row: stable_hash(
                "::".join(
                    [
                        clean_text(str(row.get("job_uid", ""))),
                        clean_text(str(row.get("title_normalized", ""))),
                        clean_text(str(row.get("location_normalized", ""))),
                        clean_text(str(row.get("description_clean", ""))),
                    ]
                )
            ),
            axis=1,
        )
        return df

    @staticmethod
    def deduplicate_curated(df: pd.DataFrame) -> pd.DataFrame:
        if "curated_record_hash" in df.columns:
            df = df.drop_duplicates(subset=["curated_record_hash"], keep="first")
        return df.reset_index(drop=True)

    @staticmethod
    def select_final_columns(df: pd.DataFrame) -> pd.DataFrame:
        final_columns = [
            "job_uid",
            "source",
            "source_company",
            "source_job_id",
            "source_url",
            "ingested_at",
            "source_updated_at",
            "pipeline_version",
            "title_raw",
            "title_normalized",
            "job_family",
            "job_function",
            "seniority_level",
            "employment_type",
            "workplace_type",
            "location_raw",
            "location_normalized",
            "country",
            "region",
            "description_raw",
            "description_clean",
            "description_normalized",
            "language",
            "description_hash",
            "dedupe_key",
            "department",
            "team",
            "years_experience_min",
            "years_experience_preferred",
            "education_min",
            "is_remote",
            "is_hybrid",
            "is_onsite",
            "metadata_raw",
            "curated_record_hash",
        ]
        existing_columns = [col for col in final_columns if col in df.columns]
        return df[existing_columns]

    def save_outputs(self, df: pd.DataFrame) -> tuple[Path, Path]:
        csv_name = timestamped_filename(
            prefix="jobs_curated",
            extension="csv",
            timestamp_str=self.timestamp_str,
        )
        json_name = timestamped_filename(
            prefix="jobs_curated",
            extension="json",
            timestamp_str=self.timestamp_str,
        )

        csv_path = self.curated_output_dir / csv_name
        json_path = self.curated_output_dir / json_name

        write_dataframe_csv(df, csv_path)
        write_dataframe_json(df, json_path)

        logger.info("Saved curated CSV: %s", csv_path)
        logger.info("Saved curated JSON: %s", json_path)
        return csv_path, json_path

    def run(self) -> None:
        logger.info("Starting job normalization pipeline")
        df = self.load_staging_jobs()

        logger.info("Initial staging record count=%s", len(df))

        df = self.normalize_description_text(df)
        df = self.normalize_titles(df)
        df = self.normalize_locations(df)
        df = self.compute_curated_hashes(df)
        df = self.deduplicate_curated(df)
        df = self.select_final_columns(df)

        logger.info("Final curated record count=%s", len(df))

        csv_path, json_path = self.save_outputs(df)

        print("\nNormalization complete.")
        print(f"Curated CSV:  {csv_path}")
        print(f"Curated JSON: {json_path}")
        print(f"Final Records: {len(df)}")

        if not df.empty:
            preview_cols = [
                "title_raw",
                "title_normalized",
                "job_family",
                "seniority_level",
                "location_normalized",
                "country",
                "region",
                "workplace_type",
            ]
            preview_cols = [c for c in preview_cols if c in df.columns]
            print("\nSample rows:")
            print(df[preview_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    INPUT_STAGING_FILE = "data/staging/jobs/jobs_staging_2026-04-06T03-18-32.csv"

    pipeline = JobNormalizationPipeline(
        staging_input_path=INPUT_STAGING_FILE,
        curated_output_dir="data/curated/requirements",
    )
    pipeline.run()