"""Tests for the Phase 6A HTTP API."""

import csv
import json
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.app import app, get_repository, get_transaction_repository
from api.repository import (
    ArtifactRepository,
    ArtifactRepositoryError,
    TransactionRepository,
)


client = TestClient(app)


def test_health_reports_available_service():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "medicimess-api",
    }


def test_repository_loads_kpis_in_branch_period_order(tmp_path):
    metrics_directory = tmp_path / "metrics"
    metrics_directory.mkdir()
    records = [
        {"branch": "Rome", "period": "1420-02", "net_income": "20.00"},
        {"branch": "Florence", "period": "1420-02", "net_income": "10.00"},
        {"branch": "Florence", "period": "1420-01", "net_income": "5.00"},
    ]
    for index, record in enumerate(records):
        path = metrics_directory / f"metrics_{index}.json"
        path.write_text(json.dumps(record), encoding="utf-8")

    repository = ArtifactRepository(tmp_path)

    assert repository.load_kpis() == [records[2], records[1], records[0]]
    assert repository.load_kpis(branch="Florence") == [records[2], records[1]]
    assert repository.load_kpis(
        branch="Florence", start="1420-02", end="1420-02"
    ) == [records[1]]
    assert repository.list_branches() == ["Florence", "Rome"]


def test_repository_rejects_a_reversed_period_range(tmp_path):
    repository = ArtifactRepository(tmp_path)

    with pytest.raises(ArtifactRepositoryError, match="start period"):
        repository.load_kpis(start="1420-02", end="1420-01")


def test_repository_reports_a_missing_metrics_directory(tmp_path):
    repository = ArtifactRepository(tmp_path)

    with pytest.raises(ArtifactRepositoryError, match="Metrics directory"):
        repository.load_kpis()


def test_repository_loads_and_filters_alert_lists(tmp_path):
    alerts_directory = tmp_path / "alerts"
    alerts_directory.mkdir()
    records = [
        {
            "alert_id": 2,
            "branch": "Florence",
            "period": "1420-02",
            "severity": "MEDIUM",
        },
        {
            "alert_id": 1,
            "branch": "Florence",
            "period": "1420-01",
            "severity": "HIGH",
        },
        {
            "alert_id": 3,
            "branch": "Rome",
            "period": "1420-01",
            "severity": "HIGH",
        },
    ]
    (alerts_directory / "alerts_first.json").write_text(
        json.dumps([records[0], records[2]]), encoding="utf-8"
    )
    (alerts_directory / "alerts_second.json").write_text(
        json.dumps([records[1]]), encoding="utf-8"
    )
    (alerts_directory / "alerts_empty.json").write_text("[]", encoding="utf-8")

    repository = ArtifactRepository(tmp_path)

    assert repository.load_alerts() == [records[1], records[0], records[2]]
    assert repository.load_alerts(branch="Florence", severity="HIGH") == [
        records[1]
    ]
    assert repository.load_alerts(start="1420-02", end="1420-02") == [records[0]]


def test_repository_loads_and_filters_expense_csv_rows(tmp_path):
    expenses_directory = tmp_path / "expenses"
    expenses_directory.mkdir()
    records = [
        {
            "branch": "Rome",
            "period": "1420-01",
            "category": "Rent Expense",
            "counterparty": "Landlord",
            "transaction_count": "1",
            "amount": "200.00",
        },
        {
            "branch": "Florence",
            "period": "1420-02",
            "category": "Wages Expense",
            "counterparty": "Workers Guild",
            "transaction_count": "2",
            "amount": "300.00",
        },
        {
            "branch": "Florence",
            "period": "1420-01",
            "category": "Security Expense",
            "counterparty": "Security Guild",
            "transaction_count": "1",
            "amount": "100.00",
        },
    ]
    path = expenses_directory / "expense_breakdown_fixture.csv"
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    repository = ArtifactRepository(tmp_path)

    assert repository.load_expenses() == [records[2], records[1], records[0]]
    assert repository.load_expenses(
        branch="Florence", start="1420-02", end="1420-02"
    ) == [records[1]]


