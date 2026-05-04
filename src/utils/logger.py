from __future__ import annotations
# Enables modern type hints safely

import logging
# Python built-in logging system

from pathlib import Path
# Used for file path handling


# --------------------------------------------------
# MAIN LOGGER CREATION FUNCTION
# --------------------------------------------------

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create or return a configured logger.
    """

    logger = logging.getLogger(name)
    # Gets a logger with a specific name (module-based logging)

    if logger.handlers:
        return logger
        # IMPORTANT:
        # If logger already configured, return it directly
        # Avoids duplicate handlers (duplicate logs problem)

    logger.setLevel(level)
    # Set logging level (INFO by default)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Defines how logs look:
    # Example:
    # 2026-04-05 12:00:00 | INFO | ingestion | Fetching jobs...

    stream_handler = logging.StreamHandler()
    # Sends logs to console (terminal)

    stream_handler.setFormatter(formatter)
    # Apply formatting to console output

    logger.addHandler(stream_handler)
    # Attach handler to logger

    logger.propagate = False
    # Prevent logs from being duplicated in parent loggers

    return logger


# --------------------------------------------------
# FILE LOGGING (OPTIONAL)
# --------------------------------------------------

def add_file_handler(logger: logging.Logger, log_file_path: str | Path) -> None:
    """
    Add a file handler to an existing logger.
    """

    log_file_path = Path(log_file_path)

    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    # Ensure directory exists before writing log file

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Same format as console logs

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    # Logs will also be written to a file

    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    # Attach file handler to logger