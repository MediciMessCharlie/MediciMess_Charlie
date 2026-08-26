import csv
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from ingestion.csv_ingestion import CSVSchemaError, ingest_csv
from validate_transactions import validate_transaction as shared_validator


FIELDS = [
    "id", "date", "branch", "type", "counterparty", "description",
    "debit_account", "debit_amount", "credit_account", "credit_amount",
    "credit_account_2", "credit_amount_2", "currency",
]


def valid_row(**changes):
    row = {
        "id": "1", "date": "1415-05-29", "branch": "Constance",
        "type": "ransom_payment", "counterparty": "Pope John XXIII",
        "description": "Ransom payment", "debit_account": "Ransom Expense",
        "debit_amount": "35000.00", "credit_account": "Cash",
        "credit_amount": "35000.00", "credit_account_2": "",
        "credit_amount_2": "", "currency": "florin",
    }
    row.update(changes)
    return row


class CSVIngestionTests(unittest.TestCase):
    def write_csv(self, rows, fields=FIELDS):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "transactions.csv"
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_valid_row_is_normalized_to_expected_types(self):
        result = ingest_csv(self.write_csv([valid_row()]))
        transaction = result.transactions[0]
        self.assertEqual((result.accepted_count, result.rejected_count), (1, 0))
        self.assertEqual(transaction.id, 1)
        self.assertEqual(transaction.date, date(1415, 5, 29))
        self.assertEqual(transaction.debit_amount, Decimal("35000.00"))
        self.assertIsNone(transaction.credit_amount_2)

    def test_records_pass_through_shared_validator(self):
        result = ingest_csv(
            self.write_csv([valid_row(), valid_row(id="2", credit_amount="1")]),
            validator=shared_validator,
        )
        self.assertEqual((result.accepted_count, result.rejected_count), (1, 1))
        self.assertIn("unbalanced", result.rejected_records[0].reason.lower())

    def test_missing_required_column_fails_before_import(self):
        fields = [field for field in FIELDS if field != "branch"]
        with self.assertRaisesRegex(CSVSchemaError, "branch"):
            ingest_csv(self.write_csv([], fields))

    def test_bad_rows_are_rejected_without_stopping_later_rows(self):
        rows = [
            valid_row(id="1", debit_amount="not-money"),
            valid_row(id="2"),
            valid_row(id="3", credit_amount="1.00"),
        ]
        result = ingest_csv(self.write_csv(rows))
        self.assertEqual((result.accepted_count, result.rejected_count), (1, 2))
        self.assertEqual(result.transactions[0].id, 2)

    def test_secondary_credit_balances_transaction(self):
        row = valid_row(
            credit_amount="34000", credit_account_2="Interest Income",
            credit_amount_2="1000",
        )
        result = ingest_csv(self.write_csv([row]))
        self.assertEqual(result.accepted_count, 1)

    def test_duplicates_are_flagged_but_not_discarded(self):
        result = ingest_csv(self.write_csv([valid_row(), valid_row(id="2")]))
        self.assertEqual(result.accepted_count, 2)
        self.assertEqual(result.duplicate_rows, [(2, 3)])

    def test_incremental_load_skips_old_ids(self):
        result = ingest_csv(
            self.write_csv([valid_row(id="4"), valid_row(id="6")]),
            last_processed_id=5,
        )
        self.assertEqual([item.id for item in result.transactions], [6])
        self.assertEqual(result.skipped_older_records, 1)


if __name__ == "__main__":
    unittest.main()
