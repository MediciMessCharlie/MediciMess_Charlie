# MediciMess_Charlie Data Contracts

## Purpose

This document defines the shared data contracts used between Phases 3
through 6 of the MediciMess_Charlie project.

The goal is to make sure each phase uses the same field names and data
structure. Phase 3 will produce KPI records, and Phase 4 will produce
alert records. Phases 5 and 6 can build against these contracts even
while Phases 3 and 4 are still being developed.

Once the team agrees on these contracts, field names should not be
changed without discussing the change with the team.

------------------------------------------------------------------------

# 1. KPI Contract

## Purpose

Phase 3 will transform validated transaction data into Key Performance
Indicators (KPIs). A KPI is an important measurement that helps a bank
official understand how a branch is performing.

Phase 3 will produce one KPI record for each branch and reporting
period.

## Reporting Period

The initial reporting period will use monthly values in the following
format:

``` text
YYYY-MM
```

Example:

``` text
1420-01
```

## KPI Record Example

``` python
{
    "branch": "Florence",
    "period": "1420-01",

    # Cash
    "total_cash_inflows": Decimal("250000.00"),
    "total_cash_outflows": Decimal("175000.00"),
    "net_cash_movement": Decimal("75000.00"),
    "closing_cash_balance": Decimal("825000.00"),

    # Deposits and Withdrawals
    "total_deposits": Decimal("180000.00"),
    "total_withdrawals": Decimal("95000.00"),
    "deposit_count": 24,
    "withdrawal_count": 11,
    "avg_deposit_size": Decimal("7500.00"),
    "avg_withdrawal_size": Decimal("8636.36"),

    # Loans
    "loans_issued": Decimal("120000.00"),
    "loans_repaid": Decimal("80000.00"),
    "interest_earned": Decimal("8000.00"),
    "loan_portfolio_balance": Decimal("540000.00"),
    "interest_yield": Decimal("10.00"),

    # Operating Expenses
    "total_operating_expenses": Decimal("45000.00"),
    "expense_per_transaction": Decimal("321.43"),

    "expenses_by_category": {
        "Wages Expense": Decimal("20000.00"),
        "Rent Expense": Decimal("10000.00"),
        "Security Expense": Decimal("15000.00")
    },

    "top_payees_by_expense": [
        {
            "counterparty": "Florence Security Guild",
            "amount": Decimal("15000.00")
        }
    ],

    # Revenue
    "exchange_fee_revenue": Decimal("5000.00"),
    "interest_income": Decimal("8000.00"),
    "trading_revenue": Decimal("77000.00"),
    "total_revenue": Decimal("90000.00"),

    # Profitability
    "net_income": Decimal("45000.00"),
    "net_income_margin": Decimal("50.00")
}
```

## KPI Field Definitions

  -----------------------------------------------------------------------------------
  Field                        Type              Required          Description
  ---------------------------- ----------------- ----------------- ------------------
  `branch`                     string            Yes               Branch associated
                                                                   with the KPI
                                                                   record

  `period`                     string            Yes               Reporting period
                                                                   in `YYYY-MM`
                                                                   format

  `total_cash_inflows`         Decimal           Yes               Total cash
                                                                   entering the
                                                                   branch

  `total_cash_outflows`        Decimal           Yes               Total cash leaving
                                                                   the branch

  `net_cash_movement`          Decimal           Yes               Cash inflows minus
                                                                   cash outflows

  `closing_cash_balance`       Decimal           Yes               Cumulative cash
                                                                   position through
                                                                   the end of the
                                                                   period

  `total_deposits`             Decimal           Yes               Total value of
                                                                   deposits

  `total_withdrawals`          Decimal           Yes               Total value of
                                                                   withdrawals

  `deposit_count`              integer           Yes               Number of deposit
                                                                   transactions

  `withdrawal_count`           integer           Yes               Number of
                                                                   withdrawal
                                                                   transactions

  `avg_deposit_size`           Decimal           Yes               Average deposit
                                                                   amount

  `avg_withdrawal_size`        Decimal           Yes               Average withdrawal
                                                                   amount

  `loans_issued`               Decimal           Yes               Total value of
                                                                   loans issued

  `loans_repaid`               Decimal           Yes               Total loan
                                                                   principal repaid

  `interest_earned`            Decimal           Yes               Interest earned
                                                                   from loan
                                                                   repayments

  `loan_portfolio_balance`     Decimal           Yes               Cumulative loans
                                                                   issued minus loans
                                                                   repaid

  `interest_yield`             Decimal           Yes               Interest earned
                                                                   divided by loans
                                                                   repaid, as a
                                                                   percentage

  `total_operating_expenses`   Decimal           Yes               Total operating
                                                                   expenses

  `expense_per_transaction`    Decimal           Yes               Operating expenses
                                                                   divided by
                                                                   transaction count

  `expenses_by_category`       dictionary        Yes               Operating expense
                                                                   totals grouped by
                                                                   expense
                                                                   account/category

  `top_payees_by_expense`      list of           Yes               Ranked expense
                               dictionaries                        counterparties and
                                                                   amounts

  `exchange_fee_revenue`       Decimal           Yes               Revenue from
                                                                   bill-of-exchange
                                                                   fees

  `interest_income`            Decimal           Yes               Interest income
                                                                   recorded in
                                                                   transactions

  `trading_revenue`            Decimal           Yes               Trading revenue

  `total_revenue`              Decimal           Yes               Total revenue from
                                                                   all revenue
                                                                   categories

  `net_income`                 Decimal           Yes               Total revenue
                                                                   minus operating
                                                                   expenses

  `net_income_margin`          Decimal           Yes               Net income divided
                                                                   by total revenue,
                                                                   as a percentage
  -----------------------------------------------------------------------------------

