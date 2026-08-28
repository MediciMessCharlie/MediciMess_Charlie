"""
alerts.py
Phase 4 anomaly and alert detection for MediciMess.
Evaluates validated transactions and Phase 3 KPI results
for conditions that require review.
Returns alerts as a list of dictionaries.
"""
from datetime import datetime
from decimal import Decimal
from math import log10
from statistics import mean, pstdev


# -------------------------
# Alert Thresholds
# -------------------------

BENFORD_MAD_THRESHOLD = Decimal("0.015")
BENFORD_MIN_SAMPLE_SIZE = 30
VENDOR_CONCENTRATION_THRESHOLD = Decimal("5.00")
STRUCTURING_SINGLE_LIMIT = Decimal("1000.00")
STRUCTURING_TOTAL_LIMIT = Decimal("10000.00")


# -------------------------
# Shared Alert Structure
# -------------------------

def create_alert(
    alert_id,
    rule,
    severity,
    branch,
    period,
    transaction_ids,
    counterparty,
    metric_value,
    threshold_value,
    description,
):
    return {
        "alert_id": alert_id,
        "rule": rule,
        "severity": severity,
        "branch": branch,
        "period": period,
        "affected_transaction_ids": transaction_ids,
        "counterparty": counterparty,
        "metric_value": metric_value,
        "threshold_value": threshold_value,
        "description": description,
        "detected_at": datetime.now().isoformat(),
        "status": "OPEN",
    }


# =========================
# RULE A - BENFORD'S LAW
# =========================

def get_first_digit(amount):
    """Return the first non-zero digit of an amount."""
    amount = abs(Decimal(str(amount)))

    if amount == 0:
        return None

    text = format(amount, "f").replace(".", "")

    for char in text:
        if char != "0":
            return int(char)

    return None


def get_benford_distribution():
    """Return expected Benford first-digit proportions."""
    return {
        digit: Decimal(str(log10(1 + (1 / digit))))
        for digit in range(1, 10)
    }


def detect_benford_anomalies(transactions):
    """
    Rule A:
    Detect groups whose first-digit distribution significantly
    deviates from Benford's Law.

    Groups are based on branch, transaction type, and monthly period.
    """
    alerts = []
    groups = {}
    alert_id = 1
    expected = get_benford_distribution()

    for transaction in transactions:
        txn_date = transaction["date"]
        period = f"{txn_date.year}-{txn_date.month:02d}"

        key = (
            transaction["branch"],
            transaction["type"],
            period,
        )

        groups.setdefault(key, [])
        groups[key].append(transaction)

    for (branch, txn_type, period), group in groups.items():
        digit_counts = {digit: 0 for digit in range(1, 10)}
        transaction_ids = []

        for transaction in group:
            first_digit = get_first_digit(transaction["debit_amount"])

            if first_digit is not None:
                digit_counts[first_digit] += 1
                transaction_ids.append(transaction["id"])

        total_count = sum(digit_counts.values())

        if total_count < BENFORD_MIN_SAMPLE_SIZE:
            continue

        deviations = []

        for digit in range(1, 10):
            observed = Decimal(digit_counts[digit]) / Decimal(total_count)
            deviation = abs(observed - expected[digit])
            deviations.append(deviation)

        mad = sum(deviations, Decimal("0")) / Decimal("9")

        if mad > BENFORD_MAD_THRESHOLD:
            alerts.append(
                create_alert(
                    alert_id=alert_id,
                    rule="A",
                    severity="MEDIUM",
                    branch=branch,
                    period=period,
                    transaction_ids=transaction_ids,
                    counterparty=None,
                    metric_value=mad,
                    threshold_value=BENFORD_MAD_THRESHOLD,
                    description=(
                        f"Benford's Law deviation detected for "
                        f"{txn_type} transactions. MAD={mad:.4f}."
                    ),
                )
            )

            alert_id += 1

    return alerts


# =========================
# RULE B - VENDOR CONCENTRATION
# =========================

def detect_vendor_concentration(transactions):
    """
    Rule B:
    Detect operating-expense counterparties that account for
    more than 5% of spending within a branch, period, and category.
    """
    alerts = []
    groups = {}
    alert_id = 1

    for transaction in transactions:
        if transaction["type"] != "operating_expense":
            continue

        txn_date = transaction["date"]
        period = f"{txn_date.year}-{txn_date.month:02d}"

        key = (
            transaction["branch"],
            period,
            transaction["debit_account"],
        )

        groups.setdefault(key, [])
        groups[key].append(transaction)

    for (branch, period, category), group in groups.items():
        category_total = sum(
            (transaction["debit_amount"] for transaction in group),
            Decimal("0")
        )

        if category_total == 0:
            continue

        payees = {}

        for transaction in group:
            counterparty = transaction["counterparty"]

            payees.setdefault(
                counterparty,
                {
                    "amount": Decimal("0"),
                    "ids": [],
                }
            )

            payees[counterparty]["amount"] += transaction["debit_amount"]
            payees[counterparty]["ids"].append(transaction["id"])

        for counterparty, data in payees.items():
            share = (
                data["amount"] / category_total
            ) * Decimal("100")

            if share > VENDOR_CONCENTRATION_THRESHOLD:
                alerts.append(
                    create_alert(
                        alert_id=alert_id,
                        rule="B",
                        severity="HIGH",
                        branch=branch,
                        period=period,
                        transaction_ids=data["ids"],
                        counterparty=counterparty,
                        metric_value=share.quantize(Decimal("0.01")),
                        threshold_value=VENDOR_CONCENTRATION_THRESHOLD,
                        description=(
                            f"{counterparty} represents "
                            f"{share.quantize(Decimal('0.01'))}% "
                            f"of {category} expenses."
                        ),
                    )
                )

                alert_id += 1

    return alerts

