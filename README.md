# MediciMess

A Python implementation of double-entry bookkeeping inspired by the Medici banking dynasty of Renaissance Florence.

## Overview

MediciMess is an educational project that demonstrates the fundamental principles of double-entry accounting through a simulation of the Medici Bank's operations. The implementation uses florins as the currency in honor of the historical Medici banking dynasty.

This project showcases how double-entry accounting works — a system where every financial transaction affects at least two accounts, and the sum of debits must always equal the sum of credits.

The project has also been extended with a data engineering pipeline that ingests and validates historical transaction data, calculates branch-level banking KPIs, and detects potentially anomalous financial activity.

Project documentation:

- [Pipeline documentation](docs/PIPELINE_DOCUMENTATION.md)
- [User guide](docs/USER_GUIDE.md)
- [Deployment/runbook](docs/DEPLOYMENT_RUNBOOK.md)
- [KPI and anomaly example notebook](notebooks/kpi_anomaly_rules_demo.ipynb)

---

## What is Double-Entry Accounting?

Double-entry accounting is a bookkeeping method that records each transaction twice — as both a debit and a credit. This system provides a complete picture of financial transactions and helps maintain the fundamental accounting equation:

```text
Assets = Liabilities + Equity
```

### The Five Main Account Types

1. **Assets**: Resources owned by the business (Cash, Accounts Receivable, Land, etc.)
2. **Liabilities**: Debts owed by the business (Loans, Accounts Payable, etc.)
3. **Equity**: Owner's interest in the business (Capital, Retained Earnings)
4. **Revenue**: Income earned by the business (Interest Income, Sales, etc.)
5. **Expenses**: Costs incurred by the business (Wages, Rent, etc.)

### Account Balance Rules

- **Assets and Expenses**: Increased by debits, decreased by credits
- **Liabilities, Equity, and Revenue**: Increased by credits, decreased by debits

---

## Features

- ✅ Complete double-entry accounting implementation
- ✅ Support for all five main account types
- ✅ Transaction validation to ensure debits equal credits
- ✅ Trial Balance generation
- ✅ Balance Sheet reporting
- ✅ Income Statement reporting
- ✅ Decimal precision for accurate financial calculations
- ✅ Historical simulation of Medici Bank operations
- ✅ **80,000+ historical transactions dataset** covering 1390–1440
- ✅ **Import/Export transaction data** in CSV and JSON formats
- ✅ **Reusable CSV and JSON ingestion pipeline**
- ✅ **Shared transaction validation**
- ✅ **KPI analytics pipeline** with branch/month financial metrics
- ✅ **Seven-rule anomaly detection engine** with structured alerts
- ✅ **Branch Operations Dashboard UI Specification** for senior bank officials
- ✅ **Data Pipeline Specification**
- ✅ **Hidden embezzlement scenario** for forensic data analysis exercises

---

## Requirements

- Python 3.6 or higher
- Core project functionality uses the Python standard library

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ZipCodeCore/MediciMess.git
cd MediciMess
```

2. Run the program:

```bash
python3 medici-banking.py
```

---

## Usage

The main script demonstrates a series of banking transactions:

1. **Initial Capitalization**: Giovanni de' Medici invests 10,000 florins
2. **Loan Issuance**: A 2,000 florin loan to a wool merchant
3. **Loan Repayment**: Partial repayment with interest
4. **Asset Purchase**: Acquisition of land for a new banking house
5. **Operating Expenses**: Quarterly wages for bank employees

### Example Output

When you run the script, you'll see:

- Detailed transaction logs showing debits and credits
- A Trial Balance verifying the books are balanced
- A Balance Sheet showing the financial position
- An Income Statement showing profitability

---

## Code Structure

### Core Classes

- **`AccountType`**: Enum defining the five account types
- **`Account`**: Represents a single financial account with debit/credit operations
- **`TransactionEntry`**: Represents a single entry in a transaction
- **`Transaction`**: Represents a complete double-entry transaction
- **`Ledger`**: The main ledger managing all accounts and transactions

### Key Methods

- `Account.debit()` / `Account.credit()`: Apply debits and credits to accounts
- `Transaction.is_balanced()`: Verify that debits equal credits
- `Transaction.post()`: Apply transaction to account balances
- `Ledger.record_transaction()`: Record and validate new transactions
- `Ledger.print_trial_balance()`: Generate trial balance report
- `Ledger.print_balance_sheet()`: Generate balance sheet
- `Ledger.print_income_statement()`: Generate income statement

### Data Engineering Components

```text
ingestion/
    csv_ingestion.py
    json_ingestion.py
    pipeline.py

