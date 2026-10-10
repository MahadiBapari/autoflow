# CLAUDE.md

AutoFlow validates, cleans, and reports on CSV/Excel business-order files. It has a React frontend, a FastAPI backend, a CLI, and the original Streamlit UI.

## Commands

```bash
.venv/bin/python -m pytest -q -W error             # Python suite (core + API); must stay warning-free
.venv/bin/python cli.py sample_data/orders_sample.csv
.venv/bin/uvicorn api.app:app --port 8000          # API; also serves frontend/dist if it has been built
cd frontend && npm run dev                         # React dev server on :5173, proxies /api to :8000
cd frontend && npm test && npm run build           # frontend tests (vitest) and production build
.venv/bin/streamlit run app.py                     # legacy Streamlit UI (optional)
.venv/bin/python sample_data/make_sample_xlsx.py   # regenerate the XLSX after editing the sample CSV
```

The venv runs **Python 3.9**. Use `from __future__ import annotations` and `typing.Optional`/`Union`/`List`. Don't use `match` or `X | Y` in runtime-evaluated positions.

## Architecture

The pipeline runs `load → validate → normalize → report` and is orchestrated by `autoflow/pipeline.py::run_pipeline`.

- `loader.py` reads every value with `dtype=str, keep_default_na=False`, so validation sees the raw text. Any malformed input raises `FileLoadError`.
- `validator.py` owns `parse_dates` / `parse_amounts`. `normalizer.py` reuses them, so put parsing changes there and nowhere else.
- `reporter.py` gives each run a new `outputs/<stem>_<timestamp>[_N]/` folder (`mkdir(exist_ok=False)`). It writes the input copy in `"xb"` mode and refuses to overwrite existing reports.
- `run_pipeline` never raises. Errors come back in `ProcessResult.error`. No output folder is created when the input can't be processed.
- `api/app.py` (FastAPI) is a thin layer over `run_pipeline`. `create_app(output_dir)` takes the output folder as a parameter so tests can use temp dirs. Run IDs are validated against a strict regex and must be existing folders, which prevents path traversal. Uploads are capped at 10 MB.
- `frontend/` is Vite + React 18 + TypeScript. `src/api.ts` is the only place that calls `fetch`. Components are presentational; `App.tsx` owns state.
- `app.py` (Streamlit) and `cli.py` are thin. Business logic goes in the `autoflow/` package, never in the UI or the API.

## Invariants (covered by tests, don't break them)

- The original input file is never modified, and earlier outputs are never overwritten.
- Duplicate `order_id`: the first occurrence is kept and later ones are rejected. `duplicates_detected` counts only the later ones.
- `rejection_reason` lists every problem on a row, joined by `"; "`. `source_row` is the spreadsheet row number (header = 1).
- If a required column is missing, the whole file is refused with an error instead of every row being rejected.
- The sample data yields **20 total / 9 valid / 11 rejected / 3 duplicates**. If you edit the sample, update `tests/test_pipeline.py` and the README.

## Scope

No auth, no database, no cloud services. The app is file-based: results live in `outputs/` and history is read from those folders. Don't add a database without asking.

## Testing notes

- `tests/test_api.py` uses FastAPI's `TestClient` against a temp output folder.
- Frontend tests use Vitest + React Testing Library with jsdom. `src/test/setup.ts` runs RTL cleanup manually because Vitest globals are off.
- Streamlit UI tests use `streamlit.testing.v1.AppTest` and inject results through `session_state`, since `AppTest` can't drive a file uploader.
- For a real-browser check, use the `playwright-core` package with the cached Chromium or Chrome, as described in the memory notes. The `browser-automation` skill does not work on this machine.
