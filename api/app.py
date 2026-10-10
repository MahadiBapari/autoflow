"""FastAPI application: upload an orders file, run the pipeline, browse and download results.

Endpoints (all under /api):
    POST /api/runs                       upload a file and process it
    GET  /api/runs                       list past runs, newest first
    GET  /api/runs/{run_id}              summary plus cleaned and rejected rows
    GET  /api/runs/{run_id}/files/{kind} download a report: cleaned | rejected | summary | input
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from autoflow.config import (
    CLEANED_REPORT_NAME,
    OUTPUT_DIR,
    REJECTED_REPORT_NAME,
    SUMMARY_REPORT_NAME,
)
from autoflow.logging_setup import setup_logging
from autoflow.pipeline import run_pipeline

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,200}$")
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

REPORT_FILES = {
    "cleaned": CLEANED_REPORT_NAME,
    "rejected": REJECTED_REPORT_NAME,
    "summary": SUMMARY_REPORT_NAME,
}


def create_app(output_dir: Path = OUTPUT_DIR) -> FastAPI:
    """Build the app. ``output_dir`` is injectable so tests can use a temp folder."""
    output_dir = Path(output_dir)
    app = FastAPI(title="AutoFlow API", version="0.2.0")

    def run_folder(run_id: str) -> Path:
        # Validate the id before touching the filesystem: it must be a plain folder name.
        if not RUN_ID_PATTERN.match(run_id):
            raise HTTPException(status_code=404, detail="Run not found")
        folder = output_dir / run_id
        if not folder.is_dir() or not (folder / SUMMARY_REPORT_NAME).is_file():
            raise HTTPException(status_code=404, detail="Run not found")
        return folder

    @app.post("/api/runs", status_code=201)
    def create_run(file: UploadFile) -> Dict[str, Any]:
        data = file.file.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File is larger than 10 MB.")
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename was provided.")

        result = run_pipeline(data, filename=file.filename, output_dir=output_dir)
        if not result.ok:
            raise HTTPException(status_code=400, detail=result.error)
        return {"run_id": result.run_dir.name, "summary": result.summary}

    @app.get("/api/runs")
    def list_runs() -> List[Dict[str, Any]]:
        if not output_dir.is_dir():
            return []
        runs = []
        for folder in output_dir.iterdir():
            summary_path = folder / SUMMARY_REPORT_NAME
            if folder.is_dir() and summary_path.is_file():
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                runs.append({"run_id": folder.name, **summary})
        return sorted(runs, key=lambda r: r.get("processed_at", ""), reverse=True)

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> Dict[str, Any]:
        folder = run_folder(run_id)
        summary = json.loads((folder / SUMMARY_REPORT_NAME).read_text(encoding="utf-8"))
        return {
            "run_id": run_id,
            "summary": summary,
            "cleaned": _read_rows(folder / CLEANED_REPORT_NAME),
            "rejected": _read_rows(folder / REJECTED_REPORT_NAME),
        }

    @app.get("/api/runs/{run_id}/files/{kind}")
    def download(run_id: str, kind: str) -> FileResponse:
        folder = run_folder(run_id)
        if kind == "input":
            matches = sorted(folder.glob("input_*"))
            if not matches:
                raise HTTPException(status_code=404, detail="File not found")
            path = matches[0]
        elif kind in REPORT_FILES:
            path = folder / REPORT_FILES[kind]
        else:
            raise HTTPException(status_code=404, detail="File not found")
        if not path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(path, filename=path.name)

    if FRONTEND_DIST.is_dir():
        # Serve the built React app from the same origin. Mounted last so /api routes win.
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    return app


def _read_rows(path: Path) -> List[Dict[str, Optional[str]]]:
    """Read a report back as text rows. Missing optional cells become empty strings."""
    if not path.is_file():
        return []
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return df.to_dict(orient="records")


setup_logging()
app = create_app()
