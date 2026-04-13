# Branch Operations Dashboard — UI Specification

## Overview

This document specifies the requirements for a **Branch Operations Dashboard**, a web-based user interface for senior bank officials of the Medici Bank. The dashboard provides a real-time operational view of a single branch's financial health, transaction activity, and compliance posture.

This is a **specification** — not an implementation. It defines what must be analyzed, designed, and developed.

---

## 1. Purpose and User Roles

### Primary User: Senior Bank Official (Branch Supervisor)

The senior bank official is responsible for:
- Monitoring daily transaction volumes and cash positions
- Identifying anomalous or suspicious activity
- Reviewing loan portfolios and repayment status
- Overseeing operating expenses against budget
- Generating reports for the central ledger in Florence

### Secondary Users
- **Branch Manager**: Daily operational oversight
- **Head Auditor (Florence)**: Periodic audit review across all branches
- **Courier/Correspondent Clerk**: Input of bill-of-exchange data

---

## 2. Scope

The dashboard must cover the following operational domains for a single branch:

1. **Cash Position** — current cash balance and intraday movements
2. **Deposit & Withdrawal Activity** — customer account summaries
3. **Loan Portfolio** — outstanding loans, repayment schedules, overdue items
4. **Operating Expenses** — actuals vs. budget by category
5. **Bills of Exchange** — open items, settlement status
6. **Alerts & Anomalies** — flagged transactions requiring review
7. **Historical Trend Views** — period-over-period comparisons

---

## 3. Functional Requirements

### 3.1 Branch Selector and Date Range

- The user must be able to select which branch to view (Florence, Rome, Venice, Milan, Geneva, Bruges, London, Avignon, Constance).
- A date-range picker must allow filtering by day, week, month, quarter, or custom range.
- The selected branch and date range must propagate to all panels on the dashboard.

### 3.2 Key Performance Indicator (KPI) Panel

Displayed as summary cards at the top of the dashboard:

| KPI | Description |
|-----|-------------|
| **Current Cash Balance** | Sum of cash inflows minus outflows for the selected period |
| **Total Deposits** | Total florin value of new deposits |
| **Total Withdrawals** | Total florin value of withdrawals |
| **Loans Outstanding** | Sum of all open loan receivables |
| **Net Income (Period)** | Revenue minus expenses for selected period |
| **Overdue Loans** | Count and value of loans past due date |
| **Flagged Transactions** | Count of transactions flagged by anomaly detection |

All KPIs must show a delta (▲/▼) compared to the same period in the prior year.

### 3.3 Transaction Ledger View

- Paginated table of all transactions in the selected branch and date range
- Columns: `ID`, `Date`, `Type`, `Counterparty`, `Description`, `Debit Account`, `Debit Amount`, `Credit Account`, `Credit Amount`, `Status`
- Ability to sort by any column
- Full-text search across description and counterparty fields
- Ability to filter by transaction type (deposit, withdrawal, loan_issuance, etc.)
- Color-coding: green for completed/balanced, amber for pending, red for flagged
- Click-through to a detailed transaction view showing full double-entry journal entry

### 3.4 Cash Flow Chart

- A line chart showing daily/weekly cash balance over the selected period
- A bar chart showing inflows vs. outflows by day/week
- Overlay option: compare against the same period in the prior year
- Hover tooltip showing the individual transactions that make up each bar/point

### 3.5 Loan Portfolio Panel

- List of all open loans with: borrower name, date issued, principal, interest rate, current outstanding, due date, days overdue
- Visual indicator for loans approaching due date (within 30 days: amber; overdue: red)
- Donut chart: breakdown of loan portfolio by borrower type (merchant, noble, government)
- Ability to export the loan portfolio to CSV

### 3.6 Operating Expense Breakdown

- Stacked bar chart: actual expenses by category (Wages, Rent, Supplies, Courier Services, Security, Maintenance) per month
- Comparison line: budgeted expense per category (if budget data is available)
- Table: top 20 largest individual expense transactions in the period
- Highlight any single vendor that accounts for more than 5% of the expense category in the period

### 3.7 Bills of Exchange Panel

- Table of open bills: origin branch, destination branch, amount, issue date, expected settlement date, status
- Summary metric: average settlement time (days) vs. prior period
- Alert indicator if any bill is outstanding more than 30 days past expected settlement

### 3.8 Alerts and Anomaly Panel

The system must surface the following categories of anomalies:

| Alert Type | Trigger Condition |
|------------|-------------------|
| **Duplicate transaction** | Same amount, same counterparty, within 3 days |
| **Round-number clustering** | Unusual concentration of amounts ending in 00 or 50 |
| **Vendor concentration** | Single payee > 5% of operating expenses in the period |
| **Benford's Law deviation** | First-digit distribution of expense amounts deviates from Benford's Law |
| **After-hours entry** | Transactions entered outside normal business hours (if timestamp available) |
| **Overdue loan not flagged** | Loan past due date with no collection note |
| **Balance sheet imbalance** | Debits ≠ Credits for any posted transaction |