analytics/
    account_types.py
    kpis.py
    alerts.py

tests/
    test_csv_ingestion.py
    test_json_ingestion.py
    test_validation.py
    test_kpis.py
    test_alerts.py
```

The implemented data flow is:

```text
CSV / JSON Transaction Data
          ↓
       Ingestion
          ↓
      Validation
          ↓
 Validated Transactions
          ↓
   KPI Calculations
          ↓
  Anomaly Detection
          ↓
 Dashboard / Reporting
```

---

## Educational Value

This project is ideal for:

- Learning the fundamentals of double-entry accounting
- Understanding how banking systems track financial transactions
- Exploring the historical context of Renaissance banking
- Studying Python OOP design patterns for financial systems
- Building reusable data ingestion pipelines
- Calculating financial KPIs from transaction data
- Applying anomaly detection to financial datasets
- Exploring forensic data analysis techniques

---

## Historical Context

The Medici family dominated banking in Florence during the 15th century. They pioneered many modern banking practices, including:

- International banking networks
- Bills of exchange
- Double-entry bookkeeping
- Letters of credit

This simulation honors their legacy by implementing the same fundamental accounting principles they used to build one of history's greatest banking dynasties.

---

## Historical Transaction Dataset

This repository includes a dataset of **80,000+ historically-themed transactions** covering the period 1390–1440, based on events from the Medici Bank's historical era.

The dataset includes activity related to:

- **Western Schism and Papal Banking** (1402–1420s)
- **Council of Constance**, including the 35,000 florin ransom for Pope John XXIII (1415)
- **Florentine-Milanese Wars** (1390–1402, 1422–1426)
- **Wars in Lombardy** (1423–1454)
- **Alum trade** from papal monopoly mines
- Regular banking operations across multiple branch locations

### Using the Historical Data

```bash
# Generate the initial 20,000 transaction dataset
python3 generate_historical_data.py

# Expand to 80,000+ transactions and inject the embezzlement trail
python3 generate_additional_data.py

# Validate the generated data
python3 validate_transactions.py
```

---

## Reusable Data Ingestion

The `ingestion` package provides reusable CSV and JSON ingestion for the shared transaction pipeline.

The ingestion process:

- Reads transaction records
- Converts IDs to integers
- Converts dates to Python date objects
- Converts monetary fields to `Decimal`
- Runs the shared transaction validator
- Separates accepted and rejected records
- Continues processing after malformed records
- Supports incremental processing
- Reports potential duplicates without silently removing them

### Running the Pipeline

```python
from ingestion.pipeline import run_pipeline

result = run_pipeline("medici_transactions.csv")

print(f"Accepted: {result.accepted_count}")
print(f"Rejected: {result.rejected_count}")
```

The complete dataset currently produces:

```text
Total records: 80,230
Accepted:      80,230
Rejected:      0
Skipped:       0
```

For detailed information about the transaction data, see `TRANSACTION_DATA.md`.

---

## Importing and Exporting Transaction Data

The Medici Bank ledger system supports importing and exporting transaction data in both CSV and JSON formats.

This can be used to:

- Backup ledger data
- Transfer data between systems
- Analyze transactions in spreadsheets
- Load historical datasets

### Quick Start

```bash
python3 demo_import_export.py
```

The demonstration shows how to:

1. Export transactions to CSV and JSON files
2. Import transactions from CSV and JSON files
3. Import the full historical transaction dataset
4. Verify that imported data maintains double-entry accounting principles

### Exporting Transactions

```python
from medici_banking import Ledger, AccountType, TransactionEntry
from decimal import Decimal
from datetime import date

ledger = Ledger("My Bank")

cash = ledger.create_account("Cash", AccountType.ASSET)
capital = ledger.create_account("Owner's Capital", AccountType.EQUITY)

ledger.record_transaction(
    date(2024, 1, 1),
    "Initial investment",
    TransactionEntry(cash, Decimal("10000.00")),
    TransactionEntry(capital, Decimal("10000.00"))
)

ledger.export_transactions_to_csv("my_transactions.csv")
ledger.export_transactions_to_json("my_transactions.json")
```

### Importing Transactions

```python
ledger = Ledger("Import Demo")

count = ledger.import_transactions_from_csv("my_transactions.csv")
print(f"Imported {count} transactions")

count = ledger.import_transactions_from_json(
    "my_transactions.json",
    verbose=True
)

