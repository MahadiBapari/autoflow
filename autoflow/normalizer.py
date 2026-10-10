"""Normalize validated order records into a consistent, clean format."""

from __future__ import annotations

import logging

import pandas as pd

from autoflow.config import OUTPUT_DATE_FORMAT
from autoflow.validator import parse_amounts, parse_dates

logger = logging.getLogger(__name__)


def _normalize_name(name: str) -> str:
    """Collapse whitespace; fix casing only when the name is all-lower or all-upper.

    Mixed-case names (e.g. "McDonald") are left as typed.
    """
    name = " ".join(str(name).split())
    if name.islower() or name.isupper():
        name = name.title()
    return name


def normalize(valid_df: pd.DataFrame) -> pd.DataFrame:
    """Return a normalized copy of rows that already passed validation.

    - ``order_id``: trimmed string
    - ``customer_name``: whitespace collapsed, casing fixed for all-lower/upper
    - ``order_date``: ISO ``YYYY-MM-DD`` string
    - ``amount``: float rounded to 2 decimals
    - other columns: trimmed strings, otherwise untouched
    """
    df = valid_df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].fillna("").astype(str).str.strip()

    if df.empty:
        return df

    df["customer_name"] = df["customer_name"].map(_normalize_name)
    df["order_date"] = parse_dates(df["order_date"]).dt.strftime(OUTPUT_DATE_FORMAT)
    df["amount"] = parse_amounts(df["amount"]).round(2)

    logger.info("Normalized %d rows", len(df))
    return df
