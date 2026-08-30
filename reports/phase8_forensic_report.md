# MEDICIMESS FORENSIC ANALYSIS REPORT

## Executive Summary

The analysis examined all **80,230 validated transactions** using the existing
Phase 4 anomaly engine and its **10,783 alerts**. Alerts were joined to the
ledger through their affected transaction IDs, restricted to operating-expense
suppliers, and ranked by distinct detection rules rather than raw alert count.
Transaction IDs were deduplicated before counts and amounts were calculated.

## Finding

| Field | Result |
|---|---|
| Branch | London |
| Supplier | London Operations |
| Date range | 1390-01-08 through 1440-12-27 |
| Unique affected transactions | 1,397 |
| Total affected amount | 4,980,223.97 florins |
| Average transaction | 3,564.94 florins |
| Distinct rules | B, E, G |

London Operations tied with Milan Operations at three distinct rules. The
declared tie-break selected London because it had more unique alert-affected
transactions: 1,397 versus 1,350. This is an investigative lead, not a finding
of proven fraud.

## Detection Methods

- **Rule B — Vendor Concentration:** identified London Operations as accounting
  for unusually concentrated expense-category spending. It affected all 1,397
  transactions in the evidence set.
- **Rule E — Transaction Frequency Outlier:** identified unusually frequent
  monthly operating-expense activity. It affected 72 unique transactions.
- **Rule G — New Counterparty High Volume:** identified high transaction volume
  during the counterparty's first active period. It affected five unique
  transactions.

## Analysis

The combination of concentration, frequency outliers, and high initial volume
justifies management review. However, the activity spans almost the entire
51-year dataset, and the name “London Operations” may represent a broad internal
branch-cost label rather than an external supplier. Management should establish
the counterparty's legal identity, ownership, supporting invoices, approvers,
and whether unrelated expenses were combined under one label.

A separate, rule-neutral screen for multi-rule supplier activity confined to
five years or less identified one concentrated episode: **Florence / Ser
Benedetto Forniture**, flagged by Rules B and D. Its **230 unique transactions**
span **1420-01-03 through 1424-12-26** and total **95,610.00 florins**. Although
it did not win the formal distinct-rule ranking, its compact duration and
round-number pattern warrant priority vendor-verification review.

## Recommended Internal Controls

1. Require independent vendor onboarding and annual reverification, including
   identity, ownership, address, payment account, and conflict-of-interest
   checks performed by staff without payment authority.
2. Separate purchase authorization, receipt confirmation, invoice approval,
   and payment release; require secondary approval when cumulative supplier
   spend or payment frequency exceeds branch-specific limits.
3. Provide monthly vendor-concentration, frequency, round-number, and new-vendor
   exception reports to branch management and internal audit with documented
   explanations and sign-off.
4. Independently reconcile invoices, purchase orders, receiving evidence, and
   ledger entries. Replace generic internal counterparty labels with accountable
   cost centers and named approvers.

## Conclusion

The alert-led analysis identifies London Operations as the formal multi-rule
leader and Ser Benedetto Forniture as a concentrated secondary concern. Neither
pattern proves fraud by itself. Both require documentary validation, independent
reconciliation, and management follow-up, with the shorter Florence episode
receiving focused vendor and authorization testing.
