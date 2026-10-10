import hashlib
import json
from datetime import datetime

import pandas as pd
import pytest

from autoflow.reporter import archive_input, create_run_dir, write_reports

FIXED = datetime(2024, 5, 1, 12, 0, 0)


def test_run_dir_name(tmp_path):
    run_dir = create_run_dir(tmp_path, "my orders.csv", now=FIXED)
    assert run_dir.name == "my_orders_20240501_120000"
    assert run_dir.is_dir()


def test_run_dir_unique_on_collision(tmp_path):
    first = create_run_dir(tmp_path, "orders.csv", now=FIXED)
    second = create_run_dir(tmp_path, "orders.csv", now=FIXED)
    third = create_run_dir(tmp_path, "orders.csv", now=FIXED)
    assert len({first, second, third}) == 3
    assert second.name.endswith("_1") and third.name.endswith("_2")


def test_run_dir_sanitizes_path_parts(tmp_path):
    run_dir = create_run_dir(tmp_path, "../../evil.csv", now=FIXED)
    assert run_dir.parent == tmp_path


def test_write_reports(tmp_path):
    run_dir = create_run_dir(tmp_path, "o.csv")
    cleaned = pd.DataFrame({"order_id": ["1"], "amount": [1.0]})
    rejected = pd.DataFrame({"order_id": ["2"], "rejection_reason": ["missing amount"]})
    summary = {"total_records": 2, "valid_records": 1}
    paths = write_reports(run_dir, cleaned, rejected, summary)
    assert pd.read_csv(paths["cleaned"]).shape == (1, 2)
    assert pd.read_csv(paths["rejected"]).loc[0, "rejection_reason"] == "missing amount"
    assert json.loads(paths["summary"].read_text()) == summary


def test_write_reports_refuses_overwrite(tmp_path):
    run_dir = create_run_dir(tmp_path, "o.csv")
    df = pd.DataFrame({"a": [1]})
    write_reports(run_dir, df, df, {})
    with pytest.raises(FileExistsError):
        write_reports(run_dir, df, df, {})


def test_archive_input_copies_bytes_and_refuses_overwrite(tmp_path):
    run_dir = create_run_dir(tmp_path, "o.csv")
    target = archive_input(run_dir, b"abc", "sub/o.csv")
    assert target.name == "input_o.csv" and target.read_bytes() == b"abc"
    with pytest.raises(FileExistsError):
        archive_input(run_dir, b"xyz", "o.csv")
    assert target.read_bytes() == b"abc"


def test_reporting_leaves_input_untouched(tmp_path, csv_file):
    digest = hashlib.sha256(csv_file.read_bytes()).hexdigest()
    run_dir = create_run_dir(tmp_path / "out", csv_file.name)
    archive_input(run_dir, csv_file.read_bytes(), csv_file.name)
    write_reports(run_dir, pd.DataFrame(), pd.DataFrame(), {})
    assert hashlib.sha256(csv_file.read_bytes()).hexdigest() == digest
