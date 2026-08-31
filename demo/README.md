# MediciMess offline demo

This folder contains a self-contained visual tour of the dashboard for times when
the live API and Dash application are unavailable.

## View the prepared demo

- Open `offline_demo/medicimess-dashboard-walkthrough.mp4` for the short tour.
- Browse `offline_demo/screenshots/` for full-resolution stills of every panel.
- Start with `02-network-overview-dark.png`, then use the numbered branch images.
- `04-florence-complete-dark.png` is a single, full-page archival capture.
- `11-florence-overview-light.png` demonstrates the alternate theme.

The screenshots cover authentication, the managing-director network comparison,
branch and reporting-period controls, KPI cards, cash flow, operating expenses,
loan activity, bills of exchange, anomaly alerts, transaction review, navigation,
and both visual themes.

## Suggested narration (about 30 seconds)

“After secure sign-in, the managing director lands on a network comparison of all
Medici branches, including cash, income, loans, alerts, and outlier ratios. A branch
drill-down opens the operational view. The reporting controls update the KPI cards
and every analytical panel. Cash-flow trends explain liquidity; expenses and loans
show category and counterparty concentration; bills cover correspondent banking;
alerts support risk triage; and the validated ledger provides searchable, sortable,
paginated transaction review. The interface also includes a daylight theme and
role-restricted branch access.”

## Regenerate after UI changes

Requirements: Python dependencies from the repository, Google Chrome or Chromium,
plus `Pillow`, `websocket-client`, and `imageio-ffmpeg`.

```bash
python3 demo/capture_offline_demo.py
```

The utility starts local services on ports 8000 and 8050, launches headless Chrome,
signs in with the documented local demo account, waits for real data, and replaces
the generated files. It does not require internet access. Override the browser path
with `MEDICIMESS_CHROME=/path/to/chrome` when needed.