## KPI Contract Rules

-   Money values will use `Decimal` inside Python.
-   Count values will use integers.
-   Percentage values will use `Decimal`.
-   If no matching transactions exist for a KPI, the value should be
    zero rather than `None`.
-   Every KPI record must include `branch` and `period`.
-   Phase 5 may convert `Decimal` values into a JSON-compatible
    representation when output files are created.
-   Phase 5 and Phase 6 should use these exact field names when
    consuming KPI data.

------------------------------------------------------------------------

# 2. Alert Contract

## Purpose

Phase 4 will analyze transaction data for unusual or suspicious
patterns. When an anomaly-detection rule is triggered, Phase 4 will
produce an alert record.

Each detected anomaly will use the same alert structure so Phases 5 and
6 know exactly what information to expect.

## Alert Record Example

``` python
{
    "alert_id": 1,
    "rule": "B",
    "severity": "HIGH",
    "branch": "Florence",
    "period": "1420-01",

    "affected_transaction_ids": [
        1234,
        1288,
        1301
    ],

    "counterparty": "Florence Security Guild",
    "metric_value": Decimal("8.20"),
    "threshold_value": Decimal("5.00"),

    "description": (
        "Florence Security Guild represents 8.2% "
        "of Security Expense for the period."
    ),

    "detected_at": "2026-08-27T12:30:00",
    "status": "OPEN"
}
```

## Alert Field Definitions

  ----------------------------------------------------------------------------------
  Field                        Type              Required          Description
  ---------------------------- ----------------- ----------------- -----------------
  `alert_id`                   integer           Yes               Unique alert
                                                                   identifier

  `rule`                       string            Yes               Anomaly rule code

  `severity`                   string            Yes               `LOW`, `MEDIUM`,
                                                                   or `HIGH`

  `branch`                     string            Yes               Branch where the
                                                                   anomaly was
                                                                   detected

  `period`                     string            Yes               Reporting period
                                                                   in `YYYY-MM`
                                                                   format

  `affected_transaction_ids`   list of integers  Yes               Transaction IDs
                                                                   associated with
                                                                   the alert

  `counterparty`               string or None    Yes               Relevant
                                                                   counterparty when
                                                                   applicable

  `metric_value`               numeric           Yes               Calculated value
                                                                   that triggered
                                                                   the alert

  `threshold_value`            numeric           Yes               Threshold used by
                                                                   the rule

  `description`                string            Yes               Human-readable
                                                                   explanation of
                                                                   the alert

  `detected_at`                ISO timestamp     Yes               Date/time the
                               string                              alert was
                                                                   generated

  `status`                     string            Yes               Current alert
                                                                   status
  ----------------------------------------------------------------------------------

## Severity Values

Only the following severity values should be used:

``` text
LOW
MEDIUM
HIGH
```

## Alert Status Values

New alerts will begin with:

``` text
OPEN
```

Later phases may support:

``` text
ACKNOWLEDGED
RESOLVED
```

