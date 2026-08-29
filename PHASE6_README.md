# Phase 6 — API and Branch Manager Dashboard

## Status

Phase 6A (FastAPI) and Phase 6B (Dash) are complete against the available data
contracts. Full-data integration is verified; the network view belongs to Phase 7.

## Architecture

The API reads precomputed analytics and validated transactions. It does not
recalculate KPIs or anomaly rules.

## Main files

- `api/app.py` and `api/repository.py` — HTTP routes and cached data access
- `dashboard/app.py` and `dashboard/client.py` — UI callbacks and API client
- `dashboard/assets/styles.css` — responsive Florentine theme
- `tests/test_api.py` and `tests/test_dashboard.py` — API and dashboard coverage

## Phase 6A API

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | API availability |
| `GET /api/branches` | Available branch discovery |
| `GET /api/kpis` | Monthly branch KPIs |
| `GET /api/transactions` | Filtered and paginated ledger |
| `GET /api/cashflow` | Monthly cash-flow series |
| `GET /api/loans` | Monthly loan activity |
| `GET /api/expenses` | Expense detail records |
| `GET /api/alerts` | Anomaly alerts |

The transaction endpoint supports branch/date/type filters, text search, safe
sorting, ascending or descending order, and pages of up to 100 records.

Financial values are serialized as strings to preserve decimal precision. API
errors use one predictable JSON envelope. Empty valid results return HTTP 200.

Artifact and transaction repositories are reused and cached. Branch queries scan
matching artifact files, which keeps full-data dropdown changes responsive.

## How a dashboard request works

1. The user selects a branch and reporting range in Dash.
2. A Dash callback calls the appropriate method in `dashboard/client.py`.
3. The client sends an HTTP GET request to FastAPI.
4. FastAPI validates filters and delegates reading to a repository.
5. The artifact repository reads Phase 5 output; the transaction repository uses
   the validated Phase 2 ingestion result.
6. FastAPI returns JSON, and Dash converts it into cards, charts, or tables.

This boundary keeps presentation code separate from financial calculations. It also
allows another frontend to reuse the API without importing dashboard code.

## Phase 6B Dashboard

- API-discovered branch selector with Florence preferred initially
- Global monthly period controls defaulting to the latest 12 months
- KPI cards with equivalent prior-year comparisons
- Modeled cash-position line chart, inflow/outflow bars, and fallback table
- Expense category chart and top-20 counterparty table
- Loan activity chart, counterparty issuance donut, and detail table
- Observable bills-of-exchange table with pagination
- Alert severity totals, filter, and read-only review table
- Searchable, sortable transaction ledger with filters and page navigation
- Responsive Florentine red, gold, parchment, and dark-brown palette

All panels react to the selected branch and period and retrieve data through
FastAPI. The browser never receives the complete 80,230-row transaction ledger.

## Key implementation decisions

- The system is GET-only because Phase 6 presents existing historical data.
- Branch names and reporting periods come from the API rather than hardcoded lists.
- `Decimal` is used before displaying or aggregating financial strings in Dash.
- Transaction and bill tables use server-side pagination for predictable loading.
- The default range is the latest 12 months, while all 51 years remain selectable.
- Repository caching makes repeated branch and filter requests effectively instant.
- Missing data produces visible empty states instead of callback failures.
- Unsupported loan and settlement fields are documented rather than synthesized.

## Run with full historical data

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Generate artifacts once:

```bash
python3 generate_serving_artifacts.py medici_transactions.csv \
  --output serving_outputs
```

Start FastAPI:

```bash
MEDICIMESS_ARTIFACT_DIRECTORY=serving_outputs \
MEDICIMESS_TRANSACTION_SOURCE=medici_transactions.csv \
uvicorn api.app:app --reload
```

Start Dash in another terminal:

```bash
MEDICIMESS_API_URL=http://127.0.0.1:8000 \
python3 -m dashboard.app
```

Open `http://127.0.0.1:8050`; API docs are at `http://127.0.0.1:8000/docs`.

## Using the dashboard

1. Select a branch; Florence is the initial default.
2. Select inclusive start and end months.
3. Review the KPI cards and prior-year direction indicators.
4. Use the cash, expense, loan, bill, and alert panels for operational detail.
5. Search or filter the validated ledger and move between 25-row pages.

The first transaction request validates and caches the source ledger, so it may take
slightly longer than later requests. Stop either development server with `Ctrl+C`.

## Full-data results

- 80,230 transactions accepted and 19,597 artifacts generated across nine branches
- Florence covers 612 months from 1390-01 through 1440-12
- Florence contains 1,813 loan rows, 1,166 expense rows, and 1,441 alerts
- Latest-year live checks returned 12 KPIs, 44 loan rows, 24 expense rows,
  27 alerts, 16 bills, and 456 transactions

## Verification

```bash
python3 -m pytest -q
```

- Full repository suite: 68 tests passed
- Dashboard suite: 19 tests passed
- Live full-data API and Dash requests returned HTTP 200
- Cached transaction requests completed in approximately 0.02 seconds
- `git diff --check` reported no whitespace errors

## Important limitations

- Modeled cash position starts from zero because no opening cash balance exists.
- Loan data has no loan IDs, due dates, borrower types, reliable status, or
  individual outstanding balances.
- Bills have no expected settlement dates, settlement status, or overdue days.
- Alerts are read-only because there is no authenticated write contract.
- Authentication, role restrictions, and the cross-branch network overview belong
  to Phase 7.

The dashboard exposes supported facts without inventing missing operational fields.

## Team handoff

Phase 6 gives the team a tested single-branch dashboard foundation. A teammate can
regenerate artifacts, start the two services, inspect FastAPI contracts in `/docs`,
and open Dash without running analytics manually.

Phase 7 should reuse the existing API client, styles, cards, charts, and branch
controls. Its main additions are the managing-director network comparison, branch
drill-down, authentication, and role-based branch access. Any future write action,
such as alert acknowledgement, should include a persisted audit trail with user ID
and timestamp rather than modifying the current read-only callbacks directly.