"""
Rule C
Within the same branch and month, if two transactions 
have the same type, counterparty, and debit_amount, 
and their dates are within 3 calendar days, flag them.
"""
def detect_duplicate_transactions(transactions):
    alerts = []
    groups = {}
    alert_id = 1

    for transaction in transactions:
        txn_date = transaction["date"]
        period = f"{txn_date.year}-{txn_date.month:02d}"

        key = (
            transaction["branch"],
            period,
            transaction["type"],
            transaction["counterparty"],
            transaction["debit_amount"],
        )

        groups.setdefault(key, [])
        groups[key].append(transaction)

    for (branch, period, txn_type, counterparty, amount), group in groups.items():
        if len(group) < 2:
            continue

        sorted_group = sorted(group, key=lambda transaction: transaction["date"])

        for i in range(len(sorted_group) - 1):
            first = sorted_group[i]
            second = sorted_group[i + 1]

            date_difference = (second["date"] - first["date"]).days

            if date_difference <= 3:
                alerts.append(
                    create_alert(
                        alert_id=alert_id,
                        rule="C",
                        severity="MEDIUM",
                        branch=branch,
                        period=period,
                        transaction_ids=[first["id"], second["id"]],
                        counterparty=counterparty,
                        metric_value=amount,
                        threshold_value=Decimal("3"),
                        description=(
                            f"Possible duplicate {txn_type} transactions "
                            f"for {counterparty} within {date_difference} days."
                        ),
                    )
                )

                alert_id += 1

    return alerts

    """
    Rule D
    For operating_expense transactions, group by (branch, 
    debit_account) and calculate what percentage of 
    debit_amount values are exact multiples of 50. Flag 
    the group if that percentage is greater than 30%.
    """
def detect_round_number_clustering(transactions):
    alerts = []
    groups = {}
    alert_id = 1
    threshold = Decimal("30.00")

    for transaction in transactions:
        if transaction["type"] != "operating_expense":
            continue

        txn_date = transaction["date"]
        period = f"{txn_date.year}-{txn_date.month:02d}"

        key = (
            transaction["branch"],
            period,
            transaction["debit_account"],
        )

        groups.setdefault(key, [])
        groups[key].append(transaction)

    for (branch, period, category), group in groups.items():
        total_count = len(group)

        if total_count == 0:
            continue

        round_count = 0
        transaction_ids = []

        for transaction in group:
            amount = transaction["debit_amount"]

            if amount % Decimal("50") == 0:
                round_count += 1
                transaction_ids.append(transaction["id"])

        round_percentage = (
            Decimal(round_count) / Decimal(total_count)
        ) * Decimal("100")

        if round_percentage > threshold:
            alerts.append(
                create_alert(
                    alert_id=alert_id,
                    rule="D",
                    severity="MEDIUM",
                    branch=branch,
                    period=period,
                    transaction_ids=transaction_ids,
                    counterparty=None,
                    metric_value=round_percentage.quantize(Decimal("0.01")),
                    threshold_value=threshold,
                    description=(
                        f"{round_percentage.quantize(Decimal('0.01'))}% "
                        f"of {category} expenses are exact multiples of 50."
                    ),
                )
            )

            alert_id += 1

    return alerts
"""
Rulel E
For each (branch, counterparty, type), count how many 
transactions occur each month. Flag a month if its 
count is greater than the average monthly count + 3 s
tandard deviations.
"""
def detect_frequency_outliers(transactions):
    alerts = []
    groups = {}
    alert_id = 1

    for transaction in transactions:
        txn_date = transaction["date"]
        period = f"{txn_date.year}-{txn_date.month:02d}"

        key = (
            transaction["branch"],
            transaction["counterparty"],
            transaction["type"],
        )

        groups.setdefault(key, {})
        groups[key].setdefault(period, [])
        groups[key][period].append(transaction)

    for (branch, counterparty, txn_type), periods in groups.items():
        if len(periods) < 2:
            continue

        monthly_counts = [
            len(txns)
            for txns in periods.values()
        ]

        avg_count = mean(monthly_counts)
        std_dev = pstdev(monthly_counts)
        threshold = avg_count + (3 * std_dev)

        for period, period_transactions in periods.items():
            transaction_count = len(period_transactions)

            if transaction_count > threshold:
                alerts.append(
                    create_alert(
                        alert_id=alert_id,
                        rule="E",
                        severity="HIGH",
                        branch=branch,
                        period=period,
                        transaction_ids=[
                            transaction["id"]
                            for transaction in period_transactions
                        ],
                        counterparty=counterparty,
                        metric_value=Decimal(str(transaction_count)),
                        threshold_value=Decimal(str(threshold)).quantize(
                            Decimal("0.01")
                        ),
                        description=(
                            f"{counterparty} had {transaction_count} "
                            f"{txn_type} transactions in {period}, "
                            f"exceeding the frequency threshold of "
                            f"{threshold:.2f}."
                        ),
                    )
                )

                alert_id += 1

    return alerts

