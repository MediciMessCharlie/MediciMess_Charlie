# MediciMess REST API Reference

## Overview

The MediciMess API is a read-only FastAPI service for the branch and
Managing Director dashboards. It serves validated Phase 5 artifacts and a
validated transaction ledger. It does not calculate KPIs or anomaly alerts on
request and does not provide write, acknowledgement, user-management, or audit
endpoints.

Default local base URL:

```text
http://127.0.0.1:8000
```

Runtime-generated documentation:

- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`
- OpenAPI 3 schema: `GET /openapi.json`

## Start the API

From the repository root:

```bash
MEDICIMESS_ARTIFACT_DIRECTORY=serving_outputs \
MEDICIMESS_TRANSACTION_SOURCE=medici_transactions.csv \
uvicorn api.app:app --host 127.0.0.1 --port 8000
```

| Environment variable | Purpose | Default |
| --- | --- | --- |
| `MEDICIMESS_ARTIFACT_DIRECTORY` | Root containing Phase 5 artifact directories | `sample_serving_outputs` |
| `MEDICIMESS_TRANSACTION_SOURCE` | CSV or JSON source for transaction queries | `medici_transactions.csv` |

Paths are resolved by the API process. Use absolute paths when running under a
service manager.

## Conventions

### Formats and ordering

- Monthly periods use `YYYY-MM`, for example `1420-03`.
- Transaction dates use ISO `YYYY-MM-DD`.
- `start` and `end` are inclusive.
- Financial amounts and percentages are JSON strings, such as `"1250.50"`, to
  preserve decimal precision. Clients should parse them with a decimal library,
  not binary floating point.
- Counts, IDs, and pagination metadata are JSON integers.
- Empty result collections are `[]` with a count of `0`; they are not errors.
- KPI, cash-flow, expense, loan, and alert records use deterministic branch/period
  ordering. Transactions use the requested sort.

### Authentication and transport

The REST API currently has no authentication middleware. Dashboard login and
role checks protect dashboard routes but do not protect direct API calls. Bind the
demonstration API to localhost or a trusted network only. Production use requires
TLS, API authentication/authorization, rate limiting, and appropriate network
controls.

### Common list envelope

Most collection endpoints return:

```json
{
  "count": 2,
  "items": []
}
```

The transaction endpoint uses a pagination envelope, and the network endpoint
uses a comparison object described below.

## Endpoint summary

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Process availability |
| GET | `/api/branches` | Discover available branches |
| GET | `/api/kpis` | Monthly KPI records |
| GET | `/api/alerts` | Anomaly alerts |
| GET | `/api/network/summary` | Cross-branch comparison and outliers |
| GET | `/api/expenses` | Expense detail |
| GET | `/api/loans` | Observable loan activity |
| GET | `/api/cashflow` | Chart-ready monthly cash flow |
| GET | `/api/transactions` | Filtered, sorted, paginated ledger |

## `GET /health`

Confirms that the FastAPI process can answer HTTP requests. It does not validate
every artifact, source file, or downstream dashboard.

```bash
curl http://127.0.0.1:8000/health
```

```json
{
  "status": "ok",
  "service": "medicimess-api"
}
```

## `GET /api/branches`

Discovers branch names from KPI artifacts. No query parameters.

```bash
curl http://127.0.0.1:8000/api/branches
```

```json
{
  "count": 2,
  "items": ["Florence", "Rome"]
}
```

## `GET /api/kpis`

Returns one precomputed KPI dictionary per populated branch/month.

### Query parameters

| Name | Type | Required | Rules |
| --- | --- | --- | --- |
| `branch` | string | yes | Non-empty, exact branch name |
| `start` | string | no | Inclusive `YYYY-MM` |
| `end` | string | no | Inclusive `YYYY-MM`; must not precede `start` |

```bash
curl 'http://127.0.0.1:8000/api/kpis?branch=Florence&start=1420-01&end=1420-03'
```

Each item contains:

| Fields | JSON type |
| --- | --- |
| `branch`, `period` | string |
| `deposit_count`, `withdrawal_count` | integer |
| `expenses_by_category` | object mapping category to decimal string |
| `top_payees_by_expense` | array of `{counterparty, amount}` |
| all other fields below | decimal string |

Financial fields:

```text
total_cash_inflows, total_cash_outflows, net_cash_movement,
closing_cash_balance, total_deposits, total_withdrawals,
avg_deposit_size, avg_withdrawal_size, loans_issued, loans_repaid,
interest_earned, loan_portfolio_balance, interest_yield,
total_operating_expenses, expense_per_transaction,
exchange_fee_revenue, interest_income, trading_revenue,
total_revenue, net_income, net_income_margin
```

Abbreviated response:

```json
{
  "count": 1,
  "items": [
    {
      "branch": "Florence",
      "period": "1420-01",
      "total_cash_inflows": "12500.00",
      "total_cash_outflows": "8200.00",
      "net_cash_movement": "4300.00",
      "closing_cash_balance": "94000.00",
      "deposit_count": 4,
      "withdrawal_count": 2,
      "expenses_by_category": {"Wages Expense": "600.00"},
      "top_payees_by_expense": [
        {"counterparty": "Workers Guild", "amount": "600.00"}
      ]
    }
  ]
}
```

The abbreviated example omits other required KPI financial fields for readability;
real responses contain the complete contract defined in `DATA_CONTRACTS.md`.

## `GET /api/alerts`

Returns precomputed anomaly alerts.

### Query parameters

| Name | Type | Required | Rules |
| --- | --- | --- | --- |
| `branch` | string | yes | Non-empty, exact branch name |
| `start` | string | no | Inclusive `YYYY-MM` |
| `end` | string | no | Inclusive `YYYY-MM`; must not precede `start` |
| `severity` | enum | no | `LOW`, `MEDIUM`, or `HIGH` |

```bash
curl 'http://127.0.0.1:8000/api/alerts?branch=Rome&severity=HIGH'
```

```json
{
  "count": 1,
  "items": [
    {
      "alert_id": 42,
      "rule": "G",
      "severity": "HIGH",
      "branch": "Rome",
      "period": "1420-01",
      "affected_transaction_ids": [101, 104],
      "counterparty": "Example Merchant",
      "metric_value": "12500.00",
      "threshold_value": "10000.00",
      "description": "New counterparty exceeded first-period volume threshold.",
      "detected_at": "2026-08-30T12:00:00+00:00",
      "status": "OPEN"
    }
  ]
}
```

Rule codes are A Benford deviation, B vendor concentration, C possible duplicate,
D round-number clustering, E frequency outlier, F structuring, and G new
high-volume counterparty. Alerts are review signals, not findings of misconduct.

## `GET /api/network/summary`

Returns Managing Director cross-branch comparisons, a network total, and
statistical outliers.

### Query parameters

| Name | Type | Required | Rules |
| --- | --- | --- | --- |
| `start` | string | no | Inclusive `YYYY-MM` |
| `end` | string | no | Inclusive `YYYY-MM`; must not precede `start` |

```bash
curl 'http://127.0.0.1:8000/api/network/summary?start=1420-01&end=1420-12'
```

```json
{
  "branches": [
    {
      "branch": "Florence",
      "modeled_cash_position": "94000.00",
      "net_income": "6500.00",
      "loan_portfolio_balance": "22500.00",
      "open_alerts": 3,
      "expense_ratio": "18.25",
      "loan_yield": "4.50",
      "total_operating_expenses": "2400.00",
      "total_revenue": "13150.68",
      "interest_earned": "225.00",
      "loans_repaid": "5000.00"
    }
  ],
  "totals": {
    "branch": "Network Total",
    "modeled_cash_position": "94000.00",
    "net_income": "6500.00",
    "loan_portfolio_balance": "22500.00",
    "open_alerts": 3,
    "expense_ratio": "18.25",
    "loan_yield": "4.50",
    "total_operating_expenses": "2400.00",
    "total_revenue": "13150.68",
    "interest_earned": "225.00",
    "loans_repaid": "5000.00"
  },
  "outliers": [
    {
      "branch": "Bruges",
      "metric": "expense_ratio",
      "value": "34.20",
      "network_average": "18.10",
      "standard_deviation": "6.25",
      "direction": "HIGH"
    }
  ]
}
```

Snapshot balances use the latest selected month; activity fields cover the entire
selected range. Outliers apply only to `expense_ratio` and `loan_yield` and require
a deviation greater than two population standard deviations.

## `GET /api/expenses`

Returns precomputed monthly expense detail.

### Query parameters

`branch` is required. Optional `start` and `end` use the same inclusive `YYYY-MM`
rules as `/api/kpis`.

```bash
curl 'http://127.0.0.1:8000/api/expenses?branch=Florence&start=1420-01'
```

```json
{
  "count": 1,
  "items": [
    {
      "branch": "Florence",
      "period": "1420-01",
      "category": "Wages Expense",
      "counterparty": "Workers Guild",
      "transaction_count": "2",
      "amount": "600.00"
    }
  ]
}
```

Because these records are read from CSV artifacts, all item fields—including
`transaction_count`—are returned as JSON strings.

## `GET /api/loans`

Returns observable loan activity, not individual loan status or balances.

### Query parameters

`branch` is required. Optional `start` and `end` use inclusive `YYYY-MM`.

```bash
curl 'http://127.0.0.1:8000/api/loans?branch=Florence&end=1420-12'
```

```json
{
  "count": 1,
  "items": [
    {
      "branch": "Florence",
      "period": "1420-01",
      "counterparty": "Wool Merchant",
      "loans_issued": "1000.00",
      "loans_repaid": "200.00",
      "interest_earned": "20.00",
      "net_loan_movement": "800.00"
    }
  ]
}
```

All item fields are strings because the source artifact is CSV.

## `GET /api/cashflow`

Returns chart-ready monthly cash-flow fields from each branch time series.

### Query parameters

| Name | Type | Required | Rules/default |
| --- | --- | --- | --- |
| `branch` | string | yes | Non-empty, exact branch name |
| `start` | string | no | Inclusive `YYYY-MM` |
| `end` | string | no | Inclusive `YYYY-MM` |
| `granularity` | enum | no | Only `monthly`; default `monthly` |

```bash
curl 'http://127.0.0.1:8000/api/cashflow?branch=Rome&granularity=monthly'
```

```json
{
  "granularity": "monthly",
  "count": 1,
  "items": [
    {
      "branch": "Rome",
      "period": "1420-01",
      "total_cash_inflows": "1000.00",
      "total_cash_outflows": "250.00",
      "net_cash_movement": "750.00",
      "closing_cash_balance": "750.00"
    }
  ]
}
```

## `GET /api/transactions`

Returns accepted transactions from the shared ingestion and validation path.
The source is loaded once and cached for the API process.

### Query parameters

| Name | Type | Required | Rules/default |
| --- | --- | --- | --- |
| `branch` | string | yes | Non-empty, exact match |
| `start` | date | no | Inclusive `YYYY-MM-DD` |
| `end` | date | no | Inclusive `YYYY-MM-DD`; must not precede `start` |
| `type` | string | no | Exact transaction-type match |
| `search` | string | no | Non-empty, case-insensitive substring of counterparty or description |
| `sort_by` | enum | no | `id`, `date`, `type`, `counterparty`, `debit_amount`, or `credit_amount`; default `date` |
| `sort_order` | enum | no | `asc` or `desc`; default `asc` |
| `page` | integer | no | At least 1; default 1 |
| `per_page` | integer | no | 1–100; default 25 |

The query name is `type`, not the internal Python parameter name
`transaction_type`.

```bash
curl 'http://127.0.0.1:8000/api/transactions?branch=Florence&type=deposit&search=wool&sort_by=date&sort_order=desc&page=1&per_page=25'
```

```json
{
  "page": 1,
  "per_page": 25,
  "total": 1,
  "total_pages": 1,
  "items": [
    {
      "id": 101,
      "date": "1420-01-15",
      "branch": "Florence",
      "type": "deposit",
      "counterparty": "Wool Guild",
      "description": "Merchant deposit",
      "debit_account": "Cash",
      "debit_amount": "500.00",
      "credit_account": "Customer Deposits",
      "credit_amount": "500.00",
      "credit_account_2": null,
      "credit_amount_2": null,
      "currency": "FLR"
    }
  ]
}
```

Requesting a page beyond `total_pages` returns an empty `items` array while
retaining the requested page and actual totals.

## Error responses

Application and validation errors use a shared envelope.

### `400 BAD_REQUEST`

Used for repository/data-access rules such as a reversed range or missing artifact
directory.

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "start period must not be after end period"
  }
}
```

