"""
Transaction Data Validation Script

Validates that the generated historical transactions maintain proper
double-entry accounting principles and can be loaded into the Medici ledger.
"""

import csv
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime
from collections import defaultdict


REQUIRED_FIELDS = {
    "id",
    "date",
    "branch",
    "type",
    "counterparty",
    "description",
    "debit_account",
    "debit_amount",
    "credit_account",
    "credit_amount",
    "currency",
}


def validate_transaction(transaction: dict):
    """
    Validate one transaction record.

    Returns:
        tuple: (is_valid, errors)
    """

    errors = []

    # ---------------------------------------------------------
    # 1. Validate required fields
    # ---------------------------------------------------------

    for field in REQUIRED_FIELDS:
        value = transaction.get(field)

        if value is None or str(value).strip() == "":
            errors.append(f"Missing required field: {field}")

    # Stop here if required data is missing.
    # Other validation depends on these fields being present.
    if errors:
        return False, errors

    # ---------------------------------------------------------
    # 2. Validate transaction ID
    # ---------------------------------------------------------

    try:
        transaction_id = int(transaction["id"])

        if transaction_id <= 0:
            errors.append("Transaction ID must be greater than zero")

    except (ValueError, TypeError):
        errors.append("Transaction ID must be a valid integer")

    # ---------------------------------------------------------
    # 3. Validate date
    # ---------------------------------------------------------

    try:
        datetime.fromisoformat(str(transaction["date"]))

    except (ValueError, TypeError):
        errors.append(
            f"Invalid date format: {transaction['date']}"
        )

    # ---------------------------------------------------------
    # 4. Validate amounts
    # ---------------------------------------------------------

    try:
        debit_amount = Decimal(str(transaction["debit_amount"]))
        credit_amount = Decimal(str(transaction["credit_amount"]))

    except (InvalidOperation, ValueError, TypeError):
        errors.append("Debit and credit amounts must be valid numbers")
        return False, errors

    # ---------------------------------------------------------
    # 5. Validate secondary credit fields
    # ---------------------------------------------------------

    credit_account_2 = transaction.get("credit_account_2")
    credit_amount_2 = transaction.get("credit_amount_2")

    has_credit_account_2 = (
        credit_account_2 is not None
        and str(credit_account_2).strip() != ""
    )

    has_credit_amount_2 = (
        credit_amount_2 is not None
        and str(credit_amount_2).strip() != ""
    )

    # Both secondary fields must either be populated or blank.
    if has_credit_account_2 != has_credit_amount_2:
        errors.append(
            "credit_account_2 and credit_amount_2 must be populated together"
        )

    # Add secondary credit amount when present.
    if has_credit_amount_2:
        try:
            credit_amount += Decimal(str(credit_amount_2))

        except (InvalidOperation, ValueError, TypeError):
            errors.append(
                "credit_amount_2 must be a valid number"
            )

    # ---------------------------------------------------------
    # 6. Validate double-entry accounting
    # ---------------------------------------------------------

    tolerance = Decimal("0.000001")

    if abs(debit_amount - credit_amount) > tolerance:
        errors.append(
            f"Transaction is unbalanced: "
            f"debit={debit_amount}, credit={credit_amount}"
        )

    return len(errors) == 0, errors


def validate_csv_structure(filename: str) -> bool:
    """Validate the CSV file structure and transactions."""

    print(f"\n{'=' * 60}")
    print(f"VALIDATING CSV FILE: {filename}")
    print(f"{'=' * 60}\n")

    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                print("❌ CSV file does not contain a header")
                return False

            fieldnames = set(reader.fieldnames)

            # Check required CSV columns.
            missing_fields = REQUIRED_FIELDS - fieldnames

            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False

            print("✓ All required fields present")
            print(f"  Total fields: {len(fieldnames)}")
            print(
                f"  Fields: {', '.join(sorted(fieldnames))}\n"
            )

            transaction_count = 0
            error_count = 0
            total_debits = Decimal("0")
            total_credits = Decimal("0")

            for idx, row in enumerate(reader, 1):
                transaction_count += 1

                is_valid, errors = validate_transaction(row)

                if not is_valid:
                    print(
                        f"❌ Transaction {idx} failed validation:"
                    )

                    for error in errors:
                        print(f"   - {error}")

                    error_count += 1
                    continue

                # Totals are calculated only for valid records.
                debit_amount = Decimal(
                    str(row["debit_amount"])
                )

                credit_amount = Decimal(
                    str(row["credit_amount"])
                )

                if (
                    row.get("credit_amount_2") is not None
                    and str(
                        row.get("credit_amount_2")
                    ).strip() != ""
                ):
                    credit_amount += Decimal(
                        str(row["credit_amount_2"])
                    )

                total_debits += debit_amount
                total_credits += credit_amount

            print("\nValidation Results:")
            print(
                f"  Total transactions: {transaction_count}"
            )
            print(f"  Errors found: {error_count}")
            print(
                f"  Total debits:  "
                f"{total_debits:,.2f} florins"
            )
            print(
                f"  Total credits: "
                f"{total_credits:,.2f} florins"
            )
            print(
                f"  Difference:    "
                f"{abs(total_debits - total_credits):,.2f} florins"
            )

            if error_count == 0:
                print("\n✓ All transactions are valid!")
                return True

            print(f"\n❌ Found {error_count} errors")
            return False

    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return False

    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False