ledger.print_trial_balance()
```

### File Formats

#### CSV Format

```csv
id,date,description,debit_account,debit_amount,credit_account,credit_amount,credit_account_2,credit_amount_2
1,2024-01-01,Initial investment,Cash,10000.00,Owner's Capital,10000.00,,
2,2024-01-15,Service revenue,Cash,1500.00,Service Revenue,1500.00,,
```

#### JSON Format

```json
[
  {
    "id": 1,
    "date": "2024-01-01",
    "description": "Initial investment",
    "debits": [
      {
        "account": "Cash",
        "account_type": "ASSET",
        "amount": "10000.00"
      }
    ],
    "credits": [
      {
        "account": "Owner's Capital",
        "account_type": "EQUITY",
        "amount": "10000.00"
      }
    ]
  }
]
```

### Import/Export Features

- **Automatic Account Creation**: Accounts are automatically created during import if they don't exist
- **Account Type Inference**: Account types can be inferred from account names
- **Transaction Validation**: Imported transactions are validated to ensure debits equal credits
- **Batch Processing**: Supports large transaction datasets
- **Silent/Verbose Modes**: Controls whether transactions are printed during import

---

# Data Engineering Pipeline Implementation

The original project includes specifications for a data engineering pipeline supporting the Branch Operations Dashboard.

The implemented pipeline now includes transaction ingestion and validation, KPI calculation, and anomaly detection.

---

## Phase 3 — KPI Calculations and Analytics

Phase 3 transforms validated transaction data into business-level banking metrics.

Transactions are enriched with time-period information and grouped by **branch and month** before KPI calculations are performed.

### Transaction Enrichment

Each validated transaction is enriched with:

- Branch
- Year
- Month
- Quarter
- Fiscal year
- Monthly period (`YYYY-MM`)

Transactions are grouped using:

```text
(branch, period)
```

This allows financial metrics to be calculated independently for each branch and reporting period.

### Cash Position Metrics

Phase 3 calculates:

- Total cash inflows
- Total cash outflows
- Net cash movement
- Closing cash balance

Closing cash balance is maintained as a running balance across reporting periods.

### Deposit and Withdrawal Metrics

Phase 3 calculates:

- Total deposits
- Total withdrawals
- Deposit count
- Withdrawal count
- Average deposit size
- Average withdrawal size

### Loan Portfolio Metrics

Phase 3 calculates:

- Loans issued
- Loans repaid
- Interest earned
- Loan portfolio balance
- Interest yield

Loan portfolio balance is maintained as a running balance across reporting periods.

### Operating Expense Metrics

Phase 3 calculates:

- Total operating expenses
- Expenses by category
- Expense per transaction
- Top payees by expense

### Revenue and Profitability Metrics

Revenue calculations include:

- Exchange fee revenue
- Interest income
- Trading revenue
- Total revenue
- Net income
- Net income margin

### Financial Precision

Financial calculations use Python `Decimal` values rather than floating-point values.

Average monetary KPIs and percentage-based metrics are rounded to two decimal places where appropriate.

### Phase 3 Output Contract

Phase 3 returns:

```text
list[dict]
```

Each dictionary represents one branch/month KPI record.

Example structure:

```python
{
    "branch": "Florence",
    "period": "1390-01",
    "total_cash_inflows": Decimal("542443.17"),
    "total_cash_outflows": Decimal("14715015.82"),
    "net_cash_movement": Decimal("-14172572.65"),
    "closing_cash_balance": Decimal("-14172572.65"),
    "total_deposits": Decimal("9619.39"),
    "total_withdrawals": Decimal("6143.14"),
    "deposit_count": 1,
    "withdrawal_count": 1,
    "loans_issued": Decimal("388418.23"),
    "loans_repaid": Decimal("66972.58"),
    "interest_yield": Decimal("10.00"),
    "total_operating_expenses": Decimal("2919.60"),
    "total_revenue": Decimal("465851.20"),
    "net_income": Decimal("462931.60"),
    "net_income_margin": Decimal("99.37")
}
```

### Phase 3 Full Dataset Results

Phase 3 was executed against the complete validated dataset.

```text
Source transactions:    80,230
Accepted transactions:  80,230
Rejected transactions:       0
KPI records generated:   4,897
```

The reduction from 80,230 transactions to 4,897 KPI records occurs because the transaction data is aggregated into branch/month reporting periods.

### Phase 3 Testing

Phase 3 includes tests for:

- Cash position metrics
- Deposits and withdrawals
- Loan portfolio metrics
- Operating expenses
- Revenue
- Net income
- Full KPI integration

All Phase 3 tests passed successfully.

---

## Phase 4 — Anomaly Detection and Alerts

Phase 4 analyzes validated transaction data for financial patterns that may require further review.

Seven anomaly detection rules were implemented.

---

### Rule A — Benford's Law

Rule A analyzes the first-digit distribution of transaction amounts by:

```text
branch + transaction type + monthly period
```

Mean Absolute Deviation (MAD) is calculated between the observed first-digit distribution and the expected Benford distribution.

Configuration:

```text
MAD threshold:        0.015
Minimum sample size: 30 transactions
```

#### Full Dataset Adjustment

Initial full-dataset testing generated **25,104 Rule A alerts**.

Inspection showed that Benford analysis was being performed on groups containing as few as two transactions. Groups this small do not provide a meaningful first-digit distribution.

A minimum sample size of **30 transactions** was therefore added before applying the Benford calculation.

After the adjustment:

```text
Rule A alerts before: 25,104
Rule A alerts after:     308
```

This reduced low-sample alerts while retaining groups with enough observations for meaningful analysis.

---

### Rule B — Vendor Concentration

Rule B analyzes operating expenses by:

```text
branch + period + expense category + counterparty
```

A counterparty is flagged when its share of an expense category exceeds:

```text
5%
```

The configured threshold is intentionally retained for downstream analysis rather than modifying it simply to reduce alert volume.

---

### Rule C — Duplicate Transactions

Rule C detects potential duplicate transactions within the same branch and monthly period.

Transactions are compared using:

- Transaction type
- Counterparty
- Debit amount
- Transaction date

Transactions matching the identifying fields and occurring within **three calendar days** are flagged as possible duplicates.

---

### Rule D — Round-Number Clustering

Rule D analyzes operating expenses for unusual concentrations of round-number amounts.

A transaction is considered a round-number transaction when its debit amount is an exact multiple of:

```text
50
```

A group is flagged when more than:

```text
30%
```

of its transactions meet the round-number condition.

---

### Rule E — Transaction Frequency Outliers

Rule E analyzes monthly transaction frequency for each:

```text
branch + counterparty + transaction type
```

A monthly transaction count is flagged when it exceeds:

```text
average monthly count + (3 × standard deviation)
```

This helps identify sudden increases in activity involving a counterparty.

---

### Rule F — Structuring / Below-Threshold Activity

Rule F identifies repeated transactions below a defined single-transaction threshold.

Configuration:

```text
Single transaction limit: 1,000
Aggregate limit:         10,000
```

Transactions are grouped by:

```text
branch + period + counterparty + transaction type
```

When multiple transactions remain below 1,000 individually but collectively exceed 10,000 during the period, the group is flagged.

---

### Rule G — New Counterparty High Volume

Rule G identifies new counterparties with unusually high activity during their first active period at a branch.

A new counterparty is flagged when first-period transaction volume exceeds:

```text
10,000
```

---

## Phase 4 Alert Output Contract

Phase 4 returns:

```text
list[dict]
```

Each alert contains:

```text
alert_id
rule
severity
branch
period
affected_transaction_ids
counterparty
metric_value
threshold_value
description
detected_at
status
```

New alerts are assigned:

```text
status = OPEN
```

Alert IDs are reassigned during full alert generation so each alert has a unique ID across all seven rules.

Example:

```python
{
    "alert_id": 1,
    "rule": "A",
    "severity": "MEDIUM",
    "branch": "Florence",
    "period": "1390-05",
    "affected_transaction_ids": [...],
    "counterparty": None,
    "metric_value": Decimal("0.0563"),
    "threshold_value": Decimal("0.015"),
    "description": "Benford's Law deviation detected...",
    "detected_at": "...",
    "status": "OPEN"
}
```

---

## Phase 4 Full Dataset Results

Phase 4 was executed against all **80,230 accepted transactions**.

| Rule | Detection | Alerts |
|---|---|---:|
| A | Benford's Law | 308 |
| B | Vendor Concentration | 9,011 |
| C | Duplicate Transactions | 0 |
| D | Round-Number Clustering | 25 |
| E | Transaction Frequency Outliers | 1,263 |
| F | Structuring | 0 |
| G | New Counterparty High Volume | 176 |
| **Total** | | **10,783** |

A zero-alert result does not indicate that a detection rule failed. Trigger and non-trigger tests verify that Rules C and F correctly generate alerts when their respective conditions are present.

Vendor concentration produced the largest number of alerts because the configured threshold is **5%**. The result is retained for downstream analysis rather than changing the threshold solely to reduce alert volume.

---

## Phase 4 Testing

Testing includes:

- Trigger tests for all seven anomaly rules
- Non-trigger tests
- Alert schema validation
- Unique alert ID validation
- Full Phase 4 integration testing
- Full-dataset execution

All Phase 4 alert tests passed successfully.

---

## Phase 5 — Serving Layer

Phase 5 consumes the completed Phase 3 KPI/detail records and Phase 4 alert
records. It validates, partitions, and writes the required serving artifacts
without recalculating financial metrics or anomaly rules.

Generate the sample artifact bundle:

```bash
python3 generate_serving_artifacts.py tests/test_transactions.json \
    --output sample_serving_outputs
