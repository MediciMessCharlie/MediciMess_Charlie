"""Tests for Phase 7 cross-branch network calculations."""

from decimal import Decimal

from dashboard.network import detect_statistical_outliers, summarize_network


def _kpi(branch, period, cash, income, loans, expenses, revenue, interest, repaid):
    return {
        "branch": branch,
        "period": period,
        "closing_cash_balance": cash,
        "net_income": income,
        "loan_portfolio_balance": loans,
        "total_operating_expenses": expenses,
        "total_revenue": revenue,
        "interest_earned": interest,
        "loans_repaid": repaid,
    }


def test_network_summary_uses_latest_snapshots_period_totals_and_open_alerts():
    records = [
        _kpi("Rome", "1420-01", "80", "30", "40", "20", "100", "5", "50"),
        _kpi("Florence", "1420-01", "100", "40", "60", "10", "100", "8", "40"),
        _kpi("Florence", "1420-02", "130", "50", "90", "20", "100", "12", "60"),
    ]
    alerts = [
        {"branch": "Florence", "status": "OPEN"},
        {"branch": "Florence", "status": "CLOSED"},
        {"branch": "Rome", "status": "OPEN"},
    ]

    result = summarize_network(records, alerts)
    florence, rome = result["branches"]

    assert florence["modeled_cash_position"] == Decimal("130")
    assert florence["net_income"] == Decimal("90")
    assert florence["loan_portfolio_balance"] == Decimal("90")
    assert florence["open_alerts"] == 1
    assert florence["expense_ratio"] == Decimal("15.00")
    assert florence["loan_yield"] == Decimal("20.00")
    assert rome["expense_ratio"] == Decimal("20.00")

    totals = result["totals"]
    assert totals["modeled_cash_position"] == Decimal("210")
    assert totals["net_income"] == Decimal("120")
    assert totals["loan_portfolio_balance"] == Decimal("130")
    assert totals["open_alerts"] == 2
    assert totals["expense_ratio"] == Decimal("16.67")
    assert totals["loan_yield"] == Decimal("16.67")


def test_network_summary_handles_zero_revenue_and_repayments():
    records = [
        _kpi("Avignon", "1420-01", "10", "0", "0", "5", "0", "0", "0")
    ]

    row = summarize_network(records, [])["branches"][0]

    assert row["expense_ratio"] == Decimal("0.00")
    assert row["loan_yield"] == Decimal("0.00")
    assert row["open_alerts"] == 0


def test_statistical_outliers_flag_ratios_more_than_two_standard_deviations():
    rows = [
        {"branch": f"Branch {index}", "expense_ratio": "10", "loan_yield": "5"}
        for index in range(8)
    ]
    rows.append(
        {"branch": "Outlier", "expense_ratio": "100", "loan_yield": "5"}
    )

    outliers = detect_statistical_outliers(rows)

    assert len(outliers) == 1
    assert outliers[0]["branch"] == "Outlier"
    assert outliers[0]["metric"] == "expense_ratio"
    assert outliers[0]["direction"] == "HIGH"


def test_statistical_outliers_handle_empty_and_identical_values():
    assert detect_statistical_outliers([]) == []
    assert detect_statistical_outliers(
        [
            {"branch": "Florence", "expense_ratio": "10", "loan_yield": "5"},
            {"branch": "Rome", "expense_ratio": "10", "loan_yield": "5"},
        ]
    ) == []


def test_network_summary_includes_detected_outliers():
    records = [
        _kpi(
            f"Branch {index}", "1420-01", "10", "1", "5", "10", "100", "5", "100"
        )
        for index in range(8)
    ]
    records.append(
        _kpi("Outlier", "1420-01", "10", "1", "5", "100", "100", "5", "100")
    )

    result = summarize_network(records, [])

    assert result["outliers"][0]["branch"] == "Outlier"
    assert result["outliers"][0]["metric"] == "expense_ratio"
