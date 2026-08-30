"""
CSV ingestion for MediciMess transaction records.

Reads CSV transaction files, normalizes records into a common dictionary
structure, and passes each record to the shared transaction validator.

This module is responsible for:
- Reading CSV files
- Verifying required columns
- Converting values to the team's common transaction structure
- Passing normalized transactions to the shared validator
- Tracking accepted, rejected, duplicate, and skipped records

Business validation rules belong in validate_transactions.py.
"""

import csv
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

NormalizedTransaction = dict[str, Any]
Validator = Callable[[NormalizedTransaction], tuple[bool, list[str]]]

REQUIRED_COLUMNS = {
    "id", "date", "branch", "type", "counterparty", "description",
    "debit_account", "debit_amount", "credit_account", "credit_amount", "currency"
}

OPTIONAL_COLUMNS = {"credit_account_2", "credit_amount_2"}

@dataclass(frozen=True)
class RejectedRecord:
    record_number: int
    raw_record: Any
    reasons: tuple[str, ...]

@dataclass
class IngestionResult:
    accepted: list[NormalizedTransaction] = field(default_factory=list)
    rejected: list[RejectedRecord] = field(default_factory=list)
    source_errors: list[str] = field(default_factory=list)
    duplicate_rows: list[tuple[int, int]] = field(default_factory=list)
    total_records: int = 0
    skipped_by_incremental_filter: int = 0

    @property
    def accepted_count(self) -> int:
        return len(self.accepted)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)

def required_value(row: dict, field_name: str):
    """Return a required value or raise an error."""
    value = row.get(field_name)
    if value is None or str(value).strip() == "":
        raise ValueError(f"required field is empty: {field_name}")
    return value

def required_text(row: dict, field_name: str) -> str:
    """Return a required text value."""
    return str(required_value(row, field_name)).strip()

def to_int(value: Any, field_name: str) -> int:
    """Convert a value to an integer."""
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc

def to_date(value: Any) -> date:
    """Convert a value to an ISO date."""
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise ValueError("date must use YYYY-MM-DD format") from exc

def to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert a value to Decimal."""
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric")
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not amount.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return amount

def optional_text(value: Any) -> str | None:
    """Normalize an optional text value."""
    if value is None:
        return None
    value = str(value).strip()
    return value or None

def optional_decimal(value: Any, field_name: str) -> Decimal | None:
    """Normalize an optional decimal value."""
    if value is None or str(value).strip() == "":
        return None
    return to_decimal(value, field_name)

def normalize_csv_row(row: dict) -> NormalizedTransaction:
    """Convert one CSV row into the common MediciMess transaction dictionary."""
    return {
        "id": to_int(required_value(row, "id"), "id"),
        "date": to_date(required_value(row, "date")),
        "branch": required_text(row, "branch"),
        "type": required_text(row, "type"),
        "counterparty": required_text(row, "counterparty"),
        "description": required_text(row, "description"),
        "debit_account": required_text(row, "debit_account"),
        "debit_amount": to_decimal(required_value(row, "debit_amount"), "debit_amount"),
        "credit_account": required_text(row, "credit_account"),
        "credit_amount": to_decimal(required_value(row, "credit_amount"), "credit_amount"),
        "credit_account_2": optional_text(row.get("credit_account_2")),
        "credit_amount_2": optional_decimal(row.get("credit_amount_2"), "credit_amount_2"),
        "currency": required_text(row, "currency"),
    }

def ingest_csv(file_path: str | Path, validator: Validator, last_processed_id: int | None = None) -> IngestionResult:
    """Read, normalize, and validate CSV transactions."""
    result = IngestionResult()
    path = Path(file_path)

    try:
        source = path.open("r", encoding="utf-8-sig", newline="")
    except FileNotFoundError:
        result.source_errors.append(f"CSV file not found: {path}")
        return result
    except PermissionError:
        result.source_errors.append(f"CSV file is not readable: {path}")
        return result
    except OSError as exc:
        result.source_errors.append(f"Could not read CSV file {path}: {exc}")
        return result

    with source:
        reader = csv.DictReader(source, strict=True)

        if reader.fieldnames is None:
            result.source_errors.append("CSV file has no header")
            return result

        headers = {name.strip() for name in reader.fieldnames if name}
        missing_columns = sorted(REQUIRED_COLUMNS - headers)

        if missing_columns:
            result.source_errors.append("Missing required CSV columns: " + ", ".join(missing_columns))
            return result

        seen_transactions = {}

        try:
            for record_number, row in enumerate(reader, start=2):
                result.total_records += 1

                try:
                    transaction = normalize_csv_row(row)
                except (TypeError, ValueError) as exc:
                    result.rejected.append(RejectedRecord(record_number, row, (str(exc),)))
                    continue

                if last_processed_id is not None and transaction["id"] <= last_processed_id:
                    result.skipped_by_incremental_filter += 1
                    continue

                try:
                    is_valid, reasons = validator(transaction)
                except Exception as exc:
                    result.rejected.append(RejectedRecord(record_number, row, (f"validator error: {exc}",)))
                    continue

                if not is_valid:
                    result.rejected.append(RejectedRecord(record_number, row, tuple(reasons) or ("record failed shared validation",)))
                    continue

                duplicate_key = (
                    transaction["date"],
                    transaction["branch"],
                    transaction["type"],
                    transaction["counterparty"],
                    transaction["debit_amount"],
                    transaction["credit_account"],
                )

                original_row = seen_transactions.get(duplicate_key)

                if original_row is not None:
                    result.duplicate_rows.append((original_row, record_number))
                else:
                    seen_transactions[duplicate_key] = record_number

                result.accepted.append(transaction)

        except csv.Error as exc:
            result.source_errors.append(f"Malformed CSV: {exc}")

    return result