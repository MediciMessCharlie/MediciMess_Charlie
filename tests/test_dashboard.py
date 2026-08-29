"""Tests for the Phase 6B Dash application shell."""

import httpx
import pytest

from dashboard import app as dashboard_module
from dashboard.app import app
from dashboard.client import DashboardAPIClient, DashboardAPIError


def test_dashboard_shell_has_expected_identity():
    assert app.title == "Medici Bank Branch Operations"
    assert app.layout.id == "dashboard-shell"


def test_dashboard_home_page_is_served():
    response = app.server.test_client().get("/")

    assert response.status_code == 200
    assert b"Medici Bank Branch Operations" in response.data


def test_dashboard_api_client_loads_branches():
    def respond(request):
        assert request.url.path == "/api/branches"
        return httpx.Response(
            200,
            json={"count": 2, "items": ["Florence", "Rome"]},
        )

    http_client = httpx.Client(transport=httpx.MockTransport(respond))
    client = DashboardAPIClient("http://testserver", http_client=http_client)

    assert client.get_branches() == ["Florence", "Rome"]


def test_dashboard_api_client_translates_api_errors():
    def respond(_request):
        return httpx.Response(
            503,
            json={
                "error": {
                    "code": "DATA_UNAVAILABLE",
                    "message": "Serving artifacts are unavailable.",
                }
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(respond))
    client = DashboardAPIClient("http://testserver", http_client=http_client)

    with pytest.raises(DashboardAPIError, match="Serving artifacts"):
        client.get_branches()


def test_dashboard_api_client_loads_kpis():
    def respond(request):
        assert request.url.path == "/api/kpis"
        assert request.url.params["branch"] == "Florence"
        return httpx.Response(
            200,
            json={
                "count": 1,
                "items": [{"branch": "Florence", "period": "1420-01"}],
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(respond))
    client = DashboardAPIClient("http://testserver", http_client=http_client)

    assert client.get_kpis("Florence") == [
        {"branch": "Florence", "period": "1420-01"}
    ]


def test_global_controls_use_api_branches_and_periods(monkeypatch):
    class StubClient:
        def get_branches(self):
            return ["Avignon", "Florence", "Rome"]

        def get_kpis(self, branch):
            assert branch == "Florence"
            return [
                {"branch": branch, "period": period}
                for period in (
                    "1419-01", "1419-02", "1419-03", "1419-04", "1419-05",
                    "1419-06", "1419-07", "1419-08", "1419-09", "1419-10",
                    "1419-11", "1419-12", "1420-01", "1420-02",
                )
            ]

    monkeypatch.setattr(dashboard_module, "api_client", StubClient())

    branch_options, branch_value, branch_error = (
        dashboard_module.load_branch_controls("/")
    )
    start_options, start_value, end_options, end_value, period_error = (
        dashboard_module.load_period_controls(branch_value)
    )

    assert branch_options == [
        {"label": "Avignon", "value": "Avignon"},
        {"label": "Florence", "value": "Florence"},
        {"label": "Rome", "value": "Rome"},
    ]
    assert branch_value == "Florence"
    assert branch_error == ""
    assert start_options == end_options
    assert start_value == "1419-03"
    assert end_value == "1420-02"
    assert period_error == ""


def test_kpi_cards_aggregate_selected_months(monkeypatch):
    class StubClient:
        def get_kpis(self, branch, *, start=None, end=None):
            assert branch == "Florence"
            current = [
                {
                    "period": "1420-01",
                    "closing_cash_balance": "100.00",
                    "total_deposits": "20.00",
                    "total_withdrawals": "5.00",
                    "loan_portfolio_balance": "50.00",
                    "net_income": "10.00",
                },
                {
                    "period": "1420-02",
                    "closing_cash_balance": "130.00",
                    "total_deposits": "30.00",
                    "total_withdrawals": "7.00",
                    "loan_portfolio_balance": "80.00",
                    "net_income": "15.00",
                },
            ]
            prior = [
                {
                    "period": "1419-01",
                    "closing_cash_balance": "90.00",
                    "total_deposits": "10.00",
                    "total_withdrawals": "8.00",
                    "loan_portfolio_balance": "40.00",
                    "net_income": "8.00",
                },
                {
                    "period": "1419-02",
                    "closing_cash_balance": "110.00",
                    "total_deposits": "20.00",
                    "total_withdrawals": "6.00",
                    "loan_portfolio_balance": "60.00",
                    "net_income": "12.00",
                },
            ]
            if (start, end) == ("1420-01", "1420-02"):
                return current
            assert (start, end) == ("1419-01", "1419-02")
            return prior

        def get_alerts(self, branch, *, start=None, end=None):
            assert branch == "Florence"
            if (start, end) == ("1420-01", "1420-02"):
                return [{"alert_id": 1}, {"alert_id": 2}]
            assert (start, end) == ("1419-01", "1419-02")
            return [{"alert_id": 3}]

    monkeypatch.setattr(dashboard_module, "api_client", StubClient())

    cards = dashboard_module.load_kpi_cards("Florence", "1420-01", "1420-02")
    displayed_values = [card.children[1].children for card in cards]
    displayed_deltas = [card.children[2].children for card in cards]

    assert cards[0].children[0].children == "Modeled Cash Position"
    assert displayed_values == [
        "130.00 florins",
        "50.00 florins",
        "12.00 florins",
        "80.00 florins",
        "25.00 florins",
        "2",
    ]
    assert displayed_deltas == [
        "▲ 20.00 florins vs prior year",
        "▲ 20.00 florins vs prior year",
        "▼ 2.00 florins vs prior year",
        "▲ 20.00 florins vs prior year",
        "▲ 5.00 florins vs prior year",
        "▲ 1 vs prior year",
    ]


def test_kpi_cards_explain_missing_prior_year(monkeypatch):
    record = {
        "period": "1390-01",
        "closing_cash_balance": "100.00",
        "total_deposits": "20.00",
        "total_withdrawals": "5.00",
        "loan_portfolio_balance": "50.00",
        "net_income": "10.00",
    }

    class StubClient:
        def get_kpis(self, branch, *, start=None, end=None):
            return [record] if start == "1390-01" else []

        def get_alerts(self, branch, *, start=None, end=None):
            return []

    monkeypatch.setattr(dashboard_module, "api_client", StubClient())

    cards = dashboard_module.load_kpi_cards("Florence", "1390-01", "1390-01")

    assert all(
        card.children[2].children == "Prior-year data unavailable"
        for card in cards
    )


def test_dashboard_api_client_loads_cashflow():
    def respond(request):
        assert request.url.path == "/api/cashflow"
        assert request.url.params["branch"] == "Florence"
        assert request.url.params["granularity"] == "monthly"
        return httpx.Response(
            200,
            json={
                "granularity": "monthly",
                "count": 1,
                "items": [{"branch": "Florence", "period": "1420-01"}],
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(respond))
    client = DashboardAPIClient("http://testserver", http_client=http_client)

    assert client.get_cashflow("Florence") == [
        {"branch": "Florence", "period": "1420-01"}
    ]


def test_cashflow_panel_builds_charts_and_fallback_table(monkeypatch):
    records = [
        {
            "branch": "Florence",
            "period": "1420-01",
            "total_cash_inflows": "100.00",
            "total_cash_outflows": "40.00",
            "net_cash_movement": "60.00",
            "closing_cash_balance": "60.00",
        },
        {
            "branch": "Florence",
            "period": "1420-02",
            "total_cash_inflows": "150.00",
            "total_cash_outflows": "50.00",
            "net_cash_movement": "100.00",
            "closing_cash_balance": "160.00",
        },
    ]

    class StubClient:
        def get_cashflow(self, branch, *, start=None, end=None):
            assert (branch, start, end) == ("Florence", "1420-01", "1420-02")
            return records

    monkeypatch.setattr(dashboard_module, "api_client", StubClient())

    balance, movement, table, error = dashboard_module.load_cashflow_panel(
        "Florence", "1420-01", "1420-02"
    )

    assert list(balance.data[0].y) == [60.0, 160.0]
    assert list(movement.data[0].y) == [100.0, 150.0]
    assert list(movement.data[1].y) == [40.0, 50.0]
    assert len(table.children[1].children) == 2
    assert error == ""


def test_dashboard_api_client_loads_expenses():
    def respond(request):
        assert request.url.path == "/api/expenses"
        assert request.url.params["branch"] == "Florence"
        assert request.url.params["start"] == "1420-01"
        assert request.url.params["end"] == "1420-02"
        return httpx.Response(
            200,
            json={
                "count": 1,
                "items": [
                    {
                        "branch": "Florence",
                        "period": "1420-01",
                        "category": "Security Expense",
                        "counterparty": "Security Guild",
                        "transaction_count": "2",
                        "amount": "300.00",
                    }
                ],
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(respond))
    client = DashboardAPIClient("http://testserver", http_client=http_client)

    records = client.get_expenses(
        "Florence", start="1420-01", end="1420-02"
    )

    assert records[0]["counterparty"] == "Security Guild"


def test_expense_panel_stacks_categories_and_ranks_counterparties(monkeypatch):
    records = [
        {
            "branch": "Florence",
            "period": "1420-01",
            "category": "Security Expense",
            "counterparty": "Security Guild",
            "transaction_count": "2",
            "amount": "300.00",
        },
        {
            "branch": "Florence",
            "period": "1420-02",
            "category": "Security Expense",
            "counterparty": "City Watch",
            "transaction_count": "1",
            "amount": "100.00",
        },
        {
            "branch": "Florence",
            "period": "1420-01",
            "category": "Rent Expense",
            "counterparty": "Landlord",
            "transaction_count": "1",
            "amount": "200.00",
        },
    ]

    class StubClient:
        def get_expenses(self, branch, *, start=None, end=None):
            assert (branch, start, end) == ("Florence", "1420-01", "1420-02")
            return records

    monkeypatch.setattr(dashboard_module, "api_client", StubClient())

    figure, table, error = dashboard_module.load_expense_panel(
        "Florence", "1420-01", "1420-02"
    )

    security_trace = next(
        trace for trace in figure.data if trace.name == "Security Expense"
    )
    first_row = table.children[1].children[0]

    assert list(security_trace.y) == [300.0, 100.0]
    assert figure.layout.legend.orientation == "h"
    assert figure.layout.legend.y == 1.08
    assert figure.layout.title.text is None
    assert figure.layout.margin.t == 100
    assert first_row.children[1].children == "Security Guild"
    assert error == ""


def test_dashboard_api_client_loads_loans():
    def respond(request):
        assert request.url.path == "/api/loans"
        assert request.url.params["branch"] == "Florence"
        return httpx.Response(
            200,
            json={
                "count": 1,
                "items": [
                    {
                        "branch": "Florence",
                        "period": "1420-01",
                        "counterparty": "Wool Merchant",
                        "loans_issued": "1000.00",
                        "loans_repaid": "200.00",
                        "interest_earned": "20.00",
                        "net_loan_movement": "800.00",
                    }
                ],
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(respond))
    client = DashboardAPIClient("http://testserver", http_client=http_client)

    assert client.get_loans("Florence")[0]["counterparty"] == "Wool Merchant"


def test_loan_panel_aggregates_months_and_ranks_issuances(monkeypatch):
    records = [
        {
            "branch": "Florence",
            "period": "1420-01",
            "counterparty": "Wool Merchant",
            "loans_issued": "1000.00",
            "loans_repaid": "200.00",
            "interest_earned": "20.00",
            "net_loan_movement": "800.00",
        },
        {
            "branch": "Florence",
            "period": "1420-01",
            "counterparty": "Silk Merchant",
            "loans_issued": "500.00",
            "loans_repaid": "100.00",
            "interest_earned": "10.00",
            "net_loan_movement": "400.00",
        },
        {
            "branch": "Florence",
            "period": "1420-02",
            "counterparty": "Spice Merchant",
            "loans_issued": "2000.00",
            "loans_repaid": "300.00",
            "interest_earned": "30.00",
            "net_loan_movement": "1700.00",
        },
    ]

    class StubClient:
        def get_loans(self, branch, *, start=None, end=None):
            assert (branch, start, end) == ("Florence", "1420-01", "1420-02")
            return records

    monkeypatch.setattr(dashboard_module, "api_client", StubClient())

    figure, donut, table, error = dashboard_module.load_loan_panel(
        "Florence", "1420-01", "1420-02"
    )

    issued_trace = next(trace for trace in figure.data if trace.name == "Loans issued")
    first_row = table.children[1].children[0]

    assert list(issued_trace.y) == [1500.0, 2000.0]
    assert list(donut.data[0].labels) == [
        "Spice Merchant",
        "Wool Merchant",
        "Silk Merchant",
    ]
    assert list(donut.data[0].values) == [2000.0, 1000.0, 500.0]
    assert first_row.children[1].children == "Spice Merchant"
    assert error == ""


def test_alert_panel_counts_filters_and_ranks_severity(monkeypatch):
    records = [
        {
            "alert_id": 2,
            "rule": "C",
            "severity": "MEDIUM",
            "branch": "Florence",
            "period": "1420-01",
            "affected_transaction_ids": [11, 12],
            "counterparty": "Silk Merchant",
            "metric_value": "2",
            "threshold_value": "1",
            "description": "Possible duplicate transactions.",
            "detected_at": "2026-08-28T18:02:07",
            "status": "OPEN",
        },
        {
            "alert_id": 1,
            "rule": "G",
            "severity": "HIGH",
            "branch": "Florence",
            "period": "1420-01",
            "affected_transaction_ids": [10],
            "counterparty": "New Merchant",
            "metric_value": "12000.00",
            "threshold_value": "10000.00",
            "description": "High first-period activity.",
            "detected_at": "2026-08-28T18:02:07",
            "status": "OPEN",
        },
    ]

    class StubClient:
        def get_alerts(self, branch, *, start=None, end=None):
            assert (branch, start, end) == ("Florence", "1420-01", "1420-02")
            return records

    monkeypatch.setattr(dashboard_module, "api_client", StubClient())

    summary, table_container, error = dashboard_module.load_alert_panel(
        "Florence", "1420-01", "1420-02", "ALL"
    )
    table = table_container.children
    first_row = table.children[1].children[0]

    assert [card.children[1].children for card in summary] == ["1", "1", "0"]
    assert first_row.children[0].children == "HIGH"
    assert first_row.children[4].children == "10"
    assert error == ""

    _, filtered_table_container, filtered_error = dashboard_module.load_alert_panel(
        "Florence", "1420-01", "1420-02", "MEDIUM"
    )
    filtered_table = filtered_table_container.children
    filtered_row = filtered_table.children[1].children[0]

    assert filtered_row.children[0].children == "MEDIUM"
    assert filtered_error == ""


def test_dashboard_api_client_loads_paginated_transactions():
    def respond(request):
        assert request.url.path == "/api/transactions"
        assert request.url.params["branch"] == "Florence"
        assert request.url.params["page"] == "2"
        assert request.url.params["type"] == "deposit"
        return httpx.Response(
            200,
            json={
                "page": 2,
                "per_page": 25,
                "total": 30,
                "total_pages": 2,
                "items": [{"id": 26, "branch": "Florence"}],
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(respond))
    client = DashboardAPIClient("http://testserver", http_client=http_client)

    payload = client.get_transactions("Florence", page=2, type="deposit")

    assert payload["total"] == 30
    assert payload["items"][0]["id"] == 26


def test_transaction_panel_translates_periods_and_preserves_pagination(monkeypatch):
    record = {
        "id": 26,
        "date": "1420-02-29",
        "type": "deposit",
        "branch": "Florence",
        "counterparty": "Silk Merchant",
        "description": "Merchant deposit",
        "debit_account": "Cash",
        "debit_amount": "500.00",
        "credit_account": "Deposits Payable",
        "credit_amount": "500.00",
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    }

    class StubClient:
        def get_transactions(self, branch, **filters):
            assert branch == "Florence"
            assert filters == {
                "start": "1420-01-01",
                "end": "1420-02-29",
                "type": "deposit",
                "search": "silk",
                "sort_by": "debit_amount",
                "sort_order": "desc",
                "page": 2,
                "per_page": 25,
            }
            return {
                "page": 2,
                "per_page": 25,
                "total": 30,
                "total_pages": 2,
                "items": [record],
            }

    monkeypatch.setattr(dashboard_module, "api_client", StubClient())

    table_container, summary, error, metadata = dashboard_module.load_transaction_panel(
        "Florence", "1420-01", "1420-02", " silk ", "deposit",
        "debit_amount", "desc", 2,
    )
    table = table_container.children
    first_row = table.children[1].children[0]

    assert first_row.children[0].children == 26
    assert first_row.children[6].children == "500.00 florins"
    assert summary == "Page 2 of 2 · 30 matching transactions"
    assert error == ""
    assert metadata == {"total_pages": 2}


def test_transaction_page_navigation_is_bounded_and_filters_reset():
    assert dashboard_module.calculate_transaction_page(
        "transaction-next-page", 2, 4
    ) == 3
    assert dashboard_module.calculate_transaction_page(
        "transaction-next-page", 4, 4
    ) == 4
    assert dashboard_module.calculate_transaction_page(
        "transaction-previous-page", 1, 4
    ) == 1
    assert dashboard_module.calculate_transaction_page(
        "transaction-search", 3, 4
    ) == 1


def test_bill_panel_requests_and_displays_observable_accounting_fields(monkeypatch):
    record = {
        "id": 11,
        "date": "1390-01-03",
        "type": "bill_of_exchange",
        "branch": "Florence",
        "counterparty": "Transfer to Geneva",
        "description": "Bill of exchange from Florence to Geneva",
        "debit_account": "Due from Geneva",
        "debit_amount": "14992.79",
        "credit_account": "Cash",
        "credit_amount": "14749.91",
        "credit_account_2": "Exchange Fee Revenue",
        "credit_amount_2": "242.88",
        "currency": "florin",
    }

    class StubClient:
        def get_transactions(self, branch, **filters):
            assert branch == "Florence"
            assert filters == {
                "start": "1390-01-01",
                "end": "1390-12-31",
                "type": "bill_of_exchange",
                "sort_by": "date",
                "sort_order": "desc",
                "page": 2,
                "per_page": 25,
            }
            return {
                "page": 2,
                "per_page": 25,
                "total": 30,
                "total_pages": 2,
                "items": [record],
            }

    monkeypatch.setattr(dashboard_module, "api_client", StubClient())

    table_container, summary, error = dashboard_module.load_bill_panel(
        "Florence", "1390-01", "1390-12", 2
    )
    table = table_container.children
    first_row = table.children[1].children[0]

    assert first_row.children[2].children == "Transfer to Geneva"
    assert first_row.children[4].children == "14,992.79 florins"
    assert first_row.children[6].children == "242.88 florins"
    assert summary == "Page 2 of 2 · 30 matching bills"
    assert error == ""
