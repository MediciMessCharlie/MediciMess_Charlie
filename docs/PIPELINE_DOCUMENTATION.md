# MediciMess Pipeline Documentation

## System boundary and data flow

MediciMess converts historical CSV or JSON transactions into validated Python
records, monthly KPIs, anomaly alerts, stable artifacts, a read-only REST API,
and role-restricted dashboards. Phase handoffs use `list[dict]`; monetary values
remain `Decimal` until Phase 5 serialization.

```text
CSV / JSON -> normalization -> shared validation -> accepted list[dict]
  -> Phase 3 KPIs and details -> Phase 4 alerts
  -> Phase 5 contract checks and atomic files
  -> Phase 6 FastAPI -> Phase 6/7 Dash views
```

This is a batch serving path. API KPI/alert requests read precomputed files; they
do not rerun analytics. The transaction endpoint loads and validates its source
file once per API process.

## Ingestion and validation

`ingestion.pipeline.run_pipeline(path, last_processed_id=None)` selects CSV or
JSON ingestion by extension. Other extensions raise `ValueError`.

Required fields are `id`, `date`, `branch`, `type`, `counterparty`, `description`,
`debit_account`, `debit_amount`, `credit_account`, `credit_amount`, and `currency`.
The two secondary credit fields are optional but must occur together.

Normalization produces `int` IDs, `datetime.date` dates, finite `Decimal` amounts,
stripped required strings, and `None` for blank optional values. Every row passes
`validate_transactions.validate_transaction`, which checks required values,
positive IDs, ISO dates, numeric values, paired secondary credits, and double-entry
balance within `Decimal("0.000001")`.

Malformed rows are rejected individually. Results include accepted records,
rejections and reasons, source errors, duplicate rows, totals, and incremental
filter skips. An unreadable file, missing header/columns, or malformed structure
is a source error and prevents artifact generation.

## KPI transformation

`analytics.kpis.calculate_kpis` groups accepted records by branch and `YYYY-MM`,
returning one dictionary per populated branch/month. It computes cash flow and
modeled closing cash, deposits/withdrawals, loan activity and modeled portfolio,
expenses, revenue, net income, and margins. Counts are `int`; amounts and
percentages are `Decimal`; empty numeric results are zero.

Closing balances are cumulative by branch and start at zero because no opening
balance is supplied. `calculate_expense_details` returns records by branch,
period, category, and counterparty. `calculate_loan_details` returns observable
monthly activity by counterparty—not individual loan balances. The authoritative
schema is `DATA_CONTRACTS.md`; executable checks are in `serving/contracts.py`.

## Anomaly detection

`analytics.alerts.generate_alerts` runs seven rules and assigns unique alert IDs:

| Rule | Detection | Trigger | Severity |
| --- | --- | --- | --- |
| A | Benford deviation | MAD > 0.015; at least 30 records | MEDIUM |
| B | Vendor concentration | expense-category share > 5% | HIGH |
| C | Possible duplicate | same branch/month/type/vendor/amount within 3 days | MEDIUM |
| D | Round-number cluster | >30% of expenses are multiples of 50 | MEDIUM |
| E | Frequency outlier | monthly count > mean + 3 population SD | HIGH |
| F | Structuring | each amount <1,000 and monthly group total >10,000 | HIGH |
| G | New high-volume counterparty | first-period volume >10,000 | HIGH |

New alerts are `OPEN`. Alerts are review signals, not proof of wrongdoing. The
current application has no persisted acknowledgement or resolution workflow.

## Serving artifacts

`generate_serving_artifacts.py` runs ingestion, KPIs, alerts, detail calculations,
and `serving.write_serving_artifacts`. Contract checks cover types, required
fields, periods, statuses, duplicate KPI partitions, and orphan detail partitions.

```text
serving_outputs/
  metrics/metrics_<branch>_<period>.json
  time_series/time_series_<branch>.json
  alerts/alerts_<branch>_<period>.json
  expenses/expense_breakdown_<branch>_<period>.csv
  loans/loan_portfolio_<branch>_<period>.csv
```

JSON stores decimals as strings; CSV stores decimal text. Output ordering is
deterministic. Each file is flushed, synced, and atomically replaced so readers do
not observe a partially written artifact.

## REST and dashboard delivery

FastAPI exposes `/health`, `/api/branches`, `/api/kpis`, `/api/alerts`,
`/api/network/summary`, `/api/expenses`, `/api/loans`, `/api/cashflow`, and
`/api/transactions`. Period filters use `YYYY-MM`; transaction dates use
`YYYY-MM-DD`. Transactions support filters, search, sorting, and pagination up to
100 rows. Errors use a common `{ "error": ... }` envelope.

Dash calls this API instead of importing analytics internals. Managing Directors
may view the network and all branches. Branch Managers are limited to their
assigned branch with server-side route enforcement.

## Change control and operating constraints

- Coordinate changes to `DATA_CONTRACTS.md`, producers, consumers, and tests.
- Keep financial values as `Decimal` inside Phases 1–5.
- Regenerate every artifact after source, KPI, alert, or contract changes.
- Restart API workers after regeneration; repository data is cached in-process.
- Keep artifacts and transactions access-controlled as sensitive financial data.
- Run `python3 -m pytest -q` after changes.

Cash starts from a modeled zero opening balance. Loans lack IDs, due dates,
borrower types, reliable status, and individual balances. Bills lack settlement
dates/status. Constance has one KPI month (`1415-05`). Do not invent values to fill
these gaps.