"""
Rule F
Detect a counterparty making multiple transactions 
below a single-transaction threshold that collectively 
exceed a larger threshold.
"""
def detect_structuring(transactions):
    alerts = []
    groups = {}
    alert_id = 1

    for transaction in transactions:
        amount = transaction["debit_amount"]

        if amount >= STRUCTURING_SINGLE_LIMIT:
            continue

        txn_date = transaction["date"]
        period = f"{txn_date.year}-{txn_date.month:02d}"

        key = (
            transaction["branch"],
            period,
            transaction["counterparty"],
            transaction["type"],
        )

        groups.setdefault(key, [])
        groups[key].append(transaction)

    for (branch, period, counterparty, txn_type), group in groups.items():
        total_amount = sum(
            (transaction["debit_amount"] for transaction in group),
            Decimal("0")
        )

        if total_amount > STRUCTURING_TOTAL_LIMIT:
            alerts.append(
                create_alert(
                    alert_id=alert_id,
                    rule="F",
                    severity="HIGH",
                    branch=branch,
                    period=period,
                    transaction_ids=[
                        transaction["id"]
                        for transaction in group
                    ],
                    counterparty=counterparty,
                    metric_value=total_amount,
                    threshold_value=STRUCTURING_TOTAL_LIMIT,
                    description=(
                        f"{counterparty} had multiple {txn_type} "
                        f"transactions below {STRUCTURING_SINGLE_LIMIT} "
                        f"totaling {total_amount} in {period}."
                    ),
                )
            )

            alert_id += 1

    return alerts

"""
Rule G
This rule looks for a counterparty that is new 
to a branch and then suddenly has unusually high 
transaction volume.
"""
def detect_new_counterparty_high_volume(transactions):
    alerts = []
    counterparty_history = {}
    alert_id = 1

    sorted_transactions = sorted(
        transactions,
        key=lambda transaction: transaction["date"]
    )

    for transaction in sorted_transactions:
        txn_date = transaction["date"]
        period = f"{txn_date.year}-{txn_date.month:02d}"

        key = (
            transaction["branch"],
            transaction["counterparty"],
        )

        counterparty_history.setdefault(key, {})
        counterparty_history[key].setdefault(period, [])
        counterparty_history[key][period].append(transaction)

    for (branch, counterparty), periods in counterparty_history.items():

        sorted_periods = sorted(periods)

        if not sorted_periods:
            continue

        first_period = sorted_periods[0]
        first_period_transactions = periods[first_period]

        total_amount = sum(
            (
                transaction["debit_amount"]
                for transaction in first_period_transactions
            ),
            Decimal("0")
        )

        transaction_count = len(first_period_transactions)

        # New counterparty with high first-month activity
        if total_amount > Decimal("10000.00"):
            alerts.append(
                create_alert(
                    alert_id=alert_id,
                    rule="G",
                    severity="HIGH",
                    branch=branch,
                    period=first_period,
                    transaction_ids=[
                        transaction["id"]
                        for transaction in first_period_transactions
                    ],
                    counterparty=counterparty,
                    metric_value=total_amount,
                    threshold_value=Decimal("10000.00"),
                    description=(
                        f"New counterparty {counterparty} had "
                        f"{transaction_count} transactions totaling "
                        f"{total_amount} during its first active period."
                    ),
                )
            )

            alert_id += 1

    return alerts

def generate_alerts(transactions):
    """
    Run all Phase 4 alert detection rules.

    Returns:
        list[dict]: All generated alerts.
    """

    alerts = []

    alerts.extend(detect_benford_anomalies(transactions))
    alerts.extend(detect_vendor_concentration(transactions))
    alerts.extend(detect_duplicate_transactions(transactions))
    alerts.extend(detect_round_number_clustering(transactions))
    alerts.extend(detect_frequency_outliers(transactions))
    alerts.extend(detect_structuring(transactions))
    alerts.extend(detect_new_counterparty_high_volume(transactions))

    # Give every alert a unique ID across the complete result.
    for alert_id, alert in enumerate(alerts, start=1):
        alert["alert_id"] = alert_id

    return alerts