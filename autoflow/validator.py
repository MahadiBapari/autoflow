"""Validation rules for order records.

Every row is checked against all rules and receives a ``rejection_reason``
listing each problem found (joined with "; "). Rows with no problems are valid.
"""

from __future__ import annotations

import logging
from typing import List, Tuple

import numpy as np
import pandas as pd

from autoflow.config import REQUIRED_COLUMNS

logger = logging.getLogger(__name__)

REASON_COLUMN = "rejection_reason"
SOURCE_ROW_COLUMN = "source_row"
DUPLICATE_REASON = "duplicate order_id"


def check_required_columns(df: pd.DataFrame) -> List[str]:
    """Return the required columns missing from ``df`` (empty list if none)."""
    return [col for col in REQUIRED_COLUMNS if col not in df.columns]


def parse_dates(values: pd.Series) -> pd.Series:
    """Parse date strings in mixed formats; unparseable values become NaT."""
    return pd.to_datetime(values.astype(str).str.strip(), errors="coerce", format="mixed")


def parse_amounts(values: pd.Series) -> pd.Series:
    """Parse amounts, tolerating a currency symbol and thousands separators.

    Unparseable or non-finite values become NaN.
    """
    cleaned = values.astype(str).str.strip().str.replace(r"^\$", "", regex=True).str.replace(",", "", regex=False)
    numbers = pd.to_numeric(cleaned, errors="coerce")
    return numbers.where(np.isfinite(numbers))


def validate_rows(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, int]:
    """Split ``df`` into valid and rejected rows.

    Returns:
        (valid_df, rejected_df, duplicates_detected). ``rejected_df`` keeps the
        original values plus ``source_row`` (1-based spreadsheet row, header = 1)
        and ``rejection_reason``. ``duplicates_detected`` counts repeat
        occurrences of an order_id; the first occurrence is not counted.
    """
    missing = check_required_columns(df)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    df = df.reset_index(drop=True)
    reasons: List[List[str]] = [[] for _ in range(len(df))]

    def flag(mask: pd.Series, reason: str) -> None:
        for i in np.flatnonzero(mask.to_numpy()):
            reasons[i].append(reason)

    stripped = {col: df[col].fillna("").astype(str).str.strip() for col in REQUIRED_COLUMNS}
    blank = {col: stripped[col] == "" for col in REQUIRED_COLUMNS}

    for col in REQUIRED_COLUMNS:
        flag(blank[col], f"missing {col}")

    flag(~blank["order_date"] & parse_dates(stripped["order_date"]).isna(), "invalid order_date")

    amounts = parse_amounts(stripped["amount"])
    flag(~blank["amount"] & amounts.isna(), "invalid amount")
    flag(amounts < 0, "negative amount")

    duplicate_mask = ~blank["order_id"] & stripped["order_id"].duplicated(keep="first")
    flag(duplicate_mask, DUPLICATE_REASON)
    duplicates_detected = int(duplicate_mask.sum())

    reason_series = pd.Series(["; ".join(r) for r in reasons], index=df.index)
    is_valid = reason_series == ""

    valid_df = df[is_valid].reset_index(drop=True)
    rejected_df = df[~is_valid].copy()
    rejected_df.insert(0, SOURCE_ROW_COLUMN, rejected_df.index + 2)
    rejected_df[REASON_COLUMN] = reason_series[~is_valid]
    rejected_df = rejected_df.reset_index(drop=True)

    logger.info(
        "Validation: %d valid, %d rejected, %d duplicates",
        len(valid_df), len(rejected_df), duplicates_detected,
    )
    return valid_df, rejected_df, duplicates_detected
