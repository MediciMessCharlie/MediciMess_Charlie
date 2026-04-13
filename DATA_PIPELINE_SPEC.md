# Branch Metrics Data Pipeline — Specification

## Overview

This document specifies the requirements for the **Branch Metrics Data Pipeline**, the back-end data engineering system that ingests raw ledger transactions, computes key financial and operational metrics, detects anomalies, and delivers clean, aggregated data to the Branch Operations Dashboard (see `BRANCH_OPS_UI_SPEC.md`).

This is a **specification** — not an implementation. It defines what must be analyzed, designed, and developed.

---

## 1. Purpose

The data pipeline serves two complementary goals:

1. **Operational reporting**: Transform raw double-entry journal entries into human-readable KPIs and trend data that a bank official can act on.
2. **Forensic analytics**: Apply statistical and rule-based methods to detect patterns that may indicate fraud, error, or mismanagement — without relying on manual inspection of thousands of individual transactions.

The pipeline must be auditable: every derived metric must be traceable back to the source transactions that produced it.

---

## 2. Data Sources

| Source | Format | Description |
|--------|--------|-------------|
| `medici_transactions.csv` | CSV | Raw transaction ledger (~80,000 rows) |
| `medici_transactions.json` | JSON | Same data in JSON format |
| Account master (future) | CSV/DB | Chart of accounts with account types |
| Budget data (future) | CSV | Monthly expense budgets per branch |
| User/role data | JSON | Branch assignment and access roles |

### 2.1 Input Schema

Each transaction record contains:

| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer | Unique transaction identifier |
| `date` | ISO Date | `YYYY-MM-DD` |
| `branch` | String | Branch name |
| `type` | String | Transaction category |
| `counterparty` | String | Name of external party |
| `description` | String | Free-text description |
| `debit_account` | String | Account debited |
| `debit_amount` | Float | Amount in florins |
| `credit_account` | String | Primary account credited |
| `credit_amount` | Float | Amount in florins |
| `credit_account_2` | String | Secondary credit account (optional) |
| `credit_amount_2` | Float | Secondary credit amount (optional) |
| `currency` | String | Currency code (typically `florin`) |

---

## 3. Pipeline Architecture

The pipeline is organized into three stages: **Ingestion**, **Transformation**, and **Serving**.

```
┌─────────────────────┐     ┌──────────────────────────┐     ┌────────────────────────┐
│   INGESTION LAYER   │────▶│  TRANSFORMATION LAYER     │────▶│    SERVING LAYER       │
│                     │     │                          │     │                        │
│ - Load CSV / JSON   │     │ - Validate & clean        │     │ - KPI aggregates       │
│ - Schema validation │     │ - Compute KPIs            │     │ - Trend time-series    │
│ - Deduplication     │     │ - Anomaly detection       │     │ - Alert records        │
│ - Type coercion     │     │ - Enrich with categories  │     │ - REST API / files     │
└─────────────────────┘     └──────────────────────────┘     └────────────────────────┘
```

---

## 4. Ingestion Layer Requirements

### 4.1 Data Loading
- Must support loading from both CSV and JSON formats.
- Must validate that all required fields are present and non-null for every record.
- Must coerce `date` to a Python `date` object and `debit_amount` / `credit_amount` to `Decimal`.
- Must reject (log and skip) any record where `debit_amount ≠ credit_amount + credit_amount_2`.

### 4.2 Deduplication
- If two records share the same `(date, branch, type, counterparty, debit_amount, credit_account)` tuple, they must be flagged as potential duplicates.
- Duplicates must **not** be silently discarded; they must be surfaced as alerts.

### 4.3 Incremental Loading
- The pipeline must support incremental loads (processing only records with `id` greater than the last processed `id`) to enable daily or hourly runs without reprocessing the entire dataset.

---

## 5. Transformation Layer Requirements

### 5.1 Data Cleaning and Enrichment

| Transformation | Description |
|----------------|-------------|
| Normalize branch names | Ensure consistent capitalization and no trailing whitespace |
| Derive `year` and `month` | Add computed columns from the `date` field |
| Derive `quarter` | Add `Q1`/`Q2`/`Q3`/`Q4` derived from `month` |
| Derive `account_type` | Infer account type (ASSET, LIABILITY, EXPENSE, REVENUE, EQUITY) from account name using the same logic as `medici-banking.py` |
| Derive `fiscal_year` | For Medici Bank, the fiscal year runs 1 January – 31 December |

