# Phase 7 — Managing Director Dashboard

## Objective

Extend the Phase 6 branch dashboard with a consolidated network view, branch
drill-down, a Florence shortcut, and role-based access control.

## Features

### Network overview

- One comparison row per branch
- Latest modeled cash and loan-portfolio balances
- Selected-period net-income totals
- Open-alert counts
- Expense ratio and loan yield
- Network-wide aggregate totals
- Optional start and end month filters

Financial calculations use `Decimal`. Snapshot metrics use the latest selected
month, while activity metrics cover the complete selected period.

### Statistical outliers

Expense ratio and loan yield are compared across branches. A branch is flagged
when either value differs from the network average by more than two population
standard deviations, as required by `STUDENT_GUIDE.md`.

### Navigation

- `/` — Network Overview for the Managing Director
- `/branch/<name>` — Full Phase 6 dashboard for the selected branch
- `/branch/Florence` — Florence Branch shortcut
- `/login` — Login page
- `/logout` — End the current session

Selecting a branch in the network table opens its full branch dashboard.

### Role-based access

- Managing Directors can view the network and every branch.
- Branch Managers can view only their assigned branch.
- Branch dropdowns and navigation are restricted by role.
- Server-side authorization rejects crafted cross-branch and network requests.

## API

```text
GET /api/network/summary?start=YYYY-MM&end=YYYY-MM
```

The endpoint returns:

- `branches` — Branch comparison rows
- `totals` — Network aggregate row
- `outliers` — Detected expense-ratio and loan-yield outliers

Financial values are serialized as strings to preserve decimal precision.

## Main files

- `dashboard/network.py` — Network calculations and outlier detection
- `dashboard/access.py` — Role authorization rules
- `dashboard/auth.py` — Login, logout, and session handling
- `dashboard/app.py` — Network and branch dashboard views
- `dashboard/client.py` — Dashboard API client
- `api/app.py` — Network summary endpoint
- `tests/test_network.py` — Network calculation tests
- `tests/test_access.py` — Authorization policy tests
- `tests/test_api.py` and `tests/test_dashboard.py` — Integration tests

## Run with full data

Start FastAPI:

```bash
MEDICIMESS_ARTIFACT_DIRECTORY=serving_outputs \
MEDICIMESS_TRANSACTION_SOURCE=medici_transactions.csv \
uvicorn api.app:app --reload
```

Start Dash in another terminal:

```bash
MEDICIMESS_SESSION_SECRET=replace-with-a-long-random-value \
MEDICIMESS_API_URL=http://127.0.0.1:8000 \
python3 -m dashboard.app
```

Open `http://127.0.0.1:8050/login`.

Local demonstration accounts:

| Role | Username | Password |
| --- | --- | --- |
| Managing Director | `director` | `medici-demo` |
| Rome Branch Manager | `rome.manager` | `medici-demo` |

## Verification

Run all tests:

```bash
python3 -m pytest -q
```

Current results:

- 85 tests passed
- 4,897 KPI records verified across nine discovered branches
- Latest year verified across eight regularly reporting branches
- 210 open alerts found for the latest year
- Bruges identified as a high expense-ratio outlier for the latest year
- `git diff --check` passed

## Known limitations

- Constance contains only one KPI record (`1415-05`) and appears only when that
  reporting period is selected.
- Modeled cash starts from zero because no historical opening balance is available.
- Demo users are stored locally and are not suitable for production.
- Production deployment requires persistent user management, an external identity
  provider, and a strong session secret.

## Handoff

Phase 7 satisfies the `STUDENT_GUIDE.md` requirements for a consolidated network
overview, statistical branch comparison, aggregate totals, branch drill-down,
Florence access, and role-restricted dashboards.