def test_repository_loads_and_filters_loan_activity_csv_rows(tmp_path):
    loans_directory = tmp_path / "loans"
    loans_directory.mkdir()
    records = [
        {
            "branch": "Rome",
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
            "counterparty": "Wool Merchant",
            "loans_issued": "1000.00",
            "loans_repaid": "200.00",
            "interest_earned": "20.00",
            "net_loan_movement": "800.00",
        },
    ]
    path = loans_directory / "loan_portfolio_fixture.csv"
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    repository = ArtifactRepository(tmp_path)

    assert repository.load_loans() == [records[1], records[0]]
    assert repository.load_loans(
        branch="Florence", start="1420-02", end="1420-02"
    ) == [records[1]]


def test_repository_loads_and_filters_time_series_records(tmp_path):
    time_series_directory = tmp_path / "time_series"
    time_series_directory.mkdir()
    records = [
        {
            "branch": "Florence",
            "period": "1420-02",
            "total_cash_inflows": "300.00",
            "total_cash_outflows": "100.00",
            "net_cash_movement": "200.00",
            "closing_cash_balance": "500.00",
        },
        {
            "branch": "Florence",
            "period": "1420-01",
            "total_cash_inflows": "200.00",
            "total_cash_outflows": "50.00",
            "net_cash_movement": "150.00",
            "closing_cash_balance": "300.00",
        },
        {
            "branch": "Rome",
            "period": "1420-01",
            "total_cash_inflows": "100.00",
            "total_cash_outflows": "25.00",
            "net_cash_movement": "75.00",
            "closing_cash_balance": "75.00",
        },
    ]
    (time_series_directory / "time_series_Florence.json").write_text(
        json.dumps(records[:2]), encoding="utf-8"
    )
    (time_series_directory / "time_series_Rome.json").write_text(
        json.dumps([records[2]]), encoding="utf-8"
    )

    repository = ArtifactRepository(tmp_path)

    assert repository.load_time_series() == [records[1], records[0], records[2]]
    assert repository.load_time_series(
        branch="Florence", start="1420-02", end="1420-02"
    ) == [records[0]]


def test_transaction_repository_filters_and_caches_validated_records(tmp_path):
    records = [
        {
            "id": 2,
            "date": date(1420, 2, 1),
            "branch": "Florence",
            "type": "withdrawal",
            "counterparty": "Silk Merchant",
            "description": "Customer withdrawal",
            "debit_amount": Decimal("50.00"),
        },
        {
            "id": 1,
            "date": date(1420, 1, 1),
            "branch": "Florence",
            "type": "deposit",
            "counterparty": "Wool Guild",
            "description": "Merchant deposit",
            "debit_amount": Decimal("100.00"),
        },
        {
            "id": 3,
            "date": date(1420, 1, 1),
            "branch": "Rome",
            "type": "deposit",
            "counterparty": "Banking House",
            "description": "Customer deposit",
            "debit_amount": Decimal("75.00"),
        },
    ]
    load_count = 0

    def load_transactions(_source_path):
        nonlocal load_count
        load_count += 1
        return SimpleNamespace(accepted=records, source_errors=[])

    repository = TransactionRepository(
        tmp_path / "transactions.csv",
        loader=load_transactions,
    )

    assert repository.load_transactions(
        branch="Florence",
        start=date(1420, 1, 1),
        end=date(1420, 1, 31),
        transaction_type="deposit",
    ) == [records[1]]
    assert repository.load_transactions(branch="Rome") == [records[2]]
    assert repository.load_transactions(branch="Florence", search="MERCHANT") == [
        records[1],
        records[0],
    ]
    assert load_count == 1