### 5.2 KPI Computations

The pipeline must produce the following metrics, partitioned by `(branch, period)`:

#### Cash Position Metrics
| Metric | Formula |
|--------|---------|
| `total_cash_inflows` | Sum of `debit_amount` where `debit_account = 'Cash'` |
| `total_cash_outflows` | Sum of `credit_amount` where `credit_account = 'Cash'` |
| `net_cash_movement` | `total_cash_inflows - total_cash_outflows` |
| `closing_cash_balance` | Cumulative `net_cash_movement` from start of dataset to end of period |

#### Deposit and Withdrawal Metrics
| Metric | Formula |
|--------|---------|
| `total_deposits` | Sum of `debit_amount` where `type = 'deposit'` |
| `total_withdrawals` | Sum of `debit_amount` where `type = 'withdrawal'` |
| `deposit_count` | Count of transactions where `type = 'deposit'` |
| `withdrawal_count` | Count of transactions where `type = 'withdrawal'` |
| `avg_deposit_size` | `total_deposits / deposit_count` |
| `avg_withdrawal_size` | `total_withdrawals / withdrawal_count` |

#### Loan Portfolio Metrics
| Metric | Formula |
|--------|---------|
| `loans_issued` | Sum of `debit_amount` where `type = 'loan_issuance'` |
| `loans_repaid` | Sum of `credit_amount` where `type = 'loan_repayment'` and `credit_account = 'Loans Receivable'` |
| `interest_earned` | Sum of `credit_amount_2` where `type = 'loan_repayment'` |
| `loan_portfolio_balance` | Cumulative `loans_issued - loans_repaid` |
| `interest_yield` | `interest_earned / loans_repaid` (as percentage) |

#### Operating Expense Metrics
| Metric | Formula |
|--------|---------|
| `total_operating_expenses` | Sum of `debit_amount` where `type = 'operating_expense'` |
| `expenses_by_category` | Sum of `debit_amount` grouped by `debit_account` where `type = 'operating_expense'` |
| `expense_per_transaction` | `total_operating_expenses / transaction_count` |
| `top_payees_by_expense` | Ranked list of `counterparty` by total payments in the period |

#### Revenue Metrics
| Metric | Formula |
|--------|---------|
| `exchange_fee_revenue` | Sum of `credit_amount_2` where `type = 'bill_of_exchange'` |
| `interest_income` | Sum of `credit_amount_2` where `credit_account_2 = 'Interest Income'` |
| `trading_revenue` | Sum of `credit_amount` where `credit_account = 'Trading Revenue'` |
| `total_revenue` | Sum of all revenue-type credits |

#### Net Income
| Metric | Formula |
|--------|---------|
| `net_income` | `total_revenue - total_operating_expenses` |
| `net_income_margin` | `net_income / total_revenue` (as percentage) |

### 5.3 Anomaly Detection Module

The pipeline must implement the following anomaly-detection rules. Every detected anomaly must produce an alert record (see Section 5.4).

#### Rule A — Benford's Law Deviation
- **Applies to**: All `debit_amount` values in each `(branch, type)` group for the period
- **Method**: Compute the observed distribution of first significant digits (1–9) and compare to the theoretical Benford distribution using the Chi-squared test or Mean Absolute Deviation
- **Threshold**: Flag if MAD > 0.015 or chi-squared p-value < 0.05
- **Interpretation**: Constructed or manipulated amounts often fail Benford's Law; natural transactions typically conform

#### Rule B — Vendor Concentration
- **Applies to**: `type = 'operating_expense'` transactions
- **Method**: For each `(branch, period, debit_account)` group, compute each `counterparty`'s share of total spend
- **Threshold**: Flag if any single counterparty accounts for > 5% of the expense category within the period
- **Interpretation**: A disproportionate share paid to one vendor may indicate a ghost-vendor scheme

