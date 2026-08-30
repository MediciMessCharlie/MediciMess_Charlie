"""
alerts.py

Phase 4 anomaly and alert detection for MediciMess.

Evaluates validated transactions for suspicious or unusual patterns
and returns alerts as a list of dictionaries.
"""

from datetime import date
from decimal import Decimal

from analytics.alerts import (
    detect_benford_anomalies,
    detect_vendor_concentration,
    detect_duplicate_transactions,
    detect_round_number_clustering,
    detect_frequency_outliers,
    detect_structuring,
    detect_new_counterparty_high_volume,
    generate_alerts,
)

# =========================
# RULE A - BENFORD'S LAW
# =========================

# -------------------------
# Rule A Trigger Test
# -------------------------

benford_trigger_transactions = []

for i in range(1, 41):
    benford_trigger_transactions.append(
        {
            "id": i,
            "date": date(1420, 1, ((i - 1) % 28) + 1),
            "branch": "Florence",
            "type": "operating_expense",
            "counterparty": f"Vendor {i}",
            "debit_account": "Supplies",
            "debit_amount": Decimal("900.00"),
            "credit_account": "Cash",
            "credit_amount": Decimal("900.00"),
        }
    )

trigger_alerts = detect_benford_anomalies(
    benford_trigger_transactions
)

assert len(trigger_alerts) > 0
assert trigger_alerts[0]["rule"] == "A"
assert trigger_alerts[0]["branch"] == "Florence"
assert trigger_alerts[0]["period"] == "1420-01"
assert trigger_alerts[0]["metric_value"] > Decimal("0.015")


# -------------------------
# Rule A Non-Trigger Test
# -------------------------

benford_normal_transactions = []

benford_counts = {
    1: 301,
    2: 176,
    3: 125,
    4: 97,
    5: 79,
    6: 67,
    7: 58,
    8: 51,
    9: 46,
}

transaction_id = 1000

for digit, count in benford_counts.items():
    for _ in range(count):
        benford_normal_transactions.append(
            {
                "id": transaction_id,
                "date": date(
                    1420,
                    2,
                    ((transaction_id - 1000) % 28) + 1,
                ),
                "branch": "Florence",
                "type": "operating_expense",
                "counterparty": f"Vendor {transaction_id}",
                "debit_account": "Supplies",
                "debit_amount": Decimal(f"{digit}00.00"),
                "credit_account": "Cash",
                "credit_amount": Decimal(f"{digit}00.00"),
            }
        )

        transaction_id += 1

normal_alerts = detect_benford_anomalies(
    benford_normal_transactions
)

assert normal_alerts == []

print("Rule A Benford tests passed!")


# =========================
# RULE B - VENDOR CONCENTRATION
# =========================

# -------------------------
# Rule B Trigger Test
# -------------------------

