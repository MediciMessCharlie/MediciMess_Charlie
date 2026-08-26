# Transaction Validation Test Results

## Purpose

Verify that the Phase 2 transaction validator correctly accepts valid
transactions and rejects invalid transaction data.

## Tests Performed

| Test | Test Data Change | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| Valid Transaction | No changes | Transaction accepted | Transaction accepted | PASS |
| Missing Required Field | Removed `branch` value | Missing required field error | Missing required field: branch | PASS |
| Invalid Transaction ID | Changed `id` to `ABC` | Invalid integer error | Transaction ID must be a valid integer | PASS |
| Invalid Date | Changed date to `banana` | Invalid date error | Invalid date format: banana | PASS |
| Invalid Amount | Changed `debit_amount` to `banana` | Invalid numeric amount error | Debit and credit amounts must be valid numbers | PASS |
| Secondary Credit Mismatch | Populated only one secondary credit field | Secondary credit consistency error | Secondary credit fields must be populated together | PASS |
| Unbalanced Transaction | Changed credit amount so debit != credit | Unbalanced transaction error | Transaction reported as unbalanced | PASS |

## Full Dataset Validation

The validator was also executed against the complete transaction datasets.

- CSV validation: PASS
- JSON validation: PASS
- All 80,230 transactions successfully passed validation.

## Conclusion

The transaction validator successfully detects missing required values,
invalid IDs, invalid dates, invalid numeric amounts, inconsistent secondary
credit fields, and unbalanced transactions.

Valid transaction records continue to pass validation for both CSV and JSON
input formats.



## TEST 1: required field must be populated

============================================================
VALIDATING CSV FILE: tests/test_transactions.csv
============================================================

✓ All required fields present
  Total fields: 13
  Fields: branch, counterparty, credit_account, credit_account_2, credit_amount, credit_amount_2, currency, date, debit_account, debit_amount, description, id, type

❌ Transaction 1 failed validation:
   - Missing required field: branch

Validation Results:
  Total transactions: 1
  Errors found: 1
  Total debits:  0.00 florins
  Total credits: 0.00 florins
  Difference:    0.00 florins

❌ Found 1 errors


———————————————————————————————————————————
## TEST 2: transaction ID must be a valid integer


============================================================
VALIDATING CSV FILE: tests/test_transactions.csv
============================================================

✓ All required fields present
  Total fields: 13
  Fields: branch, counterparty, credit_account, credit_account_2, credit_amount, credit_amount_2, currency, date, debit_account, debit_amount, description, id, type

❌ Transaction 1 failed validation:
   - Transaction ID must be a valid integer

Validation Results:
  Total transactions: 1
  Errors found: 1
  Total debits:  0.00 florins
  Total credits: 0.00 florins
  Difference:    0.00 florins

❌ Found 1 errors



———————————————————————————————————————————
## TEST 3: Dates must be valid

============================================================
VALIDATING CSV FILE: tests/test_transactions.csv
============================================================

✓ All required fields present
  Total fields: 13
  Fields: branch, counterparty, credit_account, credit_account_2, credit_amount, credit_amount_2, currency, date, debit_account, debit_amount, description, id, type

❌ Transaction 1 failed validation:
   - Invalid date format: banana

Validation Results:
  Total transactions: 1
  Errors found: 1
  Total debits:  0.00 florins
  Total credits: 0.00 florins
  Difference:    0.00 florins

❌ Found 1 errors


——————————————————
## TEST 4:  Debit/Credit amounts must be numeric

============================================================
VALIDATING CSV FILE: tests/test_transactions.csv
============================================================

✓ All required fields present
  Total fields: 13
  Fields: branch, counterparty, credit_account, credit_account_2, credit_amount, credit_amount_2, currency, date, debit_account, debit_amount, description, id, type

❌ Transaction 1 failed validation:
   - Debit and credit amounts must be valid numbers

Validation Results:
  Total transactions: 1
  Errors found: 1
  Total debits:  0.00 florins
  Total credits: 0.00 florins
  Difference:    0.00 florins

❌ Found 1 errors

——————————————————
## TEST 5

============================================================
VALIDATING CSV FILE: tests/test_transactions.csv
============================================================

✓ All required fields present
  Total fields: 13
  Fields: branch, counterparty, credit_account, credit_account_2, credit_amount, credit_amount_2, currency, date, debit_account, debit_amount, description, id, type

❌ Transaction 1 failed validation:
   - credit_account_2 and credit_amount_2 must be populated together

Validation Results:
  Total transactions: 1
  Errors found: 1
  Total debits:  0.00 florins
  Total credits: 0.00 florins
  Difference:    0.00 florins

❌ Found 1 errors


——————————————————
## TEST 6

============================================================
VALIDATING CSV FILE: tests/test_transactions.csv
============================================================

✓ All required fields present
  Total fields: 13
  Fields: branch, counterparty, credit_account, credit_account_2, credit_amount, credit_amount_2, currency, date, debit_account, debit_amount, description, id, type

❌ Transaction 1 failed validation:
   - credit_account_2 and credit_amount_2 must be populated together
   - Transaction is unbalanced: debit=82833.66, credit=82933.66

Validation Results:
  Total transactions: 1
  Errors found: 1
  Total debits:  0.00 florins
  Total credits: 0.00 florins
  Difference:    0.00 florins

❌ Found 1 errors


## Phase 2 Pipeline Integration Testing

### Purpose

Verify that the completed ingestion pipeline successfully integrates the CSV
ingestion module, JSON ingestion module, and shared transaction validator.

The pipeline was tested using both small test files and the complete transaction
datasets.

### Integration Tests

| Test | Expected Result | Actual Result | Status |
|---|---|---|---|
| CSV test file through pipeline | Valid record accepted | 1 accepted, 0 rejected | PASS |
| JSON test file through pipeline | Valid record accepted | 1 accepted, 0 rejected | PASS |
| Full CSV dataset through pipeline | All valid records accepted | 80,230 accepted, 0 rejected | PASS |
| Full JSON dataset through pipeline | All valid records accepted | 80,230 accepted, 0 rejected | PASS |

### Full Pipeline Results

Command:

```bash
python3 -m ingestion.pipeline
