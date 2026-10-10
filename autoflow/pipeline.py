"""End-to-end order processing: load → validate → normalize → report."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

import pandas as pd

from autoflow.config import OUTPUT_DIR
from autoflow.loader import FileLoadError, load_file
from autoflow.normalizer import normalize
from autoflow.reporter import archive_input, create_run_dir, write_reports
from autoflow.validator import check_required_columns, validate_rows

logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    """Outcome of one pipeline run. ``error`` is set when the run failed."""

    cleaned: pd.DataFrame = field(default_factory=pd.DataFrame)
    rejected: pd.DataFrame = field(default_factory=pd.DataFrame)
    summary: Dict[str, int] = field(default_factory=dict)
    output_paths: Dict[str, Path] = field(default_factory=dict)
    run_dir: Optional[Path] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


def run_pipeline(
    source: Union[str, Path, bytes],
    filename: Optional[str] = None,
    output_dir: Union[str, Path] = OUTPUT_DIR,
) -> ProcessResult:
    """Process one order file and write its reports to a new run folder.

    Never raises: expected problems (malformed file, missing columns) and
    unexpected exceptions are both returned via ``ProcessResult.error``.
    No output folder is created when the input cannot be processed.
    """
    filename = filename or (Path(source).name if not isinstance(source, bytes) else None)
    logger.info("Starting run for %s", filename)
    try:
        df = load_file(source, filename)

        missing = check_required_columns(df)
        if missing:
            found = ", ".join(df.columns) or "none"
            return _fail(f"Missing required columns: {', '.join(missing)}. Found columns: {found}.")

        valid, rejected, duplicates = validate_rows(df)
        cleaned = normalize(valid)

        summary = {
            "total_records": len(df),
            "valid_records": len(cleaned),
            "rejected_records": len(rejected),
            "duplicates_detected": duplicates,
        }

        run_dir = create_run_dir(Path(output_dir), filename)
        data = source if isinstance(source, bytes) else Path(source).read_bytes()
        input_copy = archive_input(run_dir, data, filename)
        report_summary = {
            "input_file": filename,
            "processed_at": datetime.now().isoformat(timespec="seconds"),
            **summary,
        }
        paths = write_reports(run_dir, cleaned, rejected, report_summary)
        paths["input_copy"] = input_copy

        logger.info("Run complete: %s", summary)
        return ProcessResult(cleaned, rejected, summary, paths, run_dir)

    except FileLoadError as exc:
        return _fail(str(exc))
    except Exception:  # last-resort guard so callers (CLI/UI) never crash
        logger.exception("Unexpected error while processing %s", filename)
        return ProcessResult(error="An unexpected error occurred while processing the file. See logs/autoflow.log for details.")


def _fail(message: str) -> ProcessResult:
    logger.error(message)
    return ProcessResult(error=message)
