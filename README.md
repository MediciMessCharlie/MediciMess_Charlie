# MediciMess

A Python implementation of double-entry bookkeeping inspired by the Medici banking dynasty of Renaissance Florence.

## Overview

MediciMess is an educational project that demonstrates the fundamental principles of double-entry accounting through a simulation of the Medici Bank's operations in 1397. The implementation uses florins as the currency in honor of the historical Medici banking dynasty.

This project showcases how double-entry accounting works - a system where every financial transaction affects at least two accounts, and the sum of debits must always equal the sum of credits.

## What is Double-Entry Accounting?

Double-entry accounting is a bookkeeping method that records each transaction twice - as both a debit and a credit. This system provides a complete picture of financial transactions and helps maintain the fundamental accounting equation:

```
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

## Features

- ✅ Complete double-entry accounting implementation
- ✅ Support for all five main account types
- ✅ Transaction validation (ensures debits equal credits)
- ✅ Trial Balance generation
- ✅ Balance Sheet reporting
- ✅ Income Statement reporting
- ✅ Decimal precision for accurate financial calculations
- ✅ Historical simulation of Medici Bank operations (1397)
- ✅ **80,000+ historical transactions dataset** (1390-1440) based on real events
- ✅ **Import/Export transaction data** in CSV and JSON formats
- ✅ **Branch Operations Dashboard UI Specification** for senior bank officials
- ✅ **Data Pipeline Specification** for metrics computation and anomaly detection
- ✅ **Hidden embezzlement scenario** for forensic data analysis exercises

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)

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

## Usage

The main script demonstrates a series of banking transactions from the year 1397:

1. **Initial Capitalization**: Giovanni de' Medici invests 10,000 florins
2. **Loan Issuance**: A 2,000 florin loan to a wool merchant
3. **Loan Repayment**: Partial repayment with interest (200 florins)
4. **Asset Purchase**: Acquisition of land for a new banking house (3,000 florins)
5. **Operating Expenses**: Quarterly wages for bank employees (800 florins)

### Example Output

When you run the script, you'll see:
- Detailed transaction logs showing debits and credits
- A Trial Balance verifying the books are balanced
- A Balance Sheet showing the financial position
- An Income Statement showing profitability

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

## Educational Value

This project is ideal for:
- Learning the fundamentals of double-entry accounting
- Understanding how banking systems track financial transactions
- Exploring the historical context of Renaissance banking
- Studying Python OOP design patterns for financial systems

## Historical Context

The Medici family dominated banking in Florence during the 15th century. They pioneered many modern banking practices, including:
- International banking networks
- Bills of exchange
- Double-entry bookkeeping
- Letters of credit

This simulation honors their legacy by implementing the same fundamental accounting principles they used to build one of history's greatest banking dynasties.

## Historical Transaction Dataset

This repository includes a dataset of **80,000+ historically-themed transactions** covering the period 1390-1440, based on actual events from the Medici Bank's operations:

- **Western Schism and Papal Banking** (1402-1420s)
- **Council of Constance** - Including the famous 35,000 florin ransom for Pope John XXIII (1415)
- **Florentine-Milanese Wars** (1390-1402, 1422-1426)
- **Wars in Lombardy** (1423-1454)
- **Alum trade** from papal monopoly mines
- Regular banking operations across 8 branch locations

### Using the Historical Data

```bash
# Generate the initial 20,000 transaction dataset
python3 generate_historical_data.py

# Expand to 80,000+ transactions and inject the embezzlement trail
python3 generate_additional_data.py

# Validate the generated data
python3 validate_transactions.py
```

For detailed information about the transaction data, see [TRANSACTION_DATA.md](TRANSACTION_DATA.md).

## Importing and Exporting Transaction Data

The Medici Bank ledger system supports importing and exporting large volumes of transaction data in both CSV and JSON formats. This makes it easy to:
- Backup your ledger data
- Transfer data between systems
- Analyze transactions in spreadsheets
- Load historical datasets

### Quick Start

```bash
# Run the import/export demonstration
python3 demo_import_export.py
```

This interactive demo will show you how to:
1. Export transactions to CSV and JSON files
2. Import transactions from CSV and JSON files
3. Import the full 80,000+ transaction historical dataset
4. Verify that all imported data maintains double-entry accounting principles

### API Usage

#### Exporting Transactions

```python
from medici_banking import Ledger, AccountType, TransactionEntry
from decimal import Decimal
from datetime import date

