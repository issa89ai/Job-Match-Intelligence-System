from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from src.ingestion.greenhouse import GreenhouseClient
from src.ingestion.lever import LeverClient
from src.utils.io import (
    ensure_dir,
    read_yaml,
    timestamped_filename,
    write_dataframe_csv,
    write_dataframe_json,
    write_json,
)
from src.utils.logger import add_file_handler, get_logger

from src.utils.text import clean_text, normalize_location_text, safe_json_string, stable_hash


logger = get_logger(__name__)
add_file_handler(logger, "logs/ingestion.log")


class IngestionPipeline:
    def __init__(self, config_path: str = "configs/sources.yaml") -> None:
        self.config = read_yaml(config_path)

        project_cfg = self.config.get("project", {})
        ingestion_cfg = self.config.get("ingestion", {})
        storage_cfg = self.config.get("storage", {})
        sources_cfg = self.config.get("sources", {})

        self.pipeline_version: str = project_cfg.get("pipeline_version", "1.0.0")
        self.request_timeout_seconds: int = ingestion_cfg.get("request_timeout_seconds", 20)
        self.max_retries: int = ingestion_cfg.get("max_retries", 2)
        self.user_agent: str = ingestion_cfg.get("user_agent", "job-match-intelligence/1.0")

        self.raw_jobs_dir = Path(storage_cfg.get("raw_jobs_dir", "data/raw/jobs"))
        self.staging_jobs_dir = Path(storage_cfg.get("staging_jobs_dir", "data/staging/jobs"))

        self.greenhouse_cfg = sources_cfg.get("greenhouse", {})
        self.lever_cfg = sources_cfg.get("lever", {})

        ensure_dir(self.raw_jobs_dir)
        ensure_dir(self.staging_jobs_dir)
        ensure_dir("logs")

        self.greenhouse_client = GreenhouseClient(
            request_timeout_seconds=self.request_timeout_seconds,
            user_agent=self.user_agent,
        )
        self.lever_client = LeverClient(
            request_timeout_seconds=self.request_timeout_seconds,
            user_agent=self.user_agent,
        )

    @staticmethod
    def _utc_now_strings() -> tuple[str, str]:
        now = datetime.now(UTC)
        iso_str = now.isoformat()
        file_str = now.strftime("%Y-%m-%dT%H-%M-%S")
        return iso_str, file_str

    def _fetch_with_retries(self, fetch_fn, source_type: str, source_name: str) -> list[dict[str, Any]]:
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 2):
            try:
                logger.info(
                    "Fetching source_type='%s' source_name='%s' attempt=%s",
                    source_type,
                    source_name,
                    attempt,
                )
                return fetch_fn(source_name)
            except requests.HTTPError as exc:
                last_error = exc
                status_code = exc.response.status_code if exc.response is not None else "unknown"
                logger.warning(
                    "HTTP error for source_type='%s' source_name='%s' status=%s attempt=%s",
                    source_type,
                    source_name,
                    status_code,
                    attempt,
                )
                if status_code == 404:
                    break
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Error for source_type='%s' source_name='%s' attempt=%s error='%s'",
                    source_type,
                    source_name,
                    attempt,
                    str(exc),
                )

        logger.error(
            "Failed source_type='%s' source_name='%s' after retries. error='%s'",
            source_type,
            source_name,
            str(last_error) if last_error else "unknown",
        )
        return []

    def _save_raw_snapshot(
        self,
        source_type: str,
        source_name: str,
        records: list[dict[str, Any]],
        timestamp_str: str,
    ) -> str:
        filename = timestamped_filename(
            prefix=f"{source_type}_{source_name}_jobs_raw",
            extension="json",
            timestamp_str=timestamp_str,
        )
        output_path = self.raw_jobs_dir / filename
        write_json(records, output_path)
        logger.info("Saved raw snapshot: %s", output_path)
        return str(output_path)

    def _postprocess_staging_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        processed: list[dict[str, Any]] = []

        for record in records:
            description_clean = clean_text(record.get("description_clean", ""))
            location_raw = record.get("location_raw", "")
            source_url = clean_text(record.get("source_url", ""))
            title_raw = clean_text(record.get("title_raw", ""))

            record["title_raw"] = title_raw
            record["description_clean"] = description_clean
            record["location_raw"] = clean_text(location_raw)
            record["location_normalized"] = normalize_location_text(location_raw)
            record["description_hash"] = stable_hash(description_clean)
            record["dedupe_key"] = stable_hash(f"{title_raw}::{source_url}")
            record["metadata_raw"] = safe_json_string(record.get("metadata_raw", {}))

            processed.append(record)

        return processed

    @staticmethod
    def _deduplicate_staging(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        preferred_columns = ["job_uid", "source", "source_company", "source_job_id"]
        existing_primary = [col for col in preferred_columns if col in df.columns]

        if len(existing_primary) == len(preferred_columns):
            df = df.drop_duplicates(subset=preferred_columns, keep="first")

        if "dedupe_key" in df.columns:
            df = df.drop_duplicates(subset=["dedupe_key"], keep="first")

        return df.reset_index(drop=True)

    def run(self) -> None:
        ingested_at, timestamp_str = self._utc_now_strings()

        logger.info("Starting ingestion pipeline version=%s", self.pipeline_version)

        all_records: list[dict[str, Any]] = []
        run_summary: list[dict[str, Any]] = []

        # Greenhouse
        if self.greenhouse_cfg.get("enabled", False):
            boards = self.greenhouse_cfg.get("boards", [])
            for board in boards:
                raw_jobs = self._fetch_with_retries(
                    self.greenhouse_client.fetch_jobs,
                    source_type="greenhouse",
                    source_name=board,
                )
                raw_path = self._save_raw_snapshot("greenhouse", board, raw_jobs, timestamp_str)

                normalized = self.greenhouse_client.normalize_jobs(
                    jobs=raw_jobs,
                    board_token=board,
                    pipeline_version=self.pipeline_version,
                    ingested_at=ingested_at,
                )
                normalized = self._postprocess_staging_records(normalized)
                all_records.extend(normalized)

                run_summary.append(
                    {
                        "source_type": "greenhouse",
                        "source_name": board,
                        "records_fetched": len(raw_jobs),
                        "records_normalized": len(normalized),
                        "raw_snapshot_path": raw_path,
                    }
                )

        # Lever
        if self.lever_cfg.get("enabled", False):
            companies = self.lever_cfg.get("companies", [])
            for company in companies:
                raw_jobs = self._fetch_with_retries(
                    self.lever_client.fetch_jobs,
                    source_type="lever",
                    source_name=company,
                )
                raw_path = self._save_raw_snapshot("lever", company, raw_jobs, timestamp_str)

                normalized = self.lever_client.normalize_jobs(
                    jobs=raw_jobs,
                    company_slug=company,
                    pipeline_version=self.pipeline_version,
                    ingested_at=ingested_at,
                )
                normalized = self._postprocess_staging_records(normalized)
                all_records.extend(normalized)

                run_summary.append(
                    {
                        "source_type": "lever",
                        "source_name": company,
                        "records_fetched": len(raw_jobs),
                        "records_normalized": len(normalized),
                        "raw_snapshot_path": raw_path,
                    }
                )

        staging_df = pd.DataFrame(all_records)
        staging_df = self._deduplicate_staging(staging_df)

        csv_filename = timestamped_filename(
            prefix="jobs_staging",
            extension="csv",
            timestamp_str=timestamp_str,
        )
        json_filename = timestamped_filename(
            prefix="jobs_staging",
            extension="json",
            timestamp_str=timestamp_str,
        )
        summary_filename = timestamped_filename(
            prefix="ingestion_run_summary",
            extension="json",
            timestamp_str=timestamp_str,
        )

        csv_path = self.staging_jobs_dir / csv_filename
        json_path = self.staging_jobs_dir / json_filename
        summary_path = self.staging_jobs_dir / summary_filename

        write_dataframe_csv(staging_df, csv_path)
        write_dataframe_json(staging_df, json_path)
        write_json(run_summary, summary_path)

        logger.info("Saved staging CSV: %s", csv_path)
        logger.info("Saved staging JSON: %s", json_path)
        logger.info("Saved run summary: %s", summary_path)
        logger.info("Ingestion complete. final_record_count=%s", len(staging_df))

        print("\nIngestion complete.")
        print(f"Staging CSV:  {csv_path}")
        print(f"Staging JSON: {json_path}")
        print(f"Run Summary:  {summary_path}")
        print(f"Final Records: {len(staging_df)}")

        if not staging_df.empty:
            preview_cols = [
                "source",
                "source_company",
                "title_raw",
                "location_normalized",
                "source_url",
            ]
            preview_cols = [c for c in preview_cols if c in staging_df.columns]
            print("\nSample rows:")
            print(staging_df[preview_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    pipeline = IngestionPipeline(config_path="configs/sources.yaml")
    pipeline.run()