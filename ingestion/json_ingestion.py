"""
JSON ingestion for MediciMess transaction records.

Reads JSON transaction files, normalizes records into a common dictionary
structure, and passes each record to the shared transaction validator.

This module is responsible for:
- Reading JSON files
- Verifying required fields
- Converting values to the team's common transaction structure
- Passing normalized transactions to the shared validator
- Tracking accepted, rejected, duplicate, and skipped records

"""

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

NormalizedTransaction = dict[str, Any]
Validator = Callable[[NormalizedTransaction], tuple[bool, list[str]]]

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
    total_records: int = 0
    skipped_by_incremental_filter: int = 0

    @property
    def accepted_count(self) -> int:
        return len(self.accepted)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)

def required_value(record: dict, field_name: str):
    """Return a required value or raise an error."""
    value = record.get(field_name)
    if value is None or str(value).strip() == "":
        raise ValueError(f"required field is empty: {field_name}")
    return value

def required_text(record: dict, field_name: str) -> str:
    """Return a required text value."""
    return str(required_value(record, field_name)).strip()

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

def normalize_json_record(record: dict) -> NormalizedTransaction:
    """Convert one JSON object into the common MediciMess transaction dictionary."""
    return {
        "id": to_int(required_value(record, "id"), "id"),
        "date": to_date(required_value(record, "date")),
        "branch": required_text(record, "branch"),
        "type": required_text(record, "type"),
        "counterparty": required_text(record, "counterparty"),
        "description": required_text(record, "description"),
        "debit_account": required_text(record, "debit_account"),
        "debit_amount": to_decimal(required_value(record, "debit_amount"), "debit_amount"),
        "credit_account": required_text(record, "credit_account"),
        "credit_amount": to_decimal(required_value(record, "credit_amount"), "credit_amount"),
        "credit_account_2": optional_text(record.get("credit_account_2")),
        "credit_amount_2": optional_decimal(record.get("credit_amount_2"), "credit_amount_2"),
        "currency": required_text(record, "currency"),
    }

def ingest_json(file_path: str | Path, validator: Validator, last_processed_id: int | None = None) -> IngestionResult:
    """Read, normalize, and validate JSON transactions."""
    result = IngestionResult()
    path = Path(file_path)

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        result.source_errors.append(f"JSON file not found: {path}")
        return result
    except PermissionError:
        result.source_errors.append(f"JSON file is not readable: {path}")
        return result
    except json.JSONDecodeError as exc:
        result.source_errors.append(f"Malformed JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return result
    except OSError as exc:
        result.source_errors.append(f"Could not read JSON file {path}: {exc}")
        return result

    if not isinstance(data, list):
        result.source_errors.append("JSON root must be a list of transactions")
        return result

    result.total_records = len(data)

    for record_number, raw_record in enumerate(data, start=1):
        if not isinstance(raw_record, dict):
            result.rejected.append(RejectedRecord(record_number, raw_record, ("transaction must be a JSON object",)))
            continue

        try:
            transaction = normalize_json_record(raw_record)
        except (TypeError, ValueError) as exc:
            result.rejected.append(RejectedRecord(record_number, raw_record, (str(exc),)))
            continue

        if last_processed_id is not None and transaction["id"] <= last_processed_id:
            result.skipped_by_incremental_filter += 1
            continue

        try:
            is_valid, reasons = validator(transaction)
        except Exception as exc:
            result.rejected.append(RejectedRecord(record_number, raw_record, (f"validator error: {exc}",)))
            continue

        if is_valid:
            result.accepted.append(transaction)
        else:
            result.rejected.append(RejectedRecord(record_number, raw_record, tuple(reasons) or ("record failed shared validation",)))

    return result

# Backward compatibility with the original function name
load_json = ingest_json