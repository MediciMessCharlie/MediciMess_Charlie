"""Run the completed pipeline and generate all Phase 5 artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from analytics.alerts import generate_alerts
from analytics.kpis import (
    calculate_expense_details,
    calculate_kpis,
    calculate_loan_details,
)
from ingestion.pipeline import run_pipeline
from serving import write_serving_artifacts


def generate(input_path: str | Path, output_directory: str | Path):
    ingestion_result = run_pipeline(input_path)
    if ingestion_result.source_errors:
        raise ValueError("Cannot generate artifacts from an unreadable input file")

    transactions = ingestion_result.accepted
    return write_serving_artifacts(
        kpi_records=calculate_kpis(transactions),
        alert_records=generate_alerts(transactions),
        expense_details=calculate_expense_details(transactions),
        loan_details=calculate_loan_details(transactions),
        output_directory=output_directory,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input_path", nargs="?", default="medici_transactions.csv",
        help="Validated-source CSV or JSON file",
    )
    parser.add_argument(
        "--output", default="serving_outputs",
        help="Root directory for generated artifacts",
    )
    arguments = parser.parse_args()
    manifest = generate(arguments.input_path, arguments.output)
    print(f"Generated {len(manifest.all_files)} serving artifacts in {arguments.output}")


if __name__ == "__main__":
    main()
