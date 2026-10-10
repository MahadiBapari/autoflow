"""Logging configuration: console output plus a rotating-free log file."""

from __future__ import annotations

import logging
from pathlib import Path

from autoflow.config import LOG_DIR

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(level: int = logging.INFO, log_dir: Path = LOG_DIR) -> None:
    """Configure the 'autoflow' logger once. Safe to call repeatedly."""
    logger = logging.getLogger("autoflow")
    if logger.handlers:
        return
    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "autoflow.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as exc:  # e.g. read-only filesystem; console logging still works
        logger.warning("File logging disabled: %s", exc)
