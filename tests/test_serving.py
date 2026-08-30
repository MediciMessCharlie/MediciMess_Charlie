import csv
import json
from copy import deepcopy
from datetime import date
from decimal import Decimal

import pytest

from analytics.alerts import generate_alerts
from analytics.kpis import (
    calculate_expense_details,
    calculate_kpis,
    calculate_loan_details,
)
from serving import ServingContractError, write_serving_artifacts


def transaction(transaction_id, transaction_date, transaction_type, **changes):
    record = {
        "id": transaction_id,
        "date": transaction_date,
        "branch": "Florence",
        "type": transaction_type,
        "counterparty": "Merchant A",
        "description": transaction_type,
        "debit_account": "Cash",
        "debit_amount": Decimal("100.00"),
        "credit_account": "Revenue",
        "credit_amount": Decimal("100.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    }
    record.update(changes)
    return record


@pytest.fixture
def transactions():
    return [
        transaction(
            1, date(1420, 1, 2), "operating_expense",
            counterparty="Security Guild", debit_account="Security Expense",
            credit_account="Cash",
        ),
        transaction(
            2, date(1420, 1, 2), "operating_expense",
            counterparty="Security Guild", debit_account="Security Expense",
            credit_account="Cash",
        ),
        transaction(
            3, date(1420, 1, 5), "loan_issuance",
            counterparty="Wool Merchant", debit_account="Loans Receivable",
            debit_amount=Decimal("1000.00"), credit_account="Cash",
            credit_amount=Decimal("1000.00"),
        ),
        transaction(
            4, date(1420, 1, 20), "loan_repayment",
            counterparty="Wool Merchant", debit_amount=Decimal("220.00"),
            credit_account="Loans Receivable", credit_amount=Decimal("200.00"),
            credit_account_2="Interest Income", credit_amount_2=Decimal("20.00"),
        ),
        transaction(
            5, date(1420, 2, 1), "deposit",
            counterparty="Silk Merchant", credit_account="Deposits Payable",
        ),
    ]


def phase_outputs(transactions):
    return {
        "kpi_records": calculate_kpis(transactions),
        "alert_records": generate_alerts(transactions),
        "expense_details": calculate_expense_details(transactions),
        "loan_details": calculate_loan_details(transactions),
    }


def test_real_phase_outputs_generate_complete_artifact_set(tmp_path, transactions):
    manifest = write_serving_artifacts(
        **phase_outputs(transactions), output_directory=tmp_path
    )

    assert len(manifest.metric_files) == 2
    assert len(manifest.time_series_files) == 1
    assert len(manifest.alert_files) == 2
    assert len(manifest.expense_files) == 2
    assert len(manifest.loan_files) == 2
    assert len(manifest.all_files) == 9
    assert all(path.exists() for path in manifest.all_files)


def test_json_artifacts_preserve_decimal_precision_and_read_back(tmp_path, transactions):
    manifest = write_serving_artifacts(
        **phase_outputs(transactions), output_directory=tmp_path
    )

    january_metrics = json.loads(
        next(path for path in manifest.metric_files if "1420-01" in path.name)
        .read_text(encoding="utf-8")
    )
    time_series = json.loads(
        manifest.time_series_files[0].read_text(encoding="utf-8")
    )
    january_alerts = json.loads(
        next(path for path in manifest.alert_files if "1420-01" in path.name)
        .read_text(encoding="utf-8")
    )

    assert january_metrics["loans_issued"] == "1000.00"
    assert january_metrics["deposit_count"] == 0
    assert [record["period"] for record in time_series] == ["1420-01", "1420-02"]
    assert any(alert["rule"] == "C" for alert in january_alerts)
    assert isinstance(january_alerts[0]["metric_value"], str)


def test_csv_artifacts_use_phase_three_detail_contracts(tmp_path, transactions):
    manifest = write_serving_artifacts(
        **phase_outputs(transactions), output_directory=tmp_path
    )

    january_expense = next(
        path for path in manifest.expense_files if "1420-01" in path.name
    )
    january_loan = next(
        path for path in manifest.loan_files if "1420-01" in path.name
    )
    with january_expense.open(newline="", encoding="utf-8") as source:
        expenses = list(csv.DictReader(source))
    with january_loan.open(newline="", encoding="utf-8") as source:
        loans = list(csv.DictReader(source))

    assert expenses == [
        {
            "branch": "Florence",
            "period": "1420-01",
            "category": "Security Expense",
            "counterparty": "Security Guild",
            "transaction_count": "2",
            "amount": "200.00",
        }
    ]
    assert loans == [
        {
            "branch": "Florence",
            "period": "1420-01",
            "counterparty": "Wool Merchant",
            "loans_issued": "1000.00",
            "loans_repaid": "200.00",
            "interest_earned": "20.00",
            "net_loan_movement": "800.00",
        }
    ]


def test_empty_partition_artifacts_are_valid(tmp_path, transactions):
    manifest = write_serving_artifacts(
        **phase_outputs(transactions), output_directory=tmp_path
    )
    february_alerts = next(
        path for path in manifest.alert_files if "1420-02" in path.name
    )
    february_expenses = next(
        path for path in manifest.expense_files if "1420-02" in path.name
    )

    assert json.loads(february_alerts.read_text(encoding="utf-8")) == []
    with february_expenses.open(newline="", encoding="utf-8") as source:
        assert list(csv.DictReader(source)) == []


def test_invalid_decimal_is_rejected_before_any_files_are_written(tmp_path, transactions):
    outputs = phase_outputs(transactions)
    outputs["kpi_records"] = deepcopy(outputs["kpi_records"])
    outputs["kpi_records"][0]["net_income"] = 10.0

    with pytest.raises(ServingContractError, match="finite Decimal"):
        write_serving_artifacts(**outputs, output_directory=tmp_path)

    assert not list(tmp_path.rglob("*"))


def test_detail_without_matching_kpi_partition_is_rejected(tmp_path, transactions):
    outputs = phase_outputs(transactions)
    outputs["expense_details"] = deepcopy(outputs["expense_details"])
    outputs["expense_details"][0]["period"] = "1419-12"

    with pytest.raises(ServingContractError, match="no matching KPI"):
        write_serving_artifacts(**outputs, output_directory=tmp_path)


def test_duplicate_kpi_partition_is_rejected(tmp_path, transactions):
    outputs = phase_outputs(transactions)
    outputs["kpi_records"] = outputs["kpi_records"] + [outputs["kpi_records"][0]]

    with pytest.raises(ServingContractError, match="duplicate KPI"):
        write_serving_artifacts(**outputs, output_directory=tmp_path)


def test_rerun_atomically_replaces_existing_artifacts(tmp_path, transactions):
    outputs = phase_outputs(transactions)
    first = write_serving_artifacts(**outputs, output_directory=tmp_path)
    second = write_serving_artifacts(**outputs, output_directory=tmp_path)

    assert first.all_files == second.all_files
    assert not list(tmp_path.rglob("*.tmp"))
