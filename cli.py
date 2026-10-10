"""Command-line entry point: python cli.py <orders.csv|orders.xlsx> [--output-dir DIR]"""

from __future__ import annotations

import argparse
import sys

from autoflow.config import OUTPUT_DIR
from autoflow.logging_setup import setup_logging
from autoflow.pipeline import run_pipeline


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="AutoFlow: validate and clean a business orders file.")
    parser.add_argument("input_file", help="Path to a .csv or .xlsx orders file")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Base folder for run outputs")
    args = parser.parse_args(argv)

    setup_logging()
    result = run_pipeline(args.input_file, output_dir=args.output_dir)
    if not result.ok:
        print(f"ERROR: {result.error}", file=sys.stderr)
        return 1

    print("\nSummary")
    for key, value in result.summary.items():
        print(f"  {key.replace('_', ' ').title():<22} {value}")
    print(f"\nReports written to: {result.run_dir}")
    for name, path in result.output_paths.items():
        print(f"  {name:<11} {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
