# Phase 5 Serving Layer

## Purpose and boundary

Phase 5 receives completed in-memory outputs from Phases 3 and 4, validates
their contracts, partitions them, and writes stable JSON and CSV artifacts.
It does not calculate KPIs, group financial details, or execute anomaly rules.

```text
validated transactions
    ├── analytics.kpis      → KPI, expense-detail, and loan-activity records
    └── analytics.alerts    → alert records
                                  ↓
                         serving.artifacts
                                  ↓
                         JSON and CSV files
```

The finalized record fields and types are in `DATA_CONTRACTS.md`. Executable
handoff validation is in `serving/contracts.py`.

## Generate artifacts

Generate a small read-back fixture:

```bash
python3 generate_serving_artifacts.py \
    tests/test_transactions.json \
    --output sample_serving_outputs
```

Generate artifacts for the complete historical dataset:

```bash
python3 generate_serving_artifacts.py \
    medici_transactions.csv \
    --output serving_outputs
```

The generator runs shared ingestion and validation, calls the real Phase 3
and Phase 4 public functions, and passes their completed outputs to Phase 5.

Code that already owns the in-memory outputs can call Phase 5 directly:

```python
from serving import write_serving_artifacts

manifest = write_serving_artifacts(
    kpi_records=kpi_records,
    alert_records=alert_records,
    expense_details=expense_details,
    loan_details=loan_details,
    output_directory="serving_outputs",
)
```

The returned `ServingManifest` contains every generated path.

## Artifact layout

```text
serving_outputs/
├── metrics/metrics_{branch}_{period}.json
├── time_series/time_series_{branch}.json
├── alerts/alerts_{branch}_{period}.json
├── expenses/expense_breakdown_{branch}_{period}.csv
└── loans/loan_portfolio_{branch}_{period}.csv
```

- A metrics file contains one KPI dictionary.
- A time-series file contains monthly KPI dictionaries sorted by period.
- An alert file contains alerts sorted by `alert_id`, or `[]`.
- Expense and loan files contain deterministic detail rows, or headers only.
- Every KPI branch/period receives all four partitioned artifact types, even
  when no alert, expense, or loan activity exists.

Although the required filename remains `loan_portfolio_...csv`, its rows are
loan-activity summaries. The source has no loan IDs and cannot reliably match
repayments to individual issuances. The CSV therefore does not invent an open
balance or repayment status.

## Serialization and file behavior

- `Decimal` values become JSON strings and CSV text without a float conversion.
- Counts and identifiers remain JSON integers.
- Output uses UTF-8 and deterministic ordering.
- Branch names are made filename-safe without changing record values.
- Repeated runs atomically replace files for the same partition.
- All records are validated before any artifact is written.
- A detail or alert record without a matching KPI partition is rejected.
- Duplicate KPI branch/period records are rejected.

## Testing

```bash
python3 -m pytest -q
```

Tests cover the real Phase 3/4 integration boundary, contract types, exact
Decimal serialization, partitioning, empty outputs, deterministic ordering,
CSV/JSON read-back, invalid input, and atomic reruns.

## Definition of done

- [x] Required JSON and CSV artifact types are implemented.
- [x] Output contracts and the loan-data limitation are documented.
- [x] Sample data generates a complete artifact bundle.
- [x] Generated JSON and CSV files read back successfully.
- [x] Phase 5 contains no KPI or anomaly calculations.
- [x] Tests cover required fields and output structure.
- [x] Writers consume the actual Phase 3 and Phase 4 return values.
