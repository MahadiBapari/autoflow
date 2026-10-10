"""Write cleaned / rejected / summary reports into a fresh run folder.

Each run gets its own timestamped directory, so previous outputs are never
overwritten. The original input file is only ever read, never written.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from autoflow.config import CLEANED_REPORT_NAME, REJECTED_REPORT_NAME, SUMMARY_REPORT_NAME

logger = logging.getLogger(__name__)


def _safe_stem(name: str) -> str:
    stem = Path(name).stem or "input"
    return re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_") or "input"


def create_run_dir(base_dir: Path, input_name: str, now: Optional[datetime] = None) -> Path:
    """Create and return a new, unique directory for one run.

    Named ``<input-stem>_<YYYYmmdd_HHMMSS>``; a numeric suffix is appended if
    that name is already taken. Uses ``exist_ok=False`` so an existing folder
    is never reused.
    """
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    timestamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    base_name = f"{_safe_stem(input_name)}_{timestamp}"

    counter = 0
    while True:
        candidate = base_dir / (base_name if counter == 0 else f"{base_name}_{counter}")
        try:
            candidate.mkdir(exist_ok=False)
            return candidate
        except FileExistsError:
            counter += 1


def archive_input(run_dir: Path, data: bytes, filename: str) -> Path:
    """Save a copy of the original input bytes into the run folder."""
    target = Path(run_dir) / f"input_{Path(filename).name}"
    with open(target, "xb") as fh:  # 'x' mode refuses to overwrite
        fh.write(data)
    return target


def write_reports(
    run_dir: Path,
    cleaned: pd.DataFrame,
    rejected: pd.DataFrame,
    summary: dict,
) -> Dict[str, Path]:
    """Write the three report files and return their paths keyed by type."""
    run_dir = Path(run_dir)
    paths = {
        "cleaned": run_dir / CLEANED_REPORT_NAME,
        "rejected": run_dir / REJECTED_REPORT_NAME,
        "summary": run_dir / SUMMARY_REPORT_NAME,
    }
    for path in paths.values():
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite existing report: {path}")

    cleaned.to_csv(paths["cleaned"], index=False, float_format="%.2f")
    rejected.to_csv(paths["rejected"], index=False)
    paths["summary"].write_text(json.dumps(summary, indent=2), encoding="utf-8")

    logger.info("Reports written to %s", run_dir)
    return paths