#### Rule C — Duplicate Transaction Detection
- **Applies to**: All transactions
- **Method**: For each pair of transactions in the same `(branch, month)` with matching `(type, counterparty, debit_amount)`, check whether the dates are within 3 calendar days
- **Threshold**: Flag any such pair
- **Interpretation**: Accidental or deliberate re-entry of the same transaction

#### Rule D — Round-Number Clustering
- **Applies to**: `type = 'operating_expense'` transactions
- **Method**: Compute the proportion of `debit_amount` values that are exact multiples of 50 within each `(branch, debit_account)` group
- **Threshold**: Flag if the proportion exceeds 30% (natural amounts rarely cluster on round numbers at this rate)
- **Interpretation**: Manually entered fraudulent amounts often use round numbers for simplicity

#### Rule E — Transaction Frequency Outlier (by Counterparty)
- **Applies to**: All transactions
- **Method**: Compute the transaction count per `(branch, counterparty, type)` tuple per month; flag counterparties whose monthly count exceeds mean + 3 standard deviations across all months
- **Threshold**: 3 standard deviations above mean
- **Interpretation**: Unusually frequent transactions with a single counterparty may indicate a structured fraud scheme

#### Rule F — Amount Below Reporting Threshold
- **Applies to**: All transactions
- **Method**: Flag any cluster of transactions with the same `(branch, counterparty)` where all amounts are below a notable threshold (e.g., 1,000 florins) but the aggregate over a 30-day window exceeds 10,000 florins
- **Interpretation**: Smurfing or structuring — deliberately keeping individual transactions below a notable threshold to avoid scrutiny

#### Rule G — New Counterparty with Immediate High Volume
- **Applies to**: All transactions
- **Method**: For each `counterparty` that appears for the first time in the dataset, compute total volume in the first 90 days
- **Threshold**: Flag if first-90-day volume > 3× the average 90-day volume of established counterparties in the same `(branch, type)`
- **Interpretation**: A newly introduced ghost vendor receiving large payments immediately is a fraud indicator

### 5.4 Alert Record Schema

Every anomaly detection rule that fires must produce an alert record:

| Field | Type | Description |
|-------|------|-------------|
| `alert_id` | Integer | Unique identifier |
| `rule` | String | Rule code (A through G) |
| `severity` | String | `LOW`, `MEDIUM`, or `HIGH` |
| `branch` | String | Affected branch |
| `period` | String | Period in which the anomaly was detected |
| `affected_transaction_ids` | List[Integer] | Transaction IDs involved |
| `counterparty` | String | Relevant counterparty (if applicable) |
| `metric_value` | Float | The computed value that triggered the rule |
| `threshold_value` | Float | The threshold that was exceeded |
| `description` | String | Human-readable description of the anomaly |
| `detected_at` | Timestamp | When the pipeline generated this alert |
| `status` | String | `OPEN`, `ACKNOWLEDGED`, or `RESOLVED` |

---

## 6. Serving Layer Requirements

### 6.1 Output Formats

The pipeline must produce the following output artifacts after each run:

| Artifact | Format | Description |
|----------|--------|-------------|
| `metrics_{branch}_{period}.json` | JSON | KPI summary for a branch/period |
| `time_series_{branch}.json` | JSON | Daily/weekly metric time series |
| `alerts_{branch}_{period}.json` | JSON | Anomaly alert records |
| `expense_breakdown_{branch}_{period}.csv` | CSV | Expense by category and counterparty |
| `loan_portfolio_{branch}_{period}.csv` | CSV | Open loans summary |

### 6.2 API Endpoints (if serving via API)

The pipeline results must be accessible via an HTTP API to support the dashboard frontend:

| Endpoint | Method | Parameters | Response |
|----------|--------|------------|----------|
| `/api/kpis` | GET | `branch`, `start`, `end` | KPI summary object |
| `/api/transactions` | GET | `branch`, `start`, `end`, `type`, `page`, `per_page` | Paginated transaction list |
| `/api/cashflow` | GET | `branch`, `start`, `end`, `granularity` | Time series data |
| `/api/loans` | GET | `branch`, `status` | Loan portfolio list |
| `/api/expenses` | GET | `branch`, `start`, `end` | Expense breakdown |
| `/api/alerts` | GET | `branch`, `start`, `end`, `severity` | Alert list |
| `/api/alerts/{id}/acknowledge` | POST | `user_id`, `note` | Update alert status |