```

Generate artifacts from the complete historical dataset:

```bash
python3 generate_serving_artifacts.py medici_transactions.csv \
    --output serving_outputs
```

See `PHASE5_SERVING_LAYER.md` for output layouts, serialization rules,
integration usage, loan-data limitations, testing, and the definition of done.

---

## Phase 6A — Dashboard REST API

Phase 6A provides read-only FastAPI access to the Phase 5 artifacts and the
validated transaction ledger. It does not recalculate KPIs or anomaly rules.

Install the API dependencies and start the development server:

```bash
python3 -m pip install -r requirements.txt
uvicorn api.app:app --reload
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Available endpoints:

```text
GET /health
GET /api/branches
GET /api/kpis
GET /api/transactions
GET /api/cashflow
GET /api/loans
GET /api/expenses
GET /api/alerts
```

The API uses `sample_serving_outputs` and `medici_transactions.csv` by
default. Point it at another generated artifact directory or transaction
source with:

```bash
MEDICIMESS_ARTIFACT_DIRECTORY=serving_outputs \
MEDICIMESS_TRANSACTION_SOURCE=medici_transactions.csv \
uvicorn api.app:app --reload
```

See `PHASE6_README.md` for endpoint examples, design explanations, current
data limitations, and the Phase 6 learning log.

