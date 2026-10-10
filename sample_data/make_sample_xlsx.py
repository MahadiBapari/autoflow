"""Regenerate orders_sample.xlsx from orders_sample.csv (values kept as text)."""

from pathlib import Path

import pandas as pd

here = Path(__file__).resolve().parent
df = pd.read_csv(here / "orders_sample.csv", dtype=str, keep_default_na=False)
df.to_excel(here / "orders_sample.xlsx", index=False, engine="openpyxl")
print(f"Wrote {here / 'orders_sample.xlsx'} ({len(df)} rows)")