def analyze_transaction_distribution(filename: str):
    """Analyze the distribution of transactions."""

    print(f"\n{'=' * 60}")
    print("TRANSACTION DISTRIBUTION ANALYSIS")
    print(f"{'=' * 60}\n")

    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            by_type = defaultdict(int)
            by_branch = defaultdict(int)
            by_year = defaultdict(int)
            amounts_by_type = defaultdict(list)

            for row in reader:
                trans_type = row["type"]
                branch = row["branch"]
                year = row["date"][:4]
                amount = float(row["debit_amount"])

                by_type[trans_type] += 1
                by_branch[branch] += 1
                by_year[year] += 1
                amounts_by_type[trans_type].append(amount)

            print("Transactions by Type:")

            for t_type, count in sorted(
                by_type.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                avg_amount = (
                    sum(amounts_by_type[t_type])
                    / len(amounts_by_type[t_type])
                )

                print(
                    f"  {t_type:25s}: "
                    f"{count:5d} "
                    f"(avg: {avg_amount:>12,.2f} florins)"
                )

            print("\nTransactions by Branch:")

            for branch, count in sorted(
                by_branch.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                print(f"  {branch:15s}: {count:5d}")

            print("\nTransactions by Year (sample):")

            years_sample = sorted(by_year.items())[:10]

            for year, count in years_sample:
                print(f"  {year}: {count:5d}")

            print(
                f"  ... ({len(by_year)} total years)"
            )

    except Exception as e:
        print(f"❌ Error analyzing distribution: {e}")


def check_historical_events(filename: str):
    """Check for specific historical events in the data."""

    print(f"\n{'=' * 60}")
    print("HISTORICAL EVENT VERIFICATION")
    print(f"{'=' * 60}\n")

    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            events_found = {
                "ransom": False,
                "papal_deposits": 0,
                "war_financing": 0,
                "alum_trade": 0,
                "bills_of_exchange": 0,
            }

            for row in reader:
                trans_type = row["type"]

                if (
                    "ransom" in trans_type.lower()
                    or "John XXIII"
                    in row.get("description", "")
                ):
                    events_found["ransom"] = True

                    print(
                        "✓ Found Council of Constance Ransom:"
                    )
                    print(f"  Date: {row['date']}")
                    print(
                        f"  Amount: "
                        f"{row['debit_amount']} florins"
                    )
                    print(
                        f"  Description: "
                        f"{row['description']}\n"
                    )

                if (
                    trans_type == "deposit"
                    and row["branch"] == "Rome"
                ):
                    events_found["papal_deposits"] += 1

                elif trans_type == "war_financing":
                    events_found["war_financing"] += 1

                elif trans_type == "alum_trade":
                    events_found["alum_trade"] += 1

                elif trans_type == "bill_of_exchange":
                    events_found["bills_of_exchange"] += 1

            print("Historical Event Coverage:")

            print(
                f"  {'Council of Constance Ransom:':<35} "
                f"{'✓ Found' if events_found['ransom'] else '❌ Missing'}"
            )

            print(
                f"  {'Papal deposits (Rome branch):':<35} "
                f"{events_found['papal_deposits']:>6} transactions"
            )

            print(
                f"  {'War financing operations:':<35} "
                f"{events_found['war_financing']:>6} transactions"
            )

            print(
                f"  {'Alum trade (papal monopoly):':<35} "
                f"{events_found['alum_trade']:>6} transactions"
            )

            print(
                f"  {'Bills of exchange (innovation):':<35} "
                f"{events_found['bills_of_exchange']:>6} transactions"
            )

            return events_found

    except Exception as e:
        print(f"❌ Error checking historical events: {e}")
        return None


def validate_json_structure(filename: str) -> bool:
    """Validate JSON structure and transaction records."""

    print(f"\n{'=' * 60}")
    print(f"VALIDATING JSON FILE: {filename}")
    print(f"{'=' * 60}\n")

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(
                "❌ JSON should contain a list of transactions"
            )
            return False

        print("✓ Valid JSON structure")
        print(f"  Total transactions: {len(data)}")

        transaction_count = 0
        error_count = 0

        for idx, transaction in enumerate(data, 1):
            transaction_count += 1

            if not isinstance(transaction, dict):
                print(
                    f"❌ JSON transaction {idx} "
                    f"is not an object"
                )
                error_count += 1
                continue

            is_valid, errors = validate_transaction(
                transaction
            )

            if not is_valid:
                print(
                    f"❌ JSON transaction {idx} "
                    f"failed validation:"
                )

                for error in errors:
                    print(f"   - {error}")

                error_count += 1

        print("\nJSON Validation Results:")
        print(
            f"  Total transactions: {transaction_count}"
        )
        print(f"  Errors found: {error_count}")

        if error_count == 0:
            print(
                "\n✓ All JSON transactions are valid!"
            )
            return True

        print(
            f"\n❌ Found {error_count} JSON errors"
        )
        return False

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False

    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return False

    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False


def main():
    """Main validation function."""

    print("\n" + "=" * 60)
    print("MEDICI BANK TRANSACTION DATA VALIDATION")
    print("=" * 60)

    csv_valid = validate_csv_structure(
        "medici_transactions.csv"
    )

    json_valid = validate_json_structure(
        "medici_transactions.json"
    )

    analyze_transaction_distribution(
        "medici_transactions.csv"
    )

    check_historical_events(
        "medici_transactions.csv"
    )

    print(f"\n{'=' * 60}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 60}")

    print(
        f"CSV Validation:  "
        f"{'✓ PASSED' if csv_valid else '❌ FAILED'}"
    )

    print(
        f"JSON Validation: "
        f"{'✓ PASSED' if json_valid else '❌ FAILED'}"
    )

    if csv_valid and json_valid:
        print(
            "\n✓ All validations passed! "
            "Data is ready for use."
        )
        return 0

    print(
        "\n❌ Some validations failed. "
        "Please review errors above."
    )
    return 1


if __name__ == "__main__":
    exit(main())