## Phase 6B — Branch Manager Dashboard

Phase 6B adds the Dash branch-operations interface on top of the Phase 6A API.
It includes global branch/period controls, KPI comparisons, cash-flow charts,
loan and expense analysis, bills-of-exchange activity, anomaly review, and a
searchable, sortable, paginated transaction ledger.

Start Dash after starting FastAPI:

```bash
MEDICIMESS_API_URL=http://127.0.0.1:8000 \
python3 -m dashboard.app
```

Open `http://127.0.0.1:8050`. For the complete setup, full-data commands,
implemented features, verification results, and limitations, see
`PHASE6_README.md`.

---

## Advanced Lab Components

This repository includes additional components that extend the project into more complex data engineering and analysis topics.

### Branch Operations Dashboard UI Specification

`BRANCH_OPS_UI_SPEC.md` specifies a web-based dashboard for senior Medici Bank officials.

It defines:

- KPI panels for cash position, loan portfolio, net income, and alerts
- Transaction ledger view with search and filtering
- Cash flow charts and trend views
- Anomaly and alert panel
- Role-based access control requirements
- Wireframe layout and color palette

This is a **specification document** defining what the dashboard should provide.

### Data Pipeline Specification

`DATA_PIPELINE_SPEC.md` defines the back-end data engineering pipeline that feeds the dashboard.

It defines:

- Ingestion, transformation, and serving layers
- KPI computation formulas
- Cash, loan, expense, revenue, and net income metrics
- Seven anomaly-detection rules
- Alert record schema
- REST API endpoint definitions
- Testing requirements and technology options

The specification provides the requirements for the data pipeline. The KPI calculation and anomaly-detection portions have now been implemented as documented in **Phase 3** and **Phase 4** above.

### Data Contracts

`DATA_CONTRACTS.md` defines the handoff structures used between pipeline phases, including:

- Python return types
- KPI record structures
- Alert record structures
- Decimal handling
- Empty-result representation
- In-memory handoff expectations

These contracts provide a consistent interface for downstream phases.

### Forensic Data Analysis — Hidden Embezzlement Scenario

The `medici_transactions.csv` dataset contains a hidden embezzlement trail embedded within the Florence branch operating expenses during 1420–1424.

The scheme involves approximately 100,000 florins channelled through a fictitious supplier over five years.

Students are expected to:

1. Load and validate the transaction dataset
2. Apply forensic analysis techniques such as Benford's Law, vendor concentration, and frequency analysis
3. Identify potentially fraudulent transactions
4. Quantify the total amount and date range of suspicious activity
5. Recommend internal controls that could have prevented the activity

**For instructors:** See `INSTRUCTOR_EMBEZZLEMENT_GUIDE.md` for the full description of the scenario, detection methods, discussion questions, and grading rubric. **Do not distribute this file to students before the exercise.**

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

Copyright (c) 2025 Zip Code Wilmington Core

---

## Contributing

This is an educational project. Feel free to fork and experiment with different transaction scenarios or extend the functionality to include more advanced accounting, data engineering, analytics, and reporting features.
