from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def ensure_dir(path: str | Path) -> Path:
    """
    Ensure a directory exists and return it as a Path.
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def ensure_parent_dir(file_path: str | Path) -> Path:
    """
    Ensure the parent directory of a file path exists.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def read_yaml(path: str | Path) -> dict[str, Any]:
    """
    Read a YAML file into a Python dictionary.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def write_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """
    Write Python data to JSON with UTF-8 encoding.
    """
    path = ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def read_json(path: str | Path) -> Any:
    """
    Read a JSON file and return Python data.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_dataframe_csv(df: pd.DataFrame, path: str | Path) -> None:
    """
    Write a DataFrame to CSV.
    """
    path = ensure_parent_dir(path)
    df.to_csv(path, index=False, encoding="utf-8")


def read_dataframe_csv(path: str | Path) -> pd.DataFrame:
    """
    Read a CSV file into a DataFrame.
    """
    return pd.read_csv(path)


def write_dataframe_json(df: pd.DataFrame, path: str | Path) -> None:
    """
    Write a DataFrame to JSON records.
    """
    path = ensure_parent_dir(path)
    df.to_json(path, orient="records", indent=2, force_ascii=False)


def timestamped_filename(prefix: str, extension: str, timestamp_str: str) -> str:
    """
    Build a timestamped filename.
    Example: greenhouse_jobs_2026-04-05T11-55-00.json
    """
    clean_extension = extension.lstrip(".")
    return f"{prefix}_{timestamp_str}.{clean_extension}"