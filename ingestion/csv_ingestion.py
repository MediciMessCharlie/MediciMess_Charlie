"""Reusable, streaming ingestion for Medici transaction CSV files.

The module deliberately keeps ingestion separate from the ledger.  Downstream
code receives one consistent, typed structure regardless of how the CSV text
represented its values.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, Union


LOGGER = logging.getLogger(__name__)

REQUIRED_COLUMNS = frozenset(
    {
        "id", "date", "branch", "type", "counterparty", "description",
        "debit_account", "debit_amount", "credit_account", "credit_amount",
        "currency",
    }
)
OPTIONAL_COLUMNS = frozenset({"credit_account_2", "credit_amount_2"})


class CSVSchemaError(ValueError):
    """Raised before reading records when a CSV header is incomplete."""


class TransactionValidationError(ValueError):
    """Raised when an individual transaction cannot pass validation."""


@dataclass(frozen=True)
class TransactionRecord:
    """The common, typed transaction structure used by the data pipeline."""

    id: int
    date: date
    branch: str
    type: str
    counterparty: str
    description: str
    debit_account: str
    debit_amount: Decimal
    credit_account: str
    credit_amount: Decimal
    credit_account_2: Optional[str] = None
    credit_amount_2: Optional[Decimal] = None
    currency: str = "florin"

    def __getitem__(self, field_name: str) -> Any:
        """Provide the dictionary-style access used by the shared validator."""
        try:
            return getattr(self, field_name)
        except AttributeError as exc:
            raise KeyError(field_name) from exc

    def get(self, field_name: str, default: Any = None) -> Any:
        """Match ``dict.get`` so all ingestion paths share one validator."""
        return getattr(self, field_name, default)


@dataclass(frozen=True)
class RejectedRecord:
    row_number: int
    reason: str


@dataclass
class CSVIngestionResult:
    transactions: List[TransactionRecord] = field(default_factory=list)
    rejected_records: List[RejectedRecord] = field(default_factory=list)
    duplicate_rows: List[Tuple[int, int]] = field(default_factory=list)
    skipped_older_records: int = 0

    @property
    def accepted_count(self) -> int:
        return len(self.transactions)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected_records)


ValidationResult = Optional[Tuple[bool, List[str]]]
TransactionValidator = Callable[[TransactionRecord], ValidationResult]


def validate_transaction(transaction: TransactionRecord) -> None:
    """Shared validation applied to every normalized transaction."""
    text_fields = (
        "branch", "type", "counterparty", "description", "debit_account",
        "credit_account", "currency",
    )
    missing = [name for name in text_fields if not getattr(transaction, name)]
    if missing:
        raise TransactionValidationError(
            "required value(s) are blank: " + ", ".join(missing)
        )
    if transaction.id <= 0:
        raise TransactionValidationError("id must be greater than zero")
    if transaction.debit_amount <= 0 or transaction.credit_amount < 0:
        raise TransactionValidationError("transaction amounts must be positive")
    second_credit = transaction.credit_amount_2 or Decimal("0")
    if second_credit < 0:
        raise TransactionValidationError("credit_amount_2 cannot be negative")
    if second_credit and not transaction.credit_account_2:
        raise TransactionValidationError(
            "credit_account_2 is required when credit_amount_2 is present"
        )
    total_credit = transaction.credit_amount + second_credit
    if transaction.debit_amount != total_credit:
        raise TransactionValidationError(
            f"unbalanced transaction: debit {transaction.debit_amount} != "
            f"credits {total_credit}"
        )


def _required_text(row: dict, name: str) -> str:
    value = row.get(name)
    if value is None or not value.strip():
        raise TransactionValidationError(f"required value is blank: {name}")
    return value.strip()


def _decimal(
    row: dict, name: str, *, optional: bool = False
) -> Optional[Decimal]:
    raw = row.get(name)
    if optional and (raw is None or not raw.strip()):
        return None
    if raw is None or not raw.strip():
        raise TransactionValidationError(f"required value is blank: {name}")
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise TransactionValidationError(f"invalid decimal for {name}: {raw!r}") from exc
    if not value.is_finite():
        raise TransactionValidationError(f"non-finite decimal for {name}: {raw!r}")
    return value


def normalize_csv_row(row: dict) -> TransactionRecord:
    """Coerce one DictReader row into the common transaction structure."""
    try:
        transaction_id = int(_required_text(row, "id"))
    except ValueError as exc:
        raise TransactionValidationError(f"invalid integer for id: {row.get('id')!r}") from exc
    try:
        transaction_date = date.fromisoformat(_required_text(row, "date"))
    except ValueError as exc:
        raise TransactionValidationError(f"invalid ISO date: {row.get('date')!r}") from exc

    second_account = (row.get("credit_account_2") or "").strip() or None
    return TransactionRecord(
        id=transaction_id,
        date=transaction_date,
        branch=_required_text(row, "branch"),
        type=_required_text(row, "type"),
        counterparty=_required_text(row, "counterparty"),
        description=_required_text(row, "description"),
        debit_account=_required_text(row, "debit_account"),
        debit_amount=_decimal(row, "debit_amount"),
        credit_account=_required_text(row, "credit_account"),
        credit_amount=_decimal(row, "credit_amount"),
        credit_account_2=second_account,
        credit_amount_2=_decimal(row, "credit_amount_2", optional=True),
        currency=_required_text(row, "currency"),
    )


def ingest_csv(
    filename: Union[str, Path],
    *,
    last_processed_id: Optional[int] = None,
    validator: TransactionValidator = validate_transaction,
    encoding: str = "utf-8-sig",
) -> CSVIngestionResult:
    """Stream a CSV file, normalize valid rows, and report every rejection.

    Duplicate keys are surfaced in ``duplicate_rows`` but remain accepted, as
    required by the pipeline specification. Rows at or below
    ``last_processed_id`` are counted separately and do not enter validation.
    """
    result = CSVIngestionResult()
    seen = {}

    with open(filename, "r", encoding=encoding, newline="") as csv_file:
        reader = csv.DictReader(csv_file, strict=True)
        if reader.fieldnames is None:
            raise CSVSchemaError("CSV file has no header")
        headers = {name.strip() for name in reader.fieldnames if name}
        missing = sorted(REQUIRED_COLUMNS - headers)
        if missing:
            raise CSVSchemaError("missing required column(s): " + ", ".join(missing))

        try:
            for row_number, row in enumerate(reader, start=2):
                try:
                    transaction = normalize_csv_row(row)
                    if last_processed_id is not None and transaction.id <= last_processed_id:
                        result.skipped_older_records += 1
                        continue
                    validation_result = validator(transaction)
                    if validation_result is not None:
                        is_valid, reasons = validation_result
                        if not is_valid:
                            raise TransactionValidationError(
                                "; ".join(reasons) or
                                "record failed shared validation"
                            )
                    duplicate_key = (
                        transaction.date, transaction.branch, transaction.type,
                        transaction.counterparty, transaction.debit_amount,
                        transaction.credit_account,
                    )
                    original_row = seen.get(duplicate_key)
                    if original_row is not None:
                        result.duplicate_rows.append((original_row, row_number))
                    else:
                        seen[duplicate_key] = row_number
                    result.transactions.append(transaction)
                except (TransactionValidationError, ValueError, TypeError) as exc:
                    reason = str(exc)
                    result.rejected_records.append(RejectedRecord(row_number, reason))
                    LOGGER.warning("Rejected CSV row %s: %s", row_number, reason)
        except csv.Error as exc:
            row_number = reader.line_num or 2
            reason = f"malformed CSV: {exc}"
            result.rejected_records.append(RejectedRecord(row_number, reason))
            LOGGER.warning("Rejected malformed CSV at line %s: %s", row_number, exc)

    return result
