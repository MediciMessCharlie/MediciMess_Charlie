"""
Orchestrates ingestion of transaction files (CSV or JSON) through the
appropriate ingestion module using the shared transaction validator.
"""

from pathlib import Path
from .csv_ingestion import ingest_csv
from .json_ingestion import ingest_json
from validate_transactions import validate_transaction

def run_pipeline(file_path, last_processed_id=None):
    """Run the ingestion pipeline for a single CSV or JSON file."""
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension == ".csv":
        result = ingest_csv(file_path, validator=validate_transaction, last_processed_id=last_processed_id)
    elif extension == ".json":
        result = ingest_json(file_path, validator=validate_transaction, last_processed_id=last_processed_id)
    else:
        raise ValueError(f"Unsupported file type: '{extension}'")

    _print_summary(file_path, result)
    return result

def _print_summary(file_path, result):
    """Print a summary of the pipeline run."""
    print("=== Pipeline Summary ===")
    print(f"Source file:      {file_path}")
    print(f"Total records:    {result.total_records}")
    print(f"Accepted:         {result.accepted_count}")
    print(f"Rejected:         {result.rejected_count}")
    print(f"Skipped:          {result.skipped_by_incremental_filter}")

    duplicate_rows = getattr(result, "duplicate_rows", None)
    if duplicate_rows:
        print(f"Duplicates:       {len(duplicate_rows)}")

    if result.source_errors:
        print("\n--- Source Errors ---")
        for error in result.source_errors:
            print(f"  - {error}")

    if result.rejected:
        print("\n--- Rejected Records (sample) ---")
        sample = result.rejected[:5]
        for rec in sample:
            reasons = "; ".join(rec.reasons)
            print(f"  - record #{rec.record_number}: {reasons}")
        if len(result.rejected) > len(sample):
            print(f"  ... and {len(result.rejected) - len(sample)} more")

    print("=========================")

def run_all():
    """Run the complete ingestion pipeline for CSV and JSON."""
    csv_result = run_pipeline("medici_transactions.csv")
    json_result = run_pipeline("medici_transactions.json")
    return csv_result, json_result

if __name__ == "__main__":
    run_all()

# if __name__ == "__main__":
#     run_pipeline("tests/test_transactions.json")

# if __name__ == "__main__":
#     run_pipeline("medici_transactions.csv")