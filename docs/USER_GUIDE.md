# MediciMess User Guide

## Sign in

Start the services with the Deployment Runbook, then open
`http://127.0.0.1:8050/login`.

| Role | Username | Password | Access |
| --- | --- | --- | --- |
| Managing Director | `director` | `medici-demo` | network and every branch |
| Rome Branch Manager | `rome.manager` | `medici-demo` | Rome only |

These are local demonstration credentials, not production accounts. Log out when
finished, especially on a shared computer.

## Managing Director workflow

The root page displays the network view. Optional start/end months define the
comparison period. Each branch row includes latest modeled cash and loan balances,
period net income, open alerts, expense ratio, and loan yield. Aggregate totals
summarize the network. An outlier marker means expense ratio or loan yield differs
from the network average by more than two population standard deviations.

Select a row to drill into a branch. `/branch/Florence` is the Florence shortcut.

## Branch workflow

Choose a branch and reporting range. The page provides KPI cards, prior-year
comparisons where available, monthly cash flow, expense details, loan activity,
severity-filtered alerts, bills, and a searchable/sortable/paginated transaction
ledger. Branch Managers are redirected to their assigned branch and cannot use a
crafted URL to open another branch or the network.

To investigate an alert, retain its ID, rule, branch, period, counterparty, and
affected transaction IDs, then narrow the ledger with date, type, and search
filters. Changing a ledger filter resets pagination.

## Interpret results carefully

Displayed money originates from exact decimal records. Modeled cash and loan
portfolio values start from zero; they are not reconciled general-ledger balances.
Loan rows show activity, not individual open loans. A blank chart can simply mean
there are no matching observations. Constance reports only in `1415-05`.

An alert is a triage signal, not a finding of misconduct. Rules C and F may validly
return no alerts. The application is read-only; acknowledgements and resolutions
must follow the team's external review process until an audited persistence
workflow is implemented.

## Troubleshooting

- No login page: confirm Dash is running on port 8050.
- API error in Dash: open `http://127.0.0.1:8000/health` and verify
  `MEDICIMESS_API_URL`.
- No metrics: regenerate artifacts and check `MEDICIMESS_ARTIFACT_DIRECTORY`.
- No transactions: check `MEDICIMESS_TRANSACTION_SOURCE`, permissions, and schema.
- Unexpected empty result: clear filters and verify the selected data period.
- Stale results: restart FastAPI because repositories cache loaded records.

Interactive API documentation is at `http://127.0.0.1:8000/docs` while the API
is running.
