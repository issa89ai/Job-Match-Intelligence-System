from __future__ import annotations
# Allows using modern type hints (like list[str]) safely across Python versions

import json
# Used for reading/writing JSON files

from pathlib import Path
# Modern way to handle file paths (better than os.path)

from typing import Any
# Allows flexible typing (any kind of data)

import pandas as pd
# Used for handling tabular data (CSV, DataFrames)

import yaml
# Used for reading YAML config files


# --------------------------------------------------
# DIRECTORY MANAGEMENT
# --------------------------------------------------

def ensure_dir(path: str | Path) -> Path:
    """
    Ensure a directory exists and return it as a Path.
    """
    directory = Path(path)  # Convert input to Path object
    directory.mkdir(parents=True, exist_ok=True)
    # Create directory (and parents if needed), no error if already exists
    return directory


def ensure_parent_dir(file_path: str | Path) -> Path:
    """
    Ensure the parent directory of a file path exists.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Ensures folder exists before writing file
    return path


# --------------------------------------------------
# YAML HANDLING
# --------------------------------------------------

def read_yaml(path: str | Path) -> dict[str, Any]:
    """
    Read a YAML file into a Python dictionary.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        # safe_load avoids executing unsafe code (important security practice)
    return data or {}
    # Return empty dict if file is empty


# --------------------------------------------------
# JSON HANDLING
# --------------------------------------------------

def write_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """
    Write Python data to JSON with UTF-8 encoding.
    """
    path = ensure_parent_dir(path)  # Ensure directory exists
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
        # ensure_ascii=False → supports UTF-8 characters


def read_json(path: str | Path) -> Any:
    """
    Read a JSON file and return Python data.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------
# DATAFRAME (CSV)
# --------------------------------------------------

def write_dataframe_csv(df: pd.DataFrame, path: str | Path) -> None:
    """
    Write a DataFrame to CSV.
    """
    path = ensure_parent_dir(path)
    df.to_csv(path, index=False, encoding="utf-8")
    # index=False avoids unnecessary index column


def read_dataframe_csv(path: str | Path) -> pd.DataFrame:
    """
    Read a CSV file into a DataFrame.
    """
    return pd.read_csv(path)


# --------------------------------------------------
# DATAFRAME (JSON)
# --------------------------------------------------

def write_dataframe_json(df: pd.DataFrame, path: str | Path) -> None:
    """
    Write a DataFrame to JSON records.
    """
    path = ensure_parent_dir(path)
    df.to_json(path, orient="records", indent=2, force_ascii=False)
    # orient="records" → list of dicts (good for APIs)


# --------------------------------------------------
# FILENAME UTILITY
# --------------------------------------------------

def timestamped_filename(prefix: str, extension: str, timestamp_str: str) -> str:
    """
    Build a timestamped filename.
    Example: greenhouse_jobs_2026-04-05T11-55-00.json
    """
    clean_extension = extension.lstrip(".")
    # removes leading dot if user gives ".json"

    return f"{prefix}_{timestamp_str}.{clean_extension}"