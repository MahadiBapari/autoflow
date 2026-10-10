import pandas as pd
import pytest

from autoflow.validator import (
    REASON_COLUMN,
    SOURCE_ROW_COLUMN,
    check_required_columns,
    parse_amounts,
    parse_dates,
    validate_rows,
)


def make(rows):
    return pd.DataFrame(rows, columns=["order_id", "customer_name", "order_date", "amount"], dtype=str)


def reasons_by_id(rejected):
    return dict(zip(rejected["order_id"], rejected[REASON_COLUMN]))


def test_check_required_columns():
    assert check_required_columns(make([])) == []
    df = pd.DataFrame(columns=["order_id", "amount"])
    assert check_required_columns(df) == ["customer_name", "order_date"]


def test_validate_rows_raises_on_missing_columns():
    with pytest.raises(ValueError, match="customer_name"):
        validate_rows(pd.DataFrame({"order_id": ["1"], "order_date": ["2024-01-01"], "amount": ["1"]}))


def test_fixture_counts(raw_orders):
    valid, rejected, dups = validate_rows(raw_orders)
    assert len(valid) == 3
    assert len(rejected) == 5
    assert dups == 1
    assert list(valid["order_id"]) == ["ORD-001", "ORD-002", "ORD-003"]


def test_fixture_reasons(raw_orders):
    _, rejected, _ = validate_rows(raw_orders)
    assert list(rejected["order_id"]) == ["ORD-002", "ORD-004", "ORD-005", "ORD-006", "ORD-007"]
    assert list(rejected[REASON_COLUMN]) == [
        "duplicate order_id",
        "missing customer_name",
        "invalid order_date",
        "invalid amount",
        "negative amount",
    ]


def test_source_row_points_to_file_row(raw_orders):
    _, rejected, _ = validate_rows(raw_orders)
    # header is row 1, so the 4th data row (index 3) is spreadsheet row 5
    assert rejected.loc[0, SOURCE_ROW_COLUMN] == 5


def test_rejected_keeps_original_values(raw_orders):
    _, rejected, _ = validate_rows(raw_orders)
    assert rejected.loc[3, "amount"] == "abc"


def test_whitespace_only_counts_as_missing():
    _, rejected, _ = validate_rows(make([["   ", "A", "2024-01-01", "1"]]))
    assert rejected.loc[0, REASON_COLUMN] == "missing order_id"


def test_nan_counts_as_missing():
    df = make([["1", None, "2024-01-01", "1"]])
    _, rejected, _ = validate_rows(df)
    assert rejected.loc[0, REASON_COLUMN] == "missing customer_name"


def test_multiple_reasons_on_one_row():
    _, rejected, _ = validate_rows(make([["1", "", "31/31/2024", "xyz"]]))
    assert rejected.loc[0, REASON_COLUMN] == "missing customer_name; invalid order_date; invalid amount"


def test_duplicates_first_kept_and_all_repeats_counted():
    df = make([
        ["A", "x", "2024-01-01", "1"],
        ["A", "y", "2024-01-02", "2"],
        ["A", "z", "2024-01-03", "3"],
        ["B", "w", "2024-01-04", "4"],
    ])
    valid, rejected, dups = validate_rows(df)
    assert dups == 2
    assert list(valid["customer_name"]) == ["x", "w"]
    assert set(rejected[REASON_COLUMN]) == {"duplicate order_id"}


def test_duplicate_detection_ignores_surrounding_whitespace():
    _, _, dups = validate_rows(make([["A", "x", "2024-01-01", "1"], [" A ", "y", "2024-01-01", "1"]]))
    assert dups == 1


def test_blank_ids_are_not_counted_as_duplicates():
    _, rejected, dups = validate_rows(make([["", "x", "2024-01-01", "1"], ["", "y", "2024-01-01", "1"]]))
    assert dups == 0
    assert set(rejected[REASON_COLUMN]) == {"missing order_id"}


def test_zero_amount_is_valid():
    valid, _, _ = validate_rows(make([["1", "A", "2024-01-01", "0"]]))
    assert len(valid) == 1


def test_parse_amounts():
    result = parse_amounts(pd.Series(["$1,234.50", " 10 ", "abc", "inf", "nan", "-3"]))
    assert result[0] == 1234.5
    assert result[1] == 10
    assert result[[2, 3, 4]].isna().all()
    assert result[5] == -3


def test_parse_dates_mixed_formats():
    result = parse_dates(pd.Series(["2024-01-15", "01/20/2024", "15 Mar 2024", "nope", "2024-02-30"]))
    assert result[0] == pd.Timestamp("2024-01-15")
    assert result[1] == pd.Timestamp("2024-01-20")
    assert result[2] == pd.Timestamp("2024-03-15")
    assert pd.isna(result[3])
    assert pd.isna(result[4])


def test_empty_dataframe():
    valid, rejected, dups = validate_rows(make([]))
    assert valid.empty and rejected.empty and dups == 0
