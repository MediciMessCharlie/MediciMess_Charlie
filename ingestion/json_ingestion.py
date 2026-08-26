"""JSON ingestion for MediciMess transaction records.

This module owns JSON parsing and type normalization. Transaction business
rules belong in the shared validator supplied by the caller, allowing CSV and
JSON ingestion to apply exactly the same validation contract.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


NormalizedTransaction = dict[str, Any]
Validator = Callable[[NormalizedTransaction], tuple[bool, list[str]]]


@dataclass(frozen=True)
class RejectedRecord:
    """A record that could not be normalized or failed shared validation."""

    record_number: int
    raw_record: Any
    reasons: tuple[str, ...]


@dataclass
class IngestionResult:
    """Outcome of one JSON ingestion attempt."""

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


def _required_value(record: Mapping[str, Any], field_name: str) -> Any:
    """Return a required value or raise a clear normalization error."""

    if field_name not in record:
        raise ValueError(f"missing required field: {field_name}")
    value = record[field_name]
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"required field is empty: {field_name}")
    return value


def _as_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    try:
        converted = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"{field_name} must be an integer")
    return converted


def _as_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError("date must be an ISO date string")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError("date must use YYYY-MM-DD format") from exc


def _as_decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric")
    try:
        converted = Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not converted.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return converted


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    converted = str(value).strip()
    return converted or None


def normalize_json_record(record: Mapping[str, Any]) -> NormalizedTransaction:
    """Convert one JSON object to the team's common transaction structure."""

    normalized: NormalizedTransaction = dict(record)
    normalized["id"] = _as_int(_required_value(record, "id"), "id")
    normalized["date"] = _as_date(_required_value(record, "date"))
    normalized["debit_amount"] = _as_decimal(
        _required_value(record, "debit_amount"), "debit_amount"
    )
    normalized["credit_amount"] = _as_decimal(
        _required_value(record, "credit_amount"), "credit_amount"
    )

    secondary_account = _optional_text(record.get("credit_account_2"))
    secondary_amount_raw = record.get("credit_amount_2")
    secondary_amount = (
        None
        if secondary_amount_raw is None
        or (isinstance(secondary_amount_raw, str) and not secondary_amount_raw.strip())
        else _as_decimal(secondary_amount_raw, "credit_amount_2")
    )
    normalized["credit_account_2"] = secondary_account
    normalized["credit_amount_2"] = secondary_amount

    return normalized


def load_json(
    file_path: str | Path,
    validator: Validator,
    last_processed_id: int | None = None,
) -> IngestionResult:
    """Parse, normalize, and validate a JSON transaction batch.

    File-level problems are recorded in ``source_errors``. Individual malformed
    or invalid records are recorded in ``rejected`` so one bad record never
    stops the rest of the batch.
    """

    result = IngestionResult()
    path = Path(file_path)

    try:
        with path.open("r", encoding="utf-8") as source:
            payload = json.load(source)
    except FileNotFoundError:
        result.source_errors.append(f"JSON file not found: {path}")
        return result
    except PermissionError:
        result.source_errors.append(f"JSON file is not readable: {path}")
        return result
    except json.JSONDecodeError as exc:
        result.source_errors.append(
            f"Malformed JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        )
        return result
    except OSError as exc:
        result.source_errors.append(f"Could not read JSON file {path}: {exc}")
        return result

    if not isinstance(payload, list):
        result.source_errors.append("JSON root must be a list of transaction objects")
        return result

    result.total_records = len(payload)

    for record_number, raw_record in enumerate(payload, start=1):
        if not isinstance(raw_record, Mapping):
            result.rejected.append(
                RejectedRecord(
                    record_number,
                    raw_record,
                    ("transaction must be a JSON object",),
                )
            )
            continue

        try:
            normalized = normalize_json_record(raw_record)
        except (TypeError, ValueError) as exc:
            result.rejected.append(
                RejectedRecord(record_number, raw_record, (str(exc),))
            )
            continue

        if last_processed_id is not None and normalized["id"] <= last_processed_id:
            result.skipped_by_incremental_filter += 1
            continue

        try:
            is_valid, reasons = validator(normalized)
        except Exception as exc:  # A validator failure must not stop the batch.
            result.rejected.append(
                RejectedRecord(
                    record_number,
                    raw_record,
                    (f"validator error: {exc}",),
                )
            )
            continue

        if is_valid:
            result.accepted.append(normalized)
        else:
            result.rejected.append(
                RejectedRecord(
                    record_number,
                    raw_record,
                    tuple(reasons) or ("record failed shared validation",),
                )
            )

    return result