### `422 VALIDATION_ERROR`

Used when FastAPI rejects a missing required parameter, malformed date/month,
unsupported enum, or out-of-range page size.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": []
  }
}
```

The `details` array contains FastAPI field locations, messages, submitted values,
and validation types. The global handler also defines `NOT_FOUND` for explicit
404 errors and `DATA_UNAVAILABLE` for explicit 503 errors, although current read
routes normally report configured repository failures as `400`.

An unexpected malformed artifact can still produce a generic server error. Treat
that as an operational fault, remove the release from service, retain logs, and
follow the regeneration/rollback procedure in `docs/DEPLOYMENT_RUNBOOK.md`.

## Client examples

### Python with `httpx`

```python
from decimal import Decimal

import httpx

response = httpx.get(
    "http://127.0.0.1:8000/api/kpis",
    params={"branch": "Florence", "start": "1420-01"},
    timeout=10.0,
)
response.raise_for_status()
records = response.json()["items"]
net_income = Decimal(records[0]["net_income"]) if records else Decimal("0")
```

### Browser JavaScript

```javascript
const query = new URLSearchParams({
  branch: "Rome",
  severity: "HIGH",
});
const response = await fetch(`http://127.0.0.1:8000/api/alerts?${query}`);
if (!response.ok) throw new Error(`API request failed: ${response.status}`);
const { count, items } = await response.json();
```

## Caching and data refresh

Artifact repository reads and the validated transaction source are cached within
each API process. After generating a new matched artifact/source release, restart
all API workers. Replacing files underneath a running worker is not a reliable
refresh mechanism. See `docs/DEPLOYMENT_RUNBOOK.md` for release and rollback steps.

## Related contracts and implementation

- `DATA_CONTRACTS.md` — authoritative KPI, alert, and serving-detail contracts
- `api/app.py` — routes, query validation, serialization, and error envelopes
- `api/repository.py` — artifact loading, filtering, ordering, and caching
- `serving/contracts.py` — executable Phase 5 record validation
- `docs/PIPELINE_DOCUMENTATION.md` — full source-to-dashboard data flow
- `docs/DEPLOYMENT_RUNBOOK.md` — configuration, operations, refresh, and rollback