vendor_trigger_transactions = [
    {
        "id": 2001,
        "date": date(1420, 3, 1),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor A",
        "debit_account": "Supplies",
        "debit_amount": Decimal("900.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("900.00"),
    },
    {
        "id": 2002,
        "date": date(1420, 3, 2),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor B",
        "debit_account": "Supplies",
        "debit_amount": Decimal("100.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("100.00"),
    },
]

vendor_alerts = detect_vendor_concentration(
    vendor_trigger_transactions
)

assert len(vendor_alerts) == 2

assert vendor_alerts[0]["rule"] == "B"
assert vendor_alerts[0]["branch"] == "Florence"
assert vendor_alerts[0]["period"] == "1420-03"

assert vendor_alerts[0]["metric_value"] == Decimal("90.00")
assert vendor_alerts[1]["metric_value"] == Decimal("10.00")


# -------------------------
# Rule B Non-Trigger Test
# -------------------------

vendor_normal_transactions = []

for i in range(20):
    vendor_normal_transactions.append(
        {
            "id": 3000 + i,
            "date": date(1420, 4, (i % 28) + 1),
            "branch": "Florence",
            "type": "operating_expense",
            "counterparty": f"Vendor {i}",
            "debit_account": "Supplies",
            "debit_amount": Decimal("50.00"),
            "credit_account": "Cash",
            "credit_amount": Decimal("50.00"),
        }
    )

vendor_normal_alerts = detect_vendor_concentration(
    vendor_normal_transactions
)

assert vendor_normal_alerts == []

print("Rule B vendor concentration tests passed!")

print("All Phase 4 alert tests passed!")

# =========================
# RULE C - DUPLICATE TRANSACTIONS
# =========================

duplicate_transactions = [
    {
        "id": 4001,
        "date": date(1420, 5, 1),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor A",
        "debit_account": "Supplies",
        "debit_amount": Decimal("500.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("500.00"),
    },
    {
        "id": 4002,
        "date": date(1420, 5, 3),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor A",
        "debit_account": "Supplies",
        "debit_amount": Decimal("500.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("500.00"),
    },
]

duplicate_alerts = detect_duplicate_transactions(duplicate_transactions)

assert len(duplicate_alerts) == 1
assert duplicate_alerts[0]["rule"] == "C"
assert duplicate_alerts[0]["affected_transaction_ids"] == [4001, 4002]

non_duplicate_transactions = [
    {
        "id": 4101,
        "date": date(1420, 6, 1),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor A",
        "debit_account": "Supplies",
        "debit_amount": Decimal("500.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("500.00"),
    },
    {
        "id": 4102,
        "date": date(1420, 6, 10),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor A",
        "debit_account": "Supplies",
        "debit_amount": Decimal("500.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("500.00"),
    },
]

non_duplicate_alerts = detect_duplicate_transactions(non_duplicate_transactions)

assert non_duplicate_alerts == []

print("Rule C duplicate transaction tests passed!")

# =========================
# RULE D - ROUND-NUMBER CLUSTERING
# =========================

round_number_trigger_transactions = [
    {
        "id": 5001,
        "date": date(1420, 7, 1),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor A",
        "debit_account": "Supplies",
        "debit_amount": Decimal("500.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("500.00"),
    },
    {
        "id": 5002,
        "date": date(1420, 7, 2),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor B",
        "debit_account": "Supplies",
        "debit_amount": Decimal("750.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("750.00"),
    },
    {
        "id": 5003,
        "date": date(1420, 7, 3),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor C",
        "debit_account": "Supplies",
        "debit_amount": Decimal("1000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("1000.00"),
    },
    {
        "id": 5004,
        "date": date(1420, 7, 4),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor D",
        "debit_account": "Supplies",
        "debit_amount": Decimal("523.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("523.00"),
    },
]

round_alerts = detect_round_number_clustering(
    round_number_trigger_transactions
)

assert len(round_alerts) == 1
assert round_alerts[0]["rule"] == "D"
assert round_alerts[0]["metric_value"] == Decimal("75.00")

round_number_normal_transactions = [
    {
        "id": 5101,
        "date": date(1420, 8, 1),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor A",
        "debit_account": "Supplies",
        "debit_amount": Decimal("523.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("523.00"),
    },
    {
        "id": 5102,
        "date": date(1420, 8, 2),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor B",
        "debit_account": "Supplies",
        "debit_amount": Decimal("781.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("781.00"),
    },
    {
        "id": 5103,
        "date": date(1420, 8, 3),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Vendor C",
        "debit_account": "Supplies",
        "debit_amount": Decimal("1047.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("1047.00"),
    },
]

normal_round_alerts = detect_round_number_clustering(
    round_number_normal_transactions
)

assert normal_round_alerts == []

print("Rule D round-number clustering tests passed!")

# =========================
# RULE E - TRANSACTION FREQUENCY OUTLIER
# =========================

frequency_trigger_transactions = []

transaction_id = 6000

# Normal activity: 1 transaction per month for 12 months
for month in range(1, 13):
    frequency_trigger_transactions.append(
        {
            "id": transaction_id,
            "date": date(1420, month, 1),
            "branch": "Florence",
            "type": "operating_expense",
            "counterparty": "Vendor A",
            "debit_account": "Supplies",
            "debit_amount": Decimal("100.00"),
            "credit_account": "Cash",
            "credit_amount": Decimal("100.00"),
        }
    )

    transaction_id += 1

# Large spike in January of the next year
for day in range(1, 21):
    frequency_trigger_transactions.append(
        {
            "id": transaction_id,
            "date": date(1421, 1, day),
            "branch": "Florence",
            "type": "operating_expense",
            "counterparty": "Vendor A",
            "debit_account": "Supplies",
            "debit_amount": Decimal("100.00"),
            "credit_account": "Cash",
            "credit_amount": Decimal("100.00"),
        }
    )

    transaction_id += 1

frequency_alerts = detect_frequency_outliers(
    frequency_trigger_transactions
)

assert len(frequency_alerts) == 1
assert frequency_alerts[0]["rule"] == "E"
assert frequency_alerts[0]["branch"] == "Florence"
assert frequency_alerts[0]["counterparty"] == "Vendor A"
assert frequency_alerts[0]["period"] == "1421-01"
assert frequency_alerts[0]["metric_value"] == Decimal("20")


# -------------------------
# Rule E Non-Trigger Test
# -------------------------

frequency_normal_transactions = []

transaction_id = 7000

for month in range(1, 13):
    for day in range(1, 3):
        frequency_normal_transactions.append(
            {
                "id": transaction_id,
                "date": date(1420, month, day),
                "branch": "Florence",
                "type": "operating_expense",
                "counterparty": "Vendor B",
                "debit_account": "Supplies",
                "debit_amount": Decimal("100.00"),
                "credit_account": "Cash",
                "credit_amount": Decimal("100.00"),
            }
        )

        transaction_id += 1

normal_frequency_alerts = detect_frequency_outliers(
    frequency_normal_transactions
)

assert normal_frequency_alerts == []

print("Rule E transaction frequency tests passed!")

# =========================
# RULE F - STRUCTURING
# =========================

structuring_trigger_transactions = []

for i in range(12):
    structuring_trigger_transactions.append(
        {
            "id": 8000 + i,
            "date": date(1420, 9, (i % 28) + 1),
            "branch": "Florence",
            "type": "deposit",
            "counterparty": "Merchant A",
            "debit_account": "Cash",
            "debit_amount": Decimal("900.00"),
            "credit_account": "Deposits Payable",
            "credit_amount": Decimal("900.00"),
        }
    )

structuring_alerts = detect_structuring(
    structuring_trigger_transactions
)

assert len(structuring_alerts) == 1
assert structuring_alerts[0]["rule"] == "F"
assert structuring_alerts[0]["branch"] == "Florence"
assert structuring_alerts[0]["counterparty"] == "Merchant A"
assert structuring_alerts[0]["period"] == "1420-09"
assert structuring_alerts[0]["metric_value"] == Decimal("10800.00")


# -------------------------
# Rule F Non-Trigger Test
# -------------------------

structuring_normal_transactions = []

for i in range(5):
    structuring_normal_transactions.append(
        {
            "id": 9000 + i,
            "date": date(1420, 10, i + 1),
            "branch": "Florence",
            "type": "deposit",
            "counterparty": "Merchant B",
            "debit_account": "Cash",
            "debit_amount": Decimal("900.00"),
            "credit_account": "Deposits Payable",
            "credit_amount": Decimal("900.00"),
        }
    )

normal_structuring_alerts = detect_structuring(
    structuring_normal_transactions
)

assert normal_structuring_alerts == []

print("Rule F structuring tests passed!")

# =========================
# RULE G - NEW COUNTERPARTY HIGH VOLUME
# =========================

new_counterparty_trigger_transactions = [
    {
        "id": 10001,
        "date": date(1420, 11, 1),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "New Vendor",
        "debit_account": "Supplies",
        "debit_amount": Decimal("6000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("6000.00"),
    },
    {
        "id": 10002,
        "date": date(1420, 11, 10),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "New Vendor",
        "debit_account": "Supplies",
        "debit_amount": Decimal("5000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("5000.00"),
    },
]

new_counterparty_alerts = detect_new_counterparty_high_volume(
    new_counterparty_trigger_transactions
)

assert len(new_counterparty_alerts) == 1
assert new_counterparty_alerts[0]["rule"] == "G"
assert new_counterparty_alerts[0]["branch"] == "Florence"
assert new_counterparty_alerts[0]["counterparty"] == "New Vendor"
assert new_counterparty_alerts[0]["period"] == "1420-11"
assert new_counterparty_alerts[0]["metric_value"] == Decimal("11000.00")


# -------------------------
# Rule G Non-Trigger Test
# -------------------------

new_counterparty_normal_transactions = [
    {
        "id": 10101,
        "date": date(1420, 12, 1),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Small Vendor",
        "debit_account": "Supplies",
        "debit_amount": Decimal("2000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("2000.00"),
    },
    {
        "id": 10102,
        "date": date(1420, 12, 10),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Small Vendor",
        "debit_account": "Supplies",
        "debit_amount": Decimal("1000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("1000.00"),
    },
]

normal_new_counterparty_alerts = (
    detect_new_counterparty_high_volume(
        new_counterparty_normal_transactions
    )
)

assert normal_new_counterparty_alerts == []

print("Rule G new counterparty high-volume tests passed!")

# =========================
# FULL PHASE 4 INTEGRATION TEST
# =========================

all_alert_test_transactions = (
    benford_trigger_transactions
    + vendor_trigger_transactions
    + duplicate_transactions
    + round_number_trigger_transactions
    + frequency_trigger_transactions
    + structuring_trigger_transactions
    + new_counterparty_trigger_transactions
)

all_alerts = generate_alerts(all_alert_test_transactions)

assert isinstance(all_alerts, list)
assert len(all_alerts) > 0

rules_found = {
    alert["rule"]
    for alert in all_alerts
}

for rule in ["A", "B", "C", "D", "E", "F", "G"]:
    assert rule in rules_found

for alert in all_alerts:
    assert "alert_id" in alert
    assert "rule" in alert
    assert "severity" in alert
    assert "branch" in alert
    assert "period" in alert
    assert "affected_transaction_ids" in alert
    assert "counterparty" in alert
    assert "metric_value" in alert
    assert "threshold_value" in alert
    assert "description" in alert
    assert "detected_at" in alert
    assert alert["status"] == "OPEN"

alert_ids = [
    alert["alert_id"]
    for alert in all_alerts
]

assert len(alert_ids) == len(set(alert_ids))

print("Full Phase 4 alert integration test passed!")