## Anomaly Rule Codes

  Rule   Description
  ------ ------------------------------------------------
  `A`    Benford's Law Deviation
  `B`    Vendor Concentration
  `C`    Duplicate Transaction Detection
  `D`    Round-Number Clustering
  `E`    Transaction Frequency Outlier by Counterparty
  `F`    Amount Below Reporting Threshold / Structuring
  `G`    New Counterparty with Immediate High Volume

## Alert Contract Rules

-   Every anomaly rule must return alerts using this same structure.
-   `affected_transaction_ids` must always be a list, even if only one
    transaction is involved.
-   `counterparty` may be `None` when a rule does not apply to one
    specific counterparty.
-   New alerts should use a status of `OPEN`.
-   Rule codes should remain `A` through `G` as defined above.
-   Phase 5 and Phase 6 should use these exact field names when
    consuming alert data.

------------------------------------------------------------------------

# 3. Phase Handoff

The expected flow between the project phases is:

``` text
Phase 2
Validated Transactions
        |
        +-------------------+
        |                   |
        v                   v
     Phase 3             Phase 4
       KPIs               Alerts
        |                   |
        +---------+---------+
                  |
                  v
             Phase 5 / 6
        Serving Layer / API
```

Phase 3 is responsible for calculating KPI data.

Phase 4 is responsible for detecting anomalies and creating alert data.

Phases 5 and 6 are responsible for consuming these results. They should
not duplicate the KPI formulas or anomaly-detection logic.

Hakeem and Vijay may use sample/mock KPI and alert records that follow
these contracts while the actual Phase 3 and Phase 4 code is being
developed.

------------------------------------------------------------------------

# 4. Team Agreement

Before Phases 3 through 6 are developed independently, the team should
confirm:

-   The KPI field names are acceptable.
-   The alert field names are acceptable.
-   Monthly reporting using `YYYY-MM` is acceptable.
-   Money will use `Decimal` within the Python processing layer.
-   Missing KPI activity will return zero rather than `None`.
-   Alert severity values will be `LOW`, `MEDIUM`, or `HIGH`.
-   New alert status will be `OPEN`.
-   Any future changes to these contracts will be communicated to the
    team before dependent code is changed.

Once agreed upon, this document becomes the shared contract between
Phases 3, 4, 5, and 6.

------------------------------------------------------------------------

# 5. Serving Detail Contracts

Phase 3 also produces the detail records needed by the Phase 5 CSV
artifacts. These are transformation outputs; Phase 5 must not recreate
their groupings or financial calculations.

## Expense Detail Record

`calculate_expense_details(transactions)` returns `list[dict]`, grouped
by branch, monthly period, expense category, and counterparty.

``` python
{
    "branch": "Florence",
    "period": "1420-01",
    "category": "Security Expense",
    "counterparty": "Florence Security Guild",
    "transaction_count": 3,
    "amount": Decimal("15000.00")
}
```

All six fields are required. `transaction_count` is a non-negative
integer and `amount` is a `Decimal`. Empty input or no matching expense
activity returns `[]`.

## Loan Detail Record

`calculate_loan_details(transactions)` returns `list[dict]`, grouped by
branch, monthly period, and counterparty.

``` python
{
    "branch": "Florence",
    "period": "1420-01",
    "counterparty": "Tuscan Wool Merchants Guild",
    "loans_issued": Decimal("120000.00"),
    "loans_repaid": Decimal("80000.00"),
    "interest_earned": Decimal("8000.00"),
    "net_loan_movement": Decimal("40000.00")
}
```

All seven fields are required. Financial values are `Decimal` and
`net_loan_movement` equals `loans_issued - loans_repaid`. Empty input
or no matching loan activity returns `[]`.

The source dataset does not contain loan identifiers linking an
issuance to its repayments. These records therefore describe observed
loan activity, not individual open-loan balances or repayment status.
Phase 5 must not label them as matched loans or infer `OPEN`/`REPAID`
status.

## Time-Series Contract

Phase 5 uses the monthly KPI records as branch time-series observations.
For each branch, records are sorted by `period` and written as a JSON
list. No daily or weekly KPI values are inferred in Phase 5.

## Phase 5 Serialization Rules

- `Decimal` values are serialized as JSON strings and CSV text to
  preserve exact precision.
- KPI metric files contain one KPI dictionary.
- Branch time-series files contain a list of monthly KPI dictionaries.
- Alert files contain a list of alert dictionaries; no alerts is `[]`.
- Empty expense and loan CSV files contain headers and no data rows.
- Files are partitioned using the exact branch and `YYYY-MM` period
  values supplied by Phase 3 and Phase 4.
