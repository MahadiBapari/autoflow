import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def raw_orders() -> pd.DataFrame:
    """Raw string-typed orders as the loader would produce them.

    Expected outcome: rows 1, 2, 3 valid; ORD-002 second occurrence is a
    duplicate; one blank name; one bad date; one bad amount; one negative amount.
    """
    return pd.DataFrame(
        {
            "order_id": ["ORD-001", "ORD-002", "ORD-003", "ORD-002", "ORD-004", "ORD-005", "ORD-006", "ORD-007"],
            "customer_name": ["  alice   smith ", "Bob Jones", "Carol King", "Bob Jones", "", "Eve Adams", "Frank Li", "Grace Ho"],
            "order_date": ["2024-01-15", "01/20/2024", "2024-02-01", "2024-01-20", "2024-02-05", "not-a-date", "2024-02-10", "2024-02-11"],
            "amount": ["100.5", "$1,250.00", "0", "1250", "75", "60", "abc", "-5"],
        },
        dtype=str,
    )


@pytest.fixture
def csv_file(tmp_path, raw_orders) -> Path:
    path = tmp_path / "orders.csv"
    raw_orders.to_csv(path, index=False)
    return path


@pytest.fixture
def xlsx_file(tmp_path, raw_orders) -> Path:
    path = tmp_path / "orders.xlsx"
    raw_orders.to_excel(path, index=False, engine="openpyxl")
    return path
