"""AutoFlow Streamlit interface: upload → run → review → download.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from autoflow.config import REQUIRED_COLUMNS
from autoflow.logging_setup import setup_logging
from autoflow.pipeline import run_pipeline

setup_logging()

st.set_page_config(page_title="AutoFlow", layout="wide")
st.title("AutoFlow — Intelligent Business Process Automation")
st.caption(
    "Upload a CSV or Excel orders file. Required columns: "
    + ", ".join(f"`{c}`" for c in REQUIRED_COLUMNS)
)

uploaded = st.file_uploader("Orders file", type=["csv", "xlsx", "xls"])

if st.button("Run automation", type="primary", disabled=uploaded is None):
    with st.spinner("Processing..."):
        st.session_state["result"] = run_pipeline(uploaded.getvalue(), filename=uploaded.name)
        st.session_state["result_for"] = uploaded.name

result = st.session_state.get("result")

if result is not None:
    if not result.ok:
        st.error(result.error)
    else:
        st.success(f"Processed **{st.session_state['result_for']}**. Reports saved to `{result.run_dir}`.")

        s = result.summary
        cols = st.columns(4)
        cols[0].metric("Total records", s["total_records"])
        cols[1].metric("Valid records", s["valid_records"])
        cols[2].metric("Rejected records", s["rejected_records"])
        cols[3].metric("Duplicates detected", s["duplicates_detected"])

        tab_clean, tab_rejected = st.tabs(
            [f"Cleaned ({s['valid_records']})", f"Rejected ({s['rejected_records']})"]
        )
        with tab_clean:
            st.dataframe(result.cleaned, width="stretch", hide_index=True)
        with tab_rejected:
            st.dataframe(result.rejected, width="stretch", hide_index=True)

        st.subheader("Download reports")
        dl = st.columns(3)
        for col, key, label, mime in [
            (dl[0], "cleaned", "Cleaned records (CSV)", "text/csv"),
            (dl[1], "rejected", "Rejected records (CSV)", "text/csv"),
            (dl[2], "summary", "Summary (JSON)", "application/json"),
        ]:
            path = result.output_paths[key]
            col.download_button(label, data=path.read_bytes(), file_name=path.name, mime=mime, key=f"dl_{key}")
