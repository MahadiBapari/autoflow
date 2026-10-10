from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import MAX_UPLOAD_BYTES, create_app

SAMPLE = Path(__file__).resolve().parent.parent / "sample_data" / "orders_sample.csv"
SAMPLE_COUNTS = {"total_records": 20, "valid_records": 9, "rejected_records": 11, "duplicates_detected": 3}


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "outputs"))


@pytest.fixture
def uploaded(client):
    with SAMPLE.open("rb") as fh:
        resp = client.post("/api/runs", files={"file": ("orders_sample.csv", fh, "text/csv")})
    assert resp.status_code == 201, resp.text
    return resp.json()["run_id"]


def test_upload_creates_run_with_summary(client):
    with SAMPLE.open("rb") as fh:
        resp = client.post("/api/runs", files={"file": ("orders_sample.csv", fh, "text/csv")})
    assert resp.status_code == 201
    body = resp.json()
    assert body["summary"] == SAMPLE_COUNTS
    assert body["run_id"].startswith("orders_sample_")


def test_upload_xlsx(client):
    xlsx = SAMPLE.with_suffix(".xlsx")
    with xlsx.open("rb") as fh:
        resp = client.post("/api/runs", files={"file": ("orders_sample.xlsx", fh, "application/octet-stream")})
    assert resp.status_code == 201
    assert resp.json()["summary"] == SAMPLE_COUNTS


def test_upload_missing_columns_is_400(client):
    resp = client.post("/api/runs", files={"file": ("bad.csv", b"order_id,amount\n1,10\n", "text/csv")})
    assert resp.status_code == 400
    assert "customer_name" in resp.json()["detail"]


def test_upload_unsupported_type_is_400(client):
    resp = client.post("/api/runs", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert resp.status_code == 400
    assert "Unsupported" in resp.json()["detail"]


def test_upload_corrupt_excel_is_400(client):
    resp = client.post("/api/runs", files={"file": ("bad.xlsx", b"not excel", "application/octet-stream")})
    assert resp.status_code == 400


def test_upload_too_large_is_413(client):
    payload = b"a" * (MAX_UPLOAD_BYTES + 1)
    resp = client.post("/api/runs", files={"file": ("big.csv", payload, "text/csv")})
    assert resp.status_code == 413


def test_list_runs_empty_then_populated(client, uploaded):
    runs = client.get("/api/runs").json()
    assert [r["run_id"] for r in runs] == [uploaded]
    assert runs[0]["valid_records"] == 9


def test_list_runs_when_no_outputs_folder(client):
    assert client.get("/api/runs").json() == []


def test_get_run_returns_rows(client, uploaded):
    body = client.get(f"/api/runs/{uploaded}").json()
    assert body["summary"]["valid_records"] == 9
    assert len(body["cleaned"]) == 9
    assert len(body["rejected"]) == 11
    first = body["cleaned"][0]
    assert first == {
        "order_id": "ORD-1001",
        "customer_name": "John Smith",
        "order_date": "2024-03-01",
        "amount": "250.00",
        "region": "North",
    }
    assert body["rejected"][0]["rejection_reason"] == "duplicate order_id"


def test_get_unknown_run_is_404(client):
    assert client.get("/api/runs/does_not_exist").status_code == 404


@pytest.mark.parametrize("bad_id", ["..", "..%2Fetc", "a.b", "x%20y"])
def test_run_id_traversal_rejected(client, bad_id):
    assert client.get(f"/api/runs/{bad_id}").status_code == 404
    assert client.get(f"/api/runs/{bad_id}/files/summary").status_code == 404


def test_download_each_report(client, uploaded):
    for kind in ("cleaned", "rejected", "summary"):
        resp = client.get(f"/api/runs/{uploaded}/files/{kind}")
        assert resp.status_code == 200, kind
        assert resp.content


def test_download_input_copy_matches_upload(client, uploaded):
    resp = client.get(f"/api/runs/{uploaded}/files/input")
    assert resp.status_code == 200
    assert resp.content == SAMPLE.read_bytes()


def test_download_unknown_kind_is_404(client, uploaded):
    assert client.get(f"/api/runs/{uploaded}/files/secrets").status_code == 404


def test_second_upload_does_not_overwrite_first(client, uploaded):
    with SAMPLE.open("rb") as fh:
        second = client.post("/api/runs", files={"file": ("orders_sample.csv", fh, "text/csv")}).json()["run_id"]
    assert second != uploaded
    assert client.get(f"/api/runs/{uploaded}").status_code == 200