def test_kpi_endpoint_returns_filtered_repository_records(tmp_path):
    metrics_directory = tmp_path / "metrics"
    metrics_directory.mkdir()
    records = [
        {"branch": "Florence", "period": "1420-01", "net_income": "5.00"},
        {"branch": "Florence", "period": "1420-02", "net_income": "10.00"},
        {"branch": "Rome", "period": "1420-02", "net_income": "20.00"},
    ]
    for index, record in enumerate(records):
        (metrics_directory / f"metrics_{index}.json").write_text(
            json.dumps(record), encoding="utf-8"
        )

    app.dependency_overrides[get_repository] = lambda: ArtifactRepository(tmp_path)
    try:
        response = client.get(
            "/api/kpis",
            params={"branch": "Florence", "start": "1420-02", "end": "1420-02"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"count": 1, "items": [records[1]]}


def test_kpi_endpoint_validates_period_format():
    response = client.get(
        "/api/kpis",
        params={"branch": "Florence", "start": "1420-13"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_kpi_endpoint_returns_consistent_bad_range_error():
    response = client.get(
        "/api/kpis",
        params={
            "branch": "Florence",
            "start": "1420-02",
            "end": "1420-01",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "start period must not be after end period",
        }
    }


def test_alert_endpoint_returns_filtered_repository_records(tmp_path):
    alerts_directory = tmp_path / "alerts"
    alerts_directory.mkdir()
    records = [
        {
            "alert_id": 1,
            "branch": "Florence",
            "period": "1420-01",
            "severity": "HIGH",
        },
        {
            "alert_id": 2,
            "branch": "Florence",
            "period": "1420-02",
            "severity": "MEDIUM",
        },
    ]
    (alerts_directory / "alerts_Florence.json").write_text(
        json.dumps(records), encoding="utf-8"
    )

    app.dependency_overrides[get_repository] = lambda: ArtifactRepository(tmp_path)
    try:
        response = client.get(
            "/api/alerts",
            params={"branch": "Florence", "severity": "HIGH"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"count": 1, "items": [records[0]]}


def test_alert_endpoint_validates_severity():
    response = client.get(
        "/api/alerts",
        params={"branch": "Florence", "severity": "CRITICAL"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_expense_endpoint_returns_filtered_repository_rows(tmp_path):
    expenses_directory = tmp_path / "expenses"
    expenses_directory.mkdir()
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
            "branch": "Rome",
            "period": "1420-01",
            "category": "Rent Expense",
            "counterparty": "Landlord",
            "transaction_count": "1",
            "amount": "200.00",
        },
    ]
    path = expenses_directory / "expense_breakdown_fixture.csv"
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    app.dependency_overrides[get_repository] = lambda: ArtifactRepository(tmp_path)
    try:
        response = client.get(
            "/api/expenses",
            params={"branch": "Florence", "start": "1420-01", "end": "1420-01"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"count": 1, "items": [records[0]]}


def test_loan_endpoint_returns_filtered_activity_rows(tmp_path):
    loans_directory = tmp_path / "loans"
    loans_directory.mkdir()
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
            "branch": "Rome",
            "period": "1420-01",
            "counterparty": "Silk Merchant",
            "loans_issued": "500.00",
            "loans_repaid": "100.00",
            "interest_earned": "10.00",
            "net_loan_movement": "400.00",
        },
    ]
    path = loans_directory / "loan_portfolio_fixture.csv"
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    app.dependency_overrides[get_repository] = lambda: ArtifactRepository(tmp_path)
    try:
        response = client.get(
            "/api/loans",
            params={"branch": "Florence", "start": "1420-01", "end": "1420-01"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"count": 1, "items": [records[0]]}


def test_cashflow_endpoint_projects_monthly_kpi_fields(tmp_path):
    time_series_directory = tmp_path / "time_series"
    time_series_directory.mkdir()
    record = {
        "branch": "Florence",
        "period": "1420-01",
        "total_cash_inflows": "300.00",
        "total_cash_outflows": "100.00",
        "net_cash_movement": "200.00",
        "closing_cash_balance": "500.00",
        "net_income": "50.00",
    }
    (time_series_directory / "time_series_Florence.json").write_text(
        json.dumps([record]), encoding="utf-8"
    )

    app.dependency_overrides[get_repository] = lambda: ArtifactRepository(tmp_path)
    try:
        response = client.get(
            "/api/cashflow",
            params={"branch": "Florence", "granularity": "monthly"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "granularity": "monthly",
        "count": 1,
        "items": [
            {
                "branch": "Florence",
                "period": "1420-01",
                "total_cash_inflows": "300.00",
                "total_cash_outflows": "100.00",
                "net_cash_movement": "200.00",
                "closing_cash_balance": "500.00",
            }
        ],
    }


def test_cashflow_endpoint_rejects_unavailable_granularity():
    response = client.get(
        "/api/cashflow",
        params={"branch": "Florence", "granularity": "daily"},
    )

    assert response.status_code == 422


def test_transaction_endpoint_filters_paginates_and_serializes(tmp_path):
    records = [
        {
            "id": 1,
            "date": date(1420, 1, 1),
            "branch": "Florence",
            "type": "deposit",
            "debit_amount": Decimal("100.00"),
        },
        {
            "id": 2,
            "date": date(1420, 1, 2),
            "branch": "Florence",
            "type": "deposit",
            "debit_amount": Decimal("200.00"),
        },
        {
            "id": 3,
            "date": date(1420, 1, 3),
            "branch": "Florence",
            "type": "withdrawal",
            "debit_amount": Decimal("50.00"),
        },
    ]
    repository = TransactionRepository(
        tmp_path / "transactions.csv",
        loader=lambda _path: SimpleNamespace(accepted=records, source_errors=[]),
    )
    app.dependency_overrides[get_transaction_repository] = lambda: repository
    try:
        response = client.get(
            "/api/transactions",
            params={
                "branch": "Florence",
                "type": "deposit",
                "page": 2,
                "per_page": 1,
            },
        )
        sorted_response = client.get(
            "/api/transactions",
            params={
                "branch": "Florence",
                "type": "deposit",
                "sort_by": "debit_amount",
                "sort_order": "desc",
                "page": 1,
                "per_page": 1,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "page": 2,
        "per_page": 1,
        "total": 2,
        "total_pages": 2,
        "items": [
            {
                "id": 2,
                "date": "1420-01-02",
                "branch": "Florence",
                "type": "deposit",
                "debit_amount": "200.00",
            }
        ],
    }
    assert sorted_response.status_code == 200
    assert sorted_response.json()["items"][0]["id"] == 2


def test_transaction_endpoint_validates_pagination():
    response = client.get(
        "/api/transactions",
        params={"branch": "Florence", "page": 0, "per_page": 101},
    )

    assert response.status_code == 422


def test_transaction_endpoint_searches_counterparty_and_description(tmp_path):
    records = [
        {
            "id": 1,
            "date": date(1420, 1, 1),
            "branch": "Florence",
            "type": "deposit",
            "counterparty": "Wool Merchant",
            "description": "Customer deposit",
            "debit_amount": Decimal("100.00"),
        },
        {
            "id": 2,
            "date": date(1420, 1, 2),
            "branch": "Florence",
            "type": "withdrawal",
            "counterparty": "Banking House",
            "description": "Merchant withdrawal",
            "debit_amount": Decimal("50.00"),
        },
        {
            "id": 3,
            "date": date(1420, 1, 3),
            "branch": "Florence",
            "type": "deposit",
            "counterparty": "Cardinal",
            "description": "Customer deposit",
            "debit_amount": Decimal("75.00"),
        },
    ]
    repository = TransactionRepository(
        tmp_path / "transactions.csv",
        loader=lambda _path: SimpleNamespace(accepted=records, source_errors=[]),
    )
    app.dependency_overrides[get_transaction_repository] = lambda: repository
    try:
        response = client.get(
            "/api/transactions",
            params={"branch": "Florence", "search": "MERCHANT"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert [record["id"] for record in response.json()["items"]] == [1, 2]


def test_branch_endpoint_discovers_available_kpi_branches(tmp_path):
    metrics_directory = tmp_path / "metrics"
    metrics_directory.mkdir()
    records = [
        {"branch": "Rome", "period": "1420-01"},
        {"branch": "Florence", "period": "1420-01"},
        {"branch": "Florence", "period": "1420-02"},
    ]
    for index, record in enumerate(records):
        (metrics_directory / f"metrics_{index}.json").write_text(
            json.dumps(record), encoding="utf-8"
        )

    app.dependency_overrides[get_repository] = lambda: ArtifactRepository(tmp_path)
    try:
        response = client.get("/api/branches")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "count": 2,
        "items": ["Florence", "Rome"],
    }
