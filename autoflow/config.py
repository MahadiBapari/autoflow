"""Central configuration constants for AutoFlow."""

from pathlib import Path

REQUIRED_COLUMNS = ["order_id", "customer_name", "order_date", "amount"]

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"
LOG_DIR = PROJECT_ROOT / "logs"

# Normalized output date format (ISO 8601).
OUTPUT_DATE_FORMAT = "%Y-%m-%d"

CLEANED_REPORT_NAME = "cleaned_orders.csv"
REJECTED_REPORT_NAME = "rejected_orders.csv"
SUMMARY_REPORT_NAME = "summary.json"
