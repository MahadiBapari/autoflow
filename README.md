# AutoFlow — Intelligent Business Process Automation

AutoFlow is an RPA-style tool that takes a CSV or Excel file of business orders and:

1. validates it (required columns, missing or invalid values, duplicate order IDs),
2. normalizes the valid records,
3. writes a **cleaned** report, a **rejected** report (with the reason for each rejection), and a summary,
4. shows the results in a web app where you can review and download each report.

**Stack:** Python, pandas, openpyxl, FastAPI, React 18, TypeScript, Vite, `logging`, pytest, Vitest. A Streamlit version is kept as an alternative UI. There is no database, no authentication, and no cloud service.

## Project structure

```
autoflow/
├── autoflow/               # core package (no UI code)
│   ├── config.py           # required columns, allowed extensions, output/log paths
│   ├── loader.py           # read CSV/XLSX from a path or bytes; FileLoadError on bad input
│   ├── validator.py        # required-column check + per-row validation rules
│   ├── normalizer.py       # clean up valid rows (names, dates, amounts)
│   ├── reporter.py         # unique run folder, report files, archived input copy
│   ├── pipeline.py         # run_pipeline(): load → validate → normalize → report
│   └── logging_setup.py    # console + logs/autoflow.log
├── api/
│   └── app.py              # FastAPI: upload, run history, results, downloads
├── frontend/               # React + TypeScript app (Vite)
│   └── src/
│       ├── App.tsx         # page state and layout
│       ├── api.ts          # the only module that calls the API
│       ├── components/     # UploadForm, SummaryCards, RecordsTable, RunHistory
│       └── *.test.tsx      # Vitest + React Testing Library
├── app.py                  # original Streamlit UI (optional)
├── cli.py                  # command-line entry point
├── sample_data/            # example orders file (CSV + XLSX) with deliberate errors
├── tests/                  # pytest suite (core + API)
└── requirements.txt
```

## Setup

Requires Python 3.9+ and Node.js 18+.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd frontend
npm install
cd ..
```

## Running the web app

**Development** (hot reload), in two terminals:

```bash
# terminal 1: API on :8000
.venv/bin/uvicorn api.app:app --reload --port 8000

# terminal 2: React on :5173 (open this one; it proxies /api to :8000)
cd frontend && npm run dev
```

**Production-style** (one server): build the frontend once, then start the API. FastAPI serves the built app too.

```bash
cd frontend && npm run build && cd ..
.venv/bin/uvicorn api.app:app --port 8000     # open http://127.0.0.1:8000
```

In the app, upload a `.csv` or `.xlsx` file and click **Run automation**. You'll see the summary, the cleaned and rejected tables, and download links. Past runs stay in the **History** list.

### API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/runs` | Upload a file (multipart field `file`, max 10 MB); returns `run_id` and `summary` (201). Bad input returns 400 with `detail`. |
| `GET` | `/api/runs` | List past runs, newest first |
| `GET` | `/api/runs/{run_id}` | Summary plus `cleaned` and `rejected` rows |
| `GET` | `/api/runs/{run_id}/files/{kind}` | Download `cleaned`, `rejected`, `summary`, or `input` (the original upload) |

FastAPI also serves interactive docs at http://127.0.0.1:8000/docs.

### Streamlit UI (optional)

```bash
streamlit run app.py
```

### Command line

```bash
python cli.py sample_data/orders_sample.csv
python cli.py sample_data/orders_sample.xlsx --output-dir my_outputs
```

The exit code is `0` on success and `1` if the file couldn't be processed. The error message goes to stderr.

## Input format

The file must contain these columns. Header case and surrounding spaces are ignored.

| column          | rule                                                                          |
|-----------------|-------------------------------------------------------------------------------|
| `order_id`      | required; must be unique (see duplicates below)                               |
| `customer_name` | required                                                                      |
| `order_date`    | required; must parse as a date (`2024-03-01`, `03/01/2024`, `1 Mar 2024`, …)  |
| `amount`        | required; numeric and ≥ 0. A leading `$` and thousands commas are accepted    |

Extra columns are allowed and are passed through unchanged.

### Validation behaviour

- A row is rejected if it breaks **any** rule. Every problem on the row is listed in `rejection_reason`, separated by `; ` (for example `invalid order_date; invalid amount`).
- **Duplicates:** the first occurrence of an `order_id` is kept, and every later occurrence is rejected as `duplicate order_id`. "Duplicates detected" counts those later occurrences.
- Slash dates are read month-first (`03/05/2024` = 5 March 2024).
- If a **required column is missing**, the whole file is refused with a clear message, instead of every row being rejected.
- Empty, corrupt, or unsupported files are reported as errors, and no output folder is created.

### Normalization (valid rows only)

- Whitespace is trimmed everywhere, and repeated spaces in names are collapsed.
- Names typed in all-lowercase or all-uppercase are title-cased. Mixed-case names such as `McDonald` are left as typed.
- `order_date` is written as `YYYY-MM-DD`.
- `amount` is rounded to 2 decimals.

## Outputs

Each run creates a new folder, so earlier results are never overwritten:

```
outputs/<input-name>_<YYYYmmdd_HHMMSS>/
├── cleaned_orders.csv      # normalized valid records
├── rejected_orders.csv     # original values + source_row + rejection_reason
├── summary.json            # input name, timestamp, counts
└── input_<original-name>   # byte-for-byte copy of the input file
```

If two runs start in the same second, the second folder gets a `_1` suffix, the next `_2`, and so on. The original input file is only read, never modified. `source_row` is the row number in the spreadsheet (the header is row 1).

Logs are written to the console and to `logs/autoflow.log`.

## Testing

```bash
python -m pytest -v                 # Python: core logic, API, Streamlit smoke tests
cd frontend && npm test             # React: API client, components, App flow
cd frontend && npm run build        # type-checks and builds the production bundle
```

The Python suite covers the loader (CSV/XLSX, encodings, empty/corrupt/unsupported files), every validation rule, normalization, the no-overwrite guarantees, end-to-end pipeline runs including error paths, the API (uploads, errors, size limit, run-ID path traversal, downloads), and Streamlit smoke tests. The frontend suite covers the API client, the components, and the upload → results → tab flow.

The sample file `sample_data/orders_sample.csv` has 20 records: **9 valid, 11 rejected, 3 duplicates**. A test checks these counts for both the CSV and the XLSX version. To regenerate the XLSX after editing the CSV, run `python sample_data/make_sample_xlsx.py`.
