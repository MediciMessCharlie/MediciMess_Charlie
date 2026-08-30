# MediciMess Deployment and Operations Runbook

## Scope and prerequisites

This supports local or controlled demonstrations. Hard-coded users, the Dash/Flask
development server, and plain HTTP are not production-ready. Use Python 3.12 (or
a compatible Python 3), a readable transaction source, adequate disk space, and
free ports 8000 and 8050.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pytest -q
```

For the example notebook, also run:

```bash
python3 -m pip install jupyter pandas matplotlib
```

## Generate a serving release

```bash
python3 generate_serving_artifacts.py medici_transactions.csv --output serving_outputs
```

Review accepted/rejected totals and rejection reasons. Source-level errors prevent
generation; row-level rejections do not. Prefer a new versioned output directory
for each controlled release. Preflight with:

```bash
find serving_outputs -type f | wc -l
python3 -m pytest -q
git diff --check
```

## Start both services

Terminal 1:

```bash
MEDICIMESS_ARTIFACT_DIRECTORY=serving_outputs \
MEDICIMESS_TRANSACTION_SOURCE=medici_transactions.csv \
uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
MEDICIMESS_SESSION_SECRET='replace-with-a-long-random-value' \
MEDICIMESS_API_URL=http://127.0.0.1:8000 \
python3 -m dashboard.app
```

Open `http://127.0.0.1:8050/login`. Add `--reload` to Uvicorn only for local code
development.

## Configuration

| Variable | Process | Purpose | Development default |
| --- | --- | --- | --- |
| `MEDICIMESS_ARTIFACT_DIRECTORY` | API | Phase 5 artifact root | `sample_serving_outputs` |
| `MEDICIMESS_TRANSACTION_SOURCE` | API | validated ledger source | `medici_transactions.csv` |
| `MEDICIMESS_API_URL` | dashboard | FastAPI base URL | `http://127.0.0.1:8000` |
| `MEDICIMESS_SESSION_SECRET` | dashboard | session signing | insecure local fallback |

Use absolute paths under a service manager. Keep the session secret out of source
control; rotating it invalidates current sessions.

## Smoke test

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/api/branches
curl --fail 'http://127.0.0.1:8000/api/kpis?branch=Rome'
curl --fail 'http://127.0.0.1:8000/api/alerts?branch=Rome&severity=HIGH'
```

Log in with both demo roles. Confirm the director can access the network and two
branches; confirm `rome.manager` is redirected away from `/` and non-Rome branches.
Check `/docs`, KPI and alert filters, and transaction pagination.

## Refresh and rollback

Repositories cache files in-process. To refresh: generate a complete new directory,
run tests, review ingestion totals, start new API workers against the matched new
artifact and transaction paths, smoke-test, then switch the dashboard/traffic.
Replacing files without restarting workers can leave stale data.

Rollback by restarting against the previous matched artifact and transaction
release. Never combine artifacts and a source from unrelated releases; details can
then disagree with KPIs.

## Failure response

- Missing/data-unavailable response: verify artifact path and build completion;
  roll back if incomplete.
- Query validation error: use supported values and `YYYY-MM`/`YYYY-MM-DD` formats.
- Transaction source error: inspect permissions, schema, encoding, and balance.
- Dashboard cannot connect: check API health, URL, port, and network policy.
- Suspected corruption: remove the release from service, retain evidence/logs,
  regenerate into a new directory, and compare counts.

Retain source, artifact release, commit, generation timestamp, and test evidence
together. Restrict their filesystem access. Before production use, add TLS,
external identity and persistent users, secret management, hardened sessions,
managed ASGI/WSGI workers, centralized logs/metrics, backups, rate limiting, and a
database-backed alert acknowledgement and audit trail.
