"""Smoke tests for the Streamlit UI using Streamlit's AppTest harness.

AppTest cannot drive st.file_uploader, so results are injected via session
state from a real pipeline run; the upload→button wiring is checked manually.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from autoflow.pipeline import ProcessResult, run_pipeline

APP = str(Path(__file__).resolve().parent.parent / "app.py")
SAMPLE = Path(__file__).resolve().parent.parent / "sample_data" / "orders_sample.csv"


def test_initial_render_has_disabled_run_button():
    at = AppTest.from_file(APP).run()
    assert not at.exception
    assert at.button[0].label == "Run automation"
    assert at.button[0].disabled
    assert len(at.metric) == 0


def test_results_view(tmp_path):
    at = AppTest.from_file(APP)
    at.session_state["result"] = run_pipeline(SAMPLE, output_dir=tmp_path)
    at.session_state["result_for"] = SAMPLE.name
    at.run()
    assert not at.exception
    metrics = {m.label: m.value for m in at.metric}
    assert metrics == {
        "Total records": "20",
        "Valid records": "9",
        "Rejected records": "11",
        "Duplicates detected": "3",
    }
    assert len(at.dataframe) == 2
    assert len(at.get("download_button")) == 3


def test_error_view():
    at = AppTest.from_file(APP)
    at.session_state["result"] = ProcessResult(error="Missing required columns: amount.")
    at.session_state["result_for"] = "x.csv"
    at.run()
    assert not at.exception
    assert at.error[0].value == "Missing required columns: amount."
    assert len(at.metric) == 0
