import pandas as pd

from autoflow.normalizer import normalize
from autoflow.validator import validate_rows


def test_normalize_fixture(raw_orders):
    valid, _, _ = validate_rows(raw_orders)
    out = normalize(valid)
    assert list(out["order_id"]) == ["ORD-001", "ORD-002", "ORD-003"]
    assert list(out["customer_name"]) == ["Alice Smith", "Bob Jones", "Carol King"]
    assert list(out["order_date"]) == ["2024-01-15", "2024-01-20", "2024-02-01"]
    assert list(out["amount"]) == [100.5, 1250.0, 0.0]


def test_amount_rounding():
    df = pd.DataFrame({"order_id": ["1"], "customer_name": ["A"], "order_date": ["2024-01-01"], "amount": ["10.4567"]})
    assert normalize(df).loc[0, "amount"] == 10.46


def test_name_casing_rules():
    df = pd.DataFrame({
        "order_id": ["1", "2", "3"],
        "customer_name": ["JOHN DOE", "mary-jane o'neil", "Ronald McDonald"],
        "order_date": ["2024-01-01"] * 3,
        "amount": ["1"] * 3,
    })
    assert list(normalize(df)["customer_name"]) == ["John Doe", "Mary-Jane O'Neil", "Ronald McDonald"]


def test_extra_columns_preserved():
    df = pd.DataFrame({
        "order_id": [" 1 "], "customer_name": ["A"], "order_date": ["2024-01-01"],
        "amount": ["1"], "region": ["  North "],
    })
    out = normalize(df)
    assert list(out.columns) == ["order_id", "customer_name", "order_date", "amount", "region"]
    assert out.loc[0, "region"] == "North"
    assert out.loc[0, "order_id"] == "1"


def test_input_not_mutated(raw_orders):
    valid, _, _ = validate_rows(raw_orders)
    snapshot = valid.copy()
    normalize(valid)
    pd.testing.assert_frame_equal(valid, snapshot)


def test_empty_input():
    df = pd.DataFrame(columns=["order_id", "customer_name", "order_date", "amount"], dtype=str)
    assert normalize(df).empty