# Create a ledger with some transactions
ledger = Ledger("My Bank")
cash = ledger.create_account("Cash", AccountType.ASSET)
capital = ledger.create_account("Owner's Capital", AccountType.EQUITY)

ledger.record_transaction(
    date(2024, 1, 1),
    "Initial investment",
    TransactionEntry(cash, Decimal("10000.00")),
    TransactionEntry(capital, Decimal("10000.00"))
)

# Export to CSV
ledger.export_transactions_to_csv("my_transactions.csv")

# Export to JSON
ledger.export_transactions_to_json("my_transactions.json")
```

#### Importing Transactions

```python
# Create a new ledger
ledger = Ledger("Import Demo")

# Import from CSV (silent mode)
count = ledger.import_transactions_from_csv("my_transactions.csv")
print(f"Imported {count} transactions")

# Import from JSON (verbose mode - prints each transaction)
count = ledger.import_transactions_from_json("my_transactions.json", verbose=True)

# Verify the books are balanced
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
      {"account": "Cash", "account_type": "ASSET", "amount": "10000.00"}
    ],
    "credits": [
      {"account": "Owner's Capital", "account_type": "EQUITY", "amount": "10000.00"}
    ]
  }
]
```

### Features

- **Automatic Account Creation**: Accounts are automatically created during import if they don't exist
- **Account Type Inference**: For CSV imports, account types are inferred from account names
- **Transaction Validation**: All imported transactions are validated to ensure debits equal credits
- **Batch Processing**: Efficiently handles large datasets (tested with 80,000+ transactions)
- **Silent/Verbose Modes**: Control whether transactions are printed during import

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Zip Code Wilmington Core

## Advanced Lab Components

This repository includes three additional components that extend the project into more complex data engineering and analysis topics:

### Branch Operations Dashboard UI Specification

[`BRANCH_OPS_UI_SPEC.md`](BRANCH_OPS_UI_SPEC.md) specifies a web-based dashboard for senior Medici Bank officials. It defines:

- KPI panels (cash position, loan portfolio, net income, alerts)
- Transaction ledger view with search and filter
- Cash flow charts and trend views
- Anomaly and alert panel
- Role-based access control requirements
- Wireframe layout and color palette

This is a **specification document only** — it defines what to analyze, design, and build, not how.

### Data Pipeline Specification

[`DATA_PIPELINE_SPEC.md`](DATA_PIPELINE_SPEC.md) specifies the back-end data engineering pipeline that feeds the dashboard. It defines:

- Ingestion, transformation, and serving layers
- KPI computation formulas (cash, loans, expenses, revenue, net income)
- Seven anomaly-detection rules including Benford's Law, vendor concentration, duplicate detection, and round-number clustering
- Alert record schema
- REST API endpoint definitions
- Testing requirements and technology options

This is a **specification document only**.

### Forensic Data Analysis — Hidden Embezzlement Scenario

The `medici_transactions.csv` dataset contains a hidden embezzlement trail embedded within the Florence branch operating expenses (1420–1424). The scheme involves approximately 100,000 florins channelled through a fictitious supplier over five years.

Students are expected to:

1. Load the dataset using pandas or a similar tool
2. Apply forensic analysis techniques (Benford's Law, vendor concentration, frequency analysis) to identify the fraudulent transactions
3. Quantify the total amount and date range of the fraud
4. Recommend internal controls that would have prevented it

**For instructors**: See [`INSTRUCTOR_EMBEZZLEMENT_GUIDE.md`](INSTRUCTOR_EMBEZZLEMENT_GUIDE.md) for the full description of the crime, detection methods, discussion questions, and grading rubric. **Do not distribute this file to students before the exercise.**

Copyright (c) 2025 Zip Code Wilmington Core

## Contributing

This is an educational project. Feel free to fork and experiment with different transaction scenarios or extend the functionality to include more advanced accounting features.