---

## 7. Dashboard Metrics — Analytical Design

The following section defines what should be **visible to the banking official** and what analytical questions each metric is designed to answer.

### 7.1 "Is the branch financially healthy?"
- KPIs: Cash balance, Net income, Loan portfolio balance
- Trend: Month-over-month change in net income and cash

### 7.2 "Are we managing risk in our loan portfolio?"
- KPIs: Loans outstanding, Interest yield, Overdue loan count and value
- Trend: Loan issuance vs. repayment by quarter

### 7.3 "Are operating costs under control?"
- KPIs: Total operating expenses, Expenses by category, Expense ratio (expenses ÷ revenue)
- Trend: Monthly expense by category, stacked bar chart
- Alert: Any single vendor representing > 5% of a category

### 7.4 "Is there anything suspicious I should investigate?"
- Alerts panel: All open alerts sorted by severity
- Focus metrics: Benford's Law compliance score per account, vendor concentration index
- Drill-down: Click any alert to see the specific transactions

### 7.5 "How does this branch compare to others?"
- Cross-branch comparison (Head Auditor view): side-by-side KPI table for all branches
- Highlight outliers: branches whose expense ratios or loan yield deviate more than 2 standard deviations from the network average

---

## 8. Testing Requirements

### 8.1 Unit Tests
- All KPI computation functions must have unit tests with known input/output pairs
- Anomaly detection rules must be tested with synthetic data designed to trigger and not-trigger each rule
- Double-entry validation must be tested against deliberately unbalanced test records

### 8.2 Integration Tests
- End-to-end test: load the full `medici_transactions.csv`, run all transformations, verify all KPIs are non-null and within reasonable ranges
- Alert generation test: verify that the embezzlement transactions in the dataset (if present) are detected by at least Rules A, B, D, and E

### 8.3 Performance Tests
- Pipeline must process 80,000 transactions in under 60 seconds on commodity hardware
- API endpoint response time must be under 500 ms for any query over 80,000 records (with appropriate indexing)

---

## 9. Open Questions for Design Phase

1. Will the pipeline run as a batch job (nightly) or as a streaming processor (real-time)?
2. Should the anomaly detection thresholds be configurable via a config file or hard-coded constants?
3. What is the retention policy for historical alert records?
4. Should the pipeline write directly to the dashboard's database, or produce flat files consumed by the API?
5. Is there a requirement to support currencies other than florins (multi-currency support)?
6. Should the pipeline support backfill (reprocessing historical data when rules change)?

---

## 10. Technology Considerations (to be decided in design phase)

The implementation team should evaluate the following options:

- **Orchestration**: Apache Airflow, Prefect, or a simple cron-scheduled Python script
- **Data processing**: pandas, Polars, DuckDB, or PySpark (for very large scale)
- **Storage**: SQLite (small scale), PostgreSQL with TimescaleDB extension (time series), or Parquet files (analytical)
- **API framework**: FastAPI, Flask, or Django REST Framework
- **Statistical libraries**: scipy (chi-squared test), numpy (Benford's Law calculation)
- **Testing**: pytest with fixtures based on the existing `medici_transactions.csv`

---

## 11. Deliverables Expected from Development

1. Ingestion module with schema validation and deduplication
2. Transformation module with all KPI computations in Section 5.2
3. Anomaly detection module with all rules in Section 5.3
4. Serving layer producing all outputs in Section 6.1
5. REST API exposing all endpoints in Section 6.2
6. Test suite meeting requirements in Section 8
7. Pipeline documentation and runbook
8. Example Jupyter notebook demonstrating each KPI and anomaly detection rule on the historical dataset

---

## References

- `BRANCH_OPS_UI_SPEC.md` — companion UI specification
- `medici-banking.py` — core double-entry accounting engine
- `medici_transactions.csv` / `medici_transactions.json` — historical transaction dataset
- `TRANSACTION_DATA.md` — data schema and field descriptions
- Newcomb, S. (1881). "Note on the frequency of use of the different digits in natural numbers." *American Journal of Mathematics*, 4(1), 39–40. (Benford's Law original paper)
- de Roover, R. (1963). *The Rise and Decline of the Medici Bank*. Harvard University Press.