Each alert must show: alert type, affected transaction IDs, severity (Low/Medium/High), and a recommended action.

### 3.9 User Actions

- **Export Report**: Download the current dashboard view as a PDF or Excel workbook
- **Drill Down**: Navigate from a summary metric to the underlying transactions
- **Flag Transaction**: Mark a transaction for manual review and add a note
- **Acknowledge Alert**: Mark an alert as reviewed (with timestamp and user ID)
- **Print Ledger Page**: Print a formatted ledger page in the style of a Medici ledger folio (period-accurate layout option)

---

## 4. Non-Functional Requirements

### 4.1 Performance
- Dashboard must load within 3 seconds for datasets up to 80,000 transactions
- Filter and sort operations must complete within 1 second
- Charts must render within 2 seconds of applying a new date range

### 4.2 Usability
- Layout must be usable on a standard desktop monitor (1280×800 minimum)
- Navigation must require no more than 3 clicks to reach any function from the home screen
- All monetary amounts must be displayed in florins with 2 decimal places
- Dates must be displayed in the format `DD Month YYYY` (e.g., `29 May 1415`)

### 4.3 Security and Access Control
- Authentication required before accessing the dashboard
- Role-based access: Branch Supervisor can view all data for their assigned branch; Head Auditor can view any branch
- All actions (exports, flags, acknowledgements) must be logged with user ID and timestamp
- Sensitive data (full counterparty details) visible only to Supervisor role and above

### 4.4 Accessibility
- Minimum WCAG 2.1 AA compliance
- All charts must have text-based fallback tables for screen reader users

---

## 5. UI Layout — Wireframe Description

### 5.1 Top Navigation Bar
```
[Medici Bank Logo]   [Branch: Florence ▼]   [1 Jan 1420 – 31 Dec 1420 ▼]   [User: Giovanni]   [Logout]
```

### 5.2 Page Structure (single-page app)
```
┌──────────────────────────────────────────────────────────────┐
│  KPI CARDS: Cash | Deposits | Withdrawals | Loans | Net Inc  │
├────────────────────────┬─────────────────────────────────────┤
│   Cash Flow Chart      │   Alerts & Anomalies Panel           │
│   (line + bar)         │   (list of flagged items)            │
├────────────────────────┼─────────────────────────────────────┤
│   Loan Portfolio       │   Operating Expense Breakdown        │
│   (table + donut)      │   (stacked bar + top-20 table)       │
├────────────────────────┴─────────────────────────────────────┤
│   Transaction Ledger (paginated table, search, filter)        │
└──────────────────────────────────────────────────────────────┘
```

### 5.3 Color Palette
- Primary: deep Florentine red (`#8B1A1A`) and gold (`#B8860B`)
- Background: parchment (`#F5F0E8`)
- Alert colors: green (`#2E7D32`), amber (`#F57C00`), red (`#C62828`)
- Neutral text: dark brown (`#3E2723`)

---

## 6. Data Requirements

The following data must be available to the UI via an API or direct data pipeline connection:

- All transaction records for the selected branch and period
- Account balances (current and historical)
- Loan master data (borrower, rate, term, outstanding balance)
- Operating expense budget by category
- Alert and anomaly flags generated by the data pipeline
- User and role data for access control

---

## 7. Technology Considerations (to be decided in design phase)

The implementation team should evaluate the following options. No technology choice is mandated by this specification.

- **Frontend framework**: A modern JavaScript framework (React, Vue, Svelte) or a Python-based dashboard tool (Dash, Streamlit, Panel)
- **Charting library**: D3.js, Chart.js, Plotly, or Vega-Altair
- **API layer**: REST or GraphQL backed by the existing Python ledger codebase
- **Data store**: SQLite (for small deployments), PostgreSQL, or DuckDB (for analytical queries on large datasets)
- **Authentication**: OAuth 2.0 or session-based

---

## 8. Open Questions for Design Phase

1. Should the dashboard support real-time updates (WebSocket push) or periodic polling?
2. What is the authoritative source of truth for account balances — the CSV/JSON files or a database?
3. Should anomaly detection rules be configurable by the Head Auditor or hardcoded?
4. What constitutes the "budget" baseline for operating expense comparison?
5. Must the system support multiple simultaneous users accessing the same branch view?
6. Should historical trend data extend beyond the simulated 1390–1440 period (for extensibility)?

---

## 9. Deliverables Expected from Development

1. Functional dashboard web application matching the layout in Section 5
2. Backend API serving transaction data, KPIs, and alerts
3. Anomaly detection module implementing all rules in Section 3.8
4. Unit and integration tests for backend logic
5. User documentation (help text inline on dashboard, printable user guide)
6. Deployment runbook

---

## References

- `medici-banking.py` — core double-entry accounting engine
- `medici_transactions.csv` / `medici_transactions.json` — historical transaction dataset
- `TRANSACTION_DATA.md` — data schema and field descriptions
- `DATA_PIPELINE_SPEC.md` — companion specification for the data pipeline and metrics computation
