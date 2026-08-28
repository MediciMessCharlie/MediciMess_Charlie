"""Executable validation for the Phase 3/4 to Phase 5 handoff."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any


PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

KPI_DECIMAL_FIELDS = frozenset(
    {
        "total_cash_inflows", "total_cash_outflows", "net_cash_movement",
        "closing_cash_balance", "total_deposits", "total_withdrawals",
        "avg_deposit_size", "avg_withdrawal_size", "loans_issued",
        "loans_repaid", "interest_earned", "loan_portfolio_balance",
        "interest_yield", "total_operating_expenses",
        "expense_per_transaction", "exchange_fee_revenue",
        "interest_income", "trading_revenue", "total_revenue",
        "net_income", "net_income_margin",
    }
)
KPI_COUNT_FIELDS = frozenset({"deposit_count", "withdrawal_count"})
KPI_REQUIRED_FIELDS = (
    frozenset({"branch", "period", "expenses_by_category", "top_payees_by_expense"})
    | KPI_DECIMAL_FIELDS
    | KPI_COUNT_FIELDS
)
ALERT_REQUIRED_FIELDS = frozenset(
    {
        "alert_id", "rule", "severity", "branch", "period",
        "affected_transaction_ids", "counterparty", "metric_value",
        "threshold_value", "description", "detected_at", "status",
    }
)
EXPENSE_FIELDS = (
    "branch", "period", "category", "counterparty", "transaction_count", "amount"
)
LOAN_FIELDS = (
    "branch", "period", "counterparty", "loans_issued", "loans_repaid",
    "interest_earned", "net_loan_movement",
)


class ServingContractError(ValueError):
    """Raised when an upstream record cannot safely be served."""


def _mapping(record: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(record, Mapping):
        raise ServingContractError(f"{name} must be a dictionary-like mapping")
    return record


def _fields(record: Mapping[str, Any], required: set[str] | frozenset[str], name: str) -> None:
    missing = sorted(required - record.keys())
    if missing:
        raise ServingContractError(
            f"{name} missing required field(s): {', '.join(missing)}"
        )


def validate_branch(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ServingContractError("branch must be a non-empty string")
    return value.strip()


def validate_period(value: Any) -> str:
    if not isinstance(value, str) or not PERIOD_PATTERN.fullmatch(value):
        raise ServingContractError("period must use YYYY-MM format")
    return value


def _decimal(value: Any, field: str) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ServingContractError(f"{field} must be a finite Decimal")


def _count(value: Any, field: str, *, positive: bool = False) -> None:
    minimum = 1 if positive else 0
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        qualifier = "positive" if positive else "non-negative"
        raise ServingContractError(f"{field} must be a {qualifier} integer")


def validate_kpi(record: Any) -> Mapping[str, Any]:
    record = _mapping(record, "KPI record")
    _fields(record, KPI_REQUIRED_FIELDS, "KPI record")
    validate_branch(record["branch"])
    validate_period(record["period"])
    for field in KPI_DECIMAL_FIELDS:
        _decimal(record[field], field)
    for field in KPI_COUNT_FIELDS:
        _count(record[field], field)

    categories = _mapping(record["expenses_by_category"], "expenses_by_category")
    for category, amount in categories.items():
        if not isinstance(category, str) or not category.strip():
            raise ServingContractError("expense category names must be non-empty strings")
        _decimal(amount, f"expenses_by_category[{category!r}]")

    payees = record["top_payees_by_expense"]
    if not isinstance(payees, list):
        raise ServingContractError("top_payees_by_expense must be a list")
    for index, payee in enumerate(payees):
        payee = _mapping(payee, f"top_payees_by_expense[{index}]")
        _fields(payee, {"counterparty", "amount"}, f"top_payees_by_expense[{index}]")
        if not isinstance(payee["counterparty"], str) or not payee["counterparty"].strip():
            raise ServingContractError("top payee counterparty must be a non-empty string")
        _decimal(payee["amount"], "top payee amount")
    return record


def validate_alert(record: Any) -> Mapping[str, Any]:
    record = _mapping(record, "alert record")
    _fields(record, ALERT_REQUIRED_FIELDS, "alert record")
    _count(record["alert_id"], "alert_id", positive=True)
    if record["rule"] not in set("ABCDEFG"):
        raise ServingContractError("rule must be one of A through G")
    if record["severity"] not in {"LOW", "MEDIUM", "HIGH"}:
        raise ServingContractError("severity must be LOW, MEDIUM, or HIGH")
    if record["status"] not in {"OPEN", "ACKNOWLEDGED", "RESOLVED"}:
        raise ServingContractError("alert status is invalid")
    validate_branch(record["branch"])
    validate_period(record["period"])
    if not isinstance(record["affected_transaction_ids"], list):
        raise ServingContractError("affected_transaction_ids must be a list")
    for transaction_id in record["affected_transaction_ids"]:
        _count(transaction_id, "affected transaction ID", positive=True)
    if record["counterparty"] is not None and not isinstance(record["counterparty"], str):
        raise ServingContractError("counterparty must be a string or None")
    for field in ("metric_value", "threshold_value"):
        value = record[field]
        if isinstance(value, bool) or not isinstance(value, (Decimal, int, float)):
            raise ServingContractError(f"{field} must be numeric")
        if isinstance(value, Decimal) and not value.is_finite():
            raise ServingContractError(f"{field} must be finite")
    if not isinstance(record["description"], str) or not record["description"].strip():
        raise ServingContractError("description must be a non-empty string")
    if not isinstance(record["detected_at"], str):
        raise ServingContractError("detected_at must be an ISO timestamp string")
    try:
        datetime.fromisoformat(record["detected_at"])
    except ValueError as exc:
        raise ServingContractError("detected_at must be an ISO timestamp string") from exc
    return record


def validate_expense_detail(record: Any) -> Mapping[str, Any]:
    record = _mapping(record, "expense detail")
    _fields(record, set(EXPENSE_FIELDS), "expense detail")
    validate_branch(record["branch"])
    validate_period(record["period"])
    for field in ("category", "counterparty"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ServingContractError(f"{field} must be a non-empty string")
    _count(record["transaction_count"], "transaction_count")
    _decimal(record["amount"], "amount")
    return record


def validate_loan_detail(record: Any) -> Mapping[str, Any]:
    record = _mapping(record, "loan detail")
    _fields(record, set(LOAN_FIELDS), "loan detail")
    validate_branch(record["branch"])
    validate_period(record["period"])
    if not isinstance(record["counterparty"], str) or not record["counterparty"].strip():
        raise ServingContractError("counterparty must be a non-empty string")
    for field in LOAN_FIELDS[3:]:
        _decimal(record[field], field)
    expected = record["loans_issued"] - record["loans_repaid"]
    if record["net_loan_movement"] != expected:
        raise ServingContractError(
            "net_loan_movement must equal loans_issued minus loans_repaid"
        )
    return record
