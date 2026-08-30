"""Cross-branch calculations for the Phase 7 network overview."""

from collections import defaultdict
from decimal import Decimal
from typing import Any


ZERO = Decimal("0")
HUNDRED = Decimal("100")
OUTLIER_METRICS = ("expense_ratio", "loan_yield")


def _total(records: list[dict[str, Any]], field: str) -> Decimal:
    """Sum one serialized financial field without using binary floats."""
    return sum((Decimal(str(record[field])) for record in records), ZERO)


def _percentage(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Return a two-decimal percentage with a safe zero denominator."""
    if denominator == ZERO:
        return Decimal("0.00")
    return ((numerator / denominator) * HUNDRED).quantize(Decimal("0.01"))


def detect_statistical_outliers(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Flag branch ratios more than two population standard deviations away."""
    outliers = []
    for metric in OUTLIER_METRICS:
        values = [Decimal(str(row[metric])) for row in rows]
        if not values:
            continue

        average = sum(values, ZERO) / Decimal(len(values))
        variance = sum(
            ((value - average) ** 2 for value in values), ZERO
        ) / Decimal(len(values))
        standard_deviation = variance.sqrt()
        if standard_deviation == ZERO:
            continue

        threshold = standard_deviation * Decimal("2")
        for row, value in zip(rows, values):
            deviation = value - average
            if abs(deviation) > threshold:
                outliers.append(
                    {
                        "branch": row["branch"],
                        "metric": metric,
                        "value": value,
                        "network_average": average,
                        "standard_deviation": standard_deviation,
                        "direction": "HIGH" if deviation > ZERO else "LOW",
                    }
                )
    return outliers


def summarize_network(
    kpi_records: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build branch comparison rows and a network aggregate row."""
    records_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in kpi_records:
        records_by_branch[record["branch"]].append(record)

    open_alerts_by_branch: dict[str, int] = defaultdict(int)
    for alert in alerts:
        if alert["status"] == "OPEN":
            open_alerts_by_branch[alert["branch"]] += 1

    rows = []
    for branch in sorted(records_by_branch):
        records = records_by_branch[branch]
        latest = max(records, key=lambda record: record["period"])
        expenses = _total(records, "total_operating_expenses")
        revenue = _total(records, "total_revenue")
        interest = _total(records, "interest_earned")
        repayments = _total(records, "loans_repaid")
        rows.append(
            {
                "branch": branch,
                "modeled_cash_position": Decimal(
                    str(latest["closing_cash_balance"])
                ),
                "net_income": _total(records, "net_income"),
                "loan_portfolio_balance": Decimal(
                    str(latest["loan_portfolio_balance"])
                ),
                "open_alerts": open_alerts_by_branch[branch],
                "expense_ratio": _percentage(expenses, revenue),
                "loan_yield": _percentage(interest, repayments),
                "total_operating_expenses": expenses,
                "total_revenue": revenue,
                "interest_earned": interest,
                "loans_repaid": repayments,
            }
        )

    totals = {
        "branch": "Network Total",
        "modeled_cash_position": sum(
            (row["modeled_cash_position"] for row in rows), ZERO
        ),
        "net_income": sum((row["net_income"] for row in rows), ZERO),
        "loan_portfolio_balance": sum(
            (row["loan_portfolio_balance"] for row in rows), ZERO
        ),
        "open_alerts": sum(row["open_alerts"] for row in rows),
        "total_operating_expenses": sum(
            (row["total_operating_expenses"] for row in rows), ZERO
        ),
        "total_revenue": sum((row["total_revenue"] for row in rows), ZERO),
        "interest_earned": sum((row["interest_earned"] for row in rows), ZERO),
        "loans_repaid": sum((row["loans_repaid"] for row in rows), ZERO),
    }
    totals["expense_ratio"] = _percentage(
        totals["total_operating_expenses"], totals["total_revenue"]
    )
    totals["loan_yield"] = _percentage(
        totals["interest_earned"], totals["loans_repaid"]
    )
    return {
        "branches": rows,
        "totals": totals,
        "outliers": detect_statistical_outliers(rows),
    }
