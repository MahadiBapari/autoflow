import hashlib
import json

import pandas as pd

from autoflow import pipeline
from autoflow.pipeline import run_pipeline

EXPECTED = {"total_records": 8, "valid_records": 3, "rejected_records": 5, "duplicates_detected": 1}


def test_end_to_end_csv(tmp_path, csv_file):
    result = run_pipeline(csv_file, output_dir=tmp_path / "out")
    assert result.ok, result.error
    assert result.summary == EXPECTED
    assert set(result.output_paths) == {"cleaned", "rejected", "summary", "input_copy"}
    for path in result.output_paths.values():
        assert path.exists() and path.parent == result.run_dir
    saved = json.loads(result.output_paths["summary"].read_text())
    assert saved["input_file"] == "orders.csv"
    assert {k: saved[k] for k in EXPECTED} == EXPECTED
    assert len(pd.read_csv(result.output_paths["cleaned"])) == 3


def test_end_to_end_xlsx(tmp_path, xlsx_file):
    result = run_pipeline(xlsx_file, output_dir=tmp_path / "out")
    assert result.ok, result.error
    assert result.summary == EXPECTED


def test_end_to_end_bytes(tmp_path, csv_file):
    result = run_pipeline(csv_file.read_bytes(), filename="upload.csv", output_dir=tmp_path / "out")
    assert result.ok
    assert result.output_paths["input_copy"].read_bytes() == csv_file.read_bytes()


def test_input_preserved_and_runs_do_not_overwrite(tmp_path, csv_file):
    digest = hashlib.sha256(csv_file.read_bytes()).hexdigest()
    first = run_pipeline(csv_file, output_dir=tmp_path / "out")
    second = run_pipeline(csv_file, output_dir=tmp_path / "out")
    assert first.run_dir != second.run_dir
    assert first.output_paths["cleaned"].exists() and second.output_paths["cleaned"].exists()
    assert hashlib.sha256(csv_file.read_bytes()).hexdigest() == digest


def test_missing_columns_returns_error(tmp_path):
    path = tmp_path / "o.csv"
    path.write_text("order_id,amount\n1,10\n")
    result = run_pipeline(path, output_dir=tmp_path / "out")
    assert not result.ok
    assert "customer_name" in result.error and "order_date" in result.error
    assert not (tmp_path / "out").exists()


def test_malformed_file_returns_error(tmp_path):
    path = tmp_path / "bad.xlsx"
    path.write_bytes(b"garbage")
    result = run_pipeline(path, output_dir=tmp_path / "out")
    assert not result.ok and "Excel" in result.error
    assert not (tmp_path / "out").exists()


def test_empty_file_returns_error(tmp_path):
    path = tmp_path / "e.csv"
    path.write_text("")
    assert "empty" in run_pipeline(path, output_dir=tmp_path / "out").error


def test_header_only_file(tmp_path):
    path = tmp_path / "h.csv"
    path.write_text("order_id,customer_name,order_date,amount\n")
    result = run_pipeline(path, output_dir=tmp_path / "out")
    assert result.ok
    assert result.summary == {"total_records": 0, "valid_records": 0, "rejected_records": 0, "duplicates_detected": 0}


def test_unexpected_exception_is_caught(tmp_path, csv_file, monkeypatch):
    def boom(_df):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(pipeline, "normalize", boom)
    result = run_pipeline(csv_file, output_dir=tmp_path / "out")
    assert not result.ok
    assert "unexpected error" in result.error
    assert "kaboom" not in result.error


SAMPLE_DIR = pipeline.Path(__file__).resolve().parent.parent / "sample_data"
SAMPLE_EXPECTED = {"total_records": 20, "valid_records": 9, "rejected_records": 11, "duplicates_detected": 3}


def test_sample_files_produce_known_counts(tmp_path):
    for name in ("orders_sample.csv", "orders_sample.xlsx"):
        result = run_pipeline(SAMPLE_DIR / name, output_dir=tmp_path / "out")
        assert result.ok, result.error
        assert result.summary == SAMPLE_EXPECTED, name


def test_cleaned_amounts_written_with_two_decimals(tmp_path):
    result = run_pipeline(SAMPLE_DIR / "orders_sample.csv", output_dir=tmp_path / "out")
    first_row = result.output_paths["cleaned"].read_text().splitlines()[1]
    assert first_row == "ORD-1001,John Smith,2024-03-01,250.00,North"
