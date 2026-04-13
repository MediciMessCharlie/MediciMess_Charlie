# Instructor's Guide — The Embezzlement of Ser Benedetto di Agnolo

## ⚠️ INSTRUCTOR USE ONLY

**This document describes a hidden embezzlement scenario embedded in the `medici_transactions.csv` and `medici_transactions.json` datasets. Do not distribute to students before they complete the forensic analysis exercise.**

---

## 1. The Crime

### Background

Ser Benedetto di Agnolo is a senior clerk at the Medici Bank's Florence branch. He has worked at the branch since 1415 and is trusted with day-to-day approval of small operating expenses. He knows that the Head Auditor in Florence reviews only aggregate totals and rarely examines individual supply payments below 1,000 florins.

### The Scheme

Starting on 3 January 1420, Ser Benedetto begins authorising payments to a fictitious supplier he names **"Ser Benedetto Forniture"** ("Benedetto's Supplies"). The vendor is registered in the ledger as a provider of scribal materials — parchment, ink, quills, wax — entirely plausible for a busy banking branch that produces thousands of letters, bills of exchange, and ledger pages each year.

Over five years (1420–1424), Ser Benedetto authorises **230 payments** totalling approximately **95,610 florins**. The payments range from 250 to 617.50 florins each, averaging about 415 florins. Payments are made roughly every 8 days.

The money flows from the Florence branch's Cash account to the fictitious vendor. Ser Benedetto has arranged for a correspondent in Genoa — a genuine merchant named Marco Villani whom he personally knows — to receive the funds and pass them on, taking a small cut.

### Accounting Entries

Each fraudulent transaction is recorded as a standard operating expense:

```
Debit:  Supplies                      [e.g., 400.00 florins]
Credit: Cash                          [e.g., 400.00 florins]
Description: "Parchment and scribal supplies from Ser Benedetto Forniture"
Branch: Florence
Type: operating_expense
Counterparty: Ser Benedetto Forniture
```

This is a **valid double-entry transaction** — debits equal credits, the account type is correct, and the description is plausible. The fraud is not in the accounting mechanics; it is in the fictitious nature of the counterparty and the absence of any goods received.

### Timeline

| Year | Approximate Amount | Number of Payments |
|------|-------------------|-------------------|
| 1420 | ~18,500 florins | ~46 payments |
| 1421 | ~19,000 florins | ~47 payments |
| 1422 | ~19,200 florins | ~47 payments |
| 1423 | ~19,500 florins | ~47 payments |
| 1424 | ~19,410 florins | ~43 payments |
| **Total** | **~95,610 florins** | **~230 payments** |

---

## 2. Why It Is Hard to Spot Without Analysis

### 2.1 The Amounts Look Normal

Each individual payment (250–618 florins) is well within the normal range for supply purchases. The Florence branch processes hundreds of operating expense transactions; a single 400-florin supply payment does not stand out when a branch manager reviews a ledger page.

### 2.2 The Description Is Plausible

"Parchment and scribal materials" is a legitimate and expected expense for a Renaissance banking branch. The Medici Bank's Florence headquarters produced an enormous volume of correspondence, bills of exchange, account books, and legal documents. A supply budget of even 20,000 florins per year could be rationalised.

### 2.3 The Double-Entry Is Correct

The transactions are properly balanced — debits equal credits. Any automated balance check will pass.

### 2.4 The Volume Is Spread Over Five Years

The fraud totals ~95,610 florins, but spread over 5 years and ~11,000 Florence operating-expense transactions, the incremental addition is small. Year-over-year expense totals do increase slightly, but not dramatically.

---

## 3. How It Can Be Detected — Forensic Methods

### Method 1: Benford's Law Analysis ⭐ (Primary Detection Method)

**What it is**: Benford's Law states that in naturally occurring numerical data, the leading digit `1` appears about 30% of the time, `2` about 17%, and so on — a logarithmically decreasing distribution. Fraudulently constructed amounts often fail to follow this distribution because fraudsters tend to choose psychologically comfortable round numbers.

**How to apply it**: Extract all `debit_amount` values where `branch = 'Florence'` and `type = 'operating_expense'` and `counterparty = 'Ser Benedetto Forniture'`. Count the first significant digits.

**What you will find**: The fraudulent amounts are drawn almost exclusively from a fixed pool (250, 275, 300, 325, 350, 375, 380, 390, 400, 410, 420, 425, 440, 450, 460, 475, 480, 500, 520, 550, 580, 600). This produces a distribution heavily biased toward digits **2**, **3**, **4**, and **5**, and dramatically under-represents the digit **1** (which should be the most common). A chi-squared test against the expected Benford distribution will return a highly significant p-value (p < 0.001).

```python
# Illustrative Python snippet for students
import pandas as pd
from scipy.stats import chisquare
import numpy as np

df = pd.read_csv("medici_transactions.csv")
fraud_mask = (
    (df["branch"] == "Florence") &
    (df["type"] == "operating_expense") &
    (df["counterparty"] == "Ser Benedetto Forniture")
)
amounts = df.loc[fraud_mask, "debit_amount"]

# Extract first significant digit
first_digits = amounts.apply(lambda x: int(str(x).lstrip("0").replace(".", "")[0]))

# Expected Benford frequencies for digits 1-9
benford_expected = np.log10(1 + 1/np.arange(1, 10))
benford_expected = benford_expected / benford_expected.sum()  # normalise

observed_counts = first_digits.value_counts().reindex(range(1, 10), fill_value=0)
expected_counts = benford_expected * len(amounts)
chi2, p = chisquare(f_obs=observed_counts.values, f_exp=expected_counts)
print(f"Chi-squared = {chi2:.2f}, p-value = {p:.6f}")
# Expected output: very small p-value, rejecting the null that data follows Benford
```

**Compare**: Running the same analysis on legitimate `Supplies` payments from other vendors in Florence will produce a distribution much closer to Benford's Law.

---

### Method 2: Vendor Concentration Analysis ⭐ (Easiest to Spot)

**What it is**: A single vendor should not dominate a specific expense category unless there is a legitimate reason.

**How to apply it**: Group Florence `operating_expense` transactions by year and `debit_account = 'Supplies'`. Compute each counterparty's share of total Supplies spending.

**What you will find**: In every year from 1420 to 1424, "Ser Benedetto Forniture" accounts for **approximately 25–40% of all Supplies expenditure** at the Florence branch. No other single vendor approaches this share. In the years prior to 1420, this vendor does not appear at all.

```python
# Illustrative Python snippet
supplies = df[
    (df["branch"] == "Florence") &
    (df["type"] == "operating_expense") &
    (df["debit_account"] == "Supplies")
].copy()
supplies["year"] = pd.to_datetime(supplies["date"]).dt.year

vendor_share = (
    supplies.groupby(["year", "counterparty"])["debit_amount"]
    .sum()
    .reset_index()
)
total_by_year = supplies.groupby("year")["debit_amount"].sum()
vendor_share["share_pct"] = vendor_share.apply(
    lambda r: r["debit_amount"] / total_by_year[r["year"]] * 100, axis=1
)
print(vendor_share[vendor_share["share_pct"] > 5].sort_values("share_pct", ascending=False))
```

**Red flag**: Legitimate supply vendors serve multiple branches or appear irregularly. "Ser Benedetto Forniture" appears **only in the Florence branch**, in **every year 1420–1424**, with unusual regularity.

---

### Method 3: Round-Number Clustering ⭐

**What it is**: Fraudsters often choose round numbers because they are easier to remember and harder to spot at a glance. Natural transaction amounts (wages based on days worked, materials based on weight, etc.) rarely cluster on exact multiples of 50.

**How to apply it**: For all Florence `Supplies` payments, compute the percentage of amounts that are exact multiples of 50.

**What you will find**: Among the fraudulent payments, approximately **43–48% of amounts are exact multiples of 50** (e.g., 250, 300, 350, 400, 450, 500, 550, 600). Among legitimate Florence supply vendors, this proportion is typically under 10%.

```python
florence_supplies = df[
    (df["branch"] == "Florence") &
    (df["type"] == "operating_expense") &
    (df["debit_account"] == "Supplies")
]

def round50_share(group):
    pct = (group["debit_amount"] % 50 == 0).mean() * 100
    return round(pct, 1)

print(florence_supplies.groupby("counterparty").apply(round50_share).sort_values(ascending=False))
```

---

### Method 4: Payment Frequency Analysis

**What it is**: Real suppliers deliver goods irregularly — depending on orders, inventory, and travel time. A vendor who delivers exactly every 7–8 days, 52 times a year, for 5 consecutive years is suspicious.

**How to apply it**: For "Ser Benedetto Forniture", compute the intervals (in days) between consecutive payment dates.

**What you will find**: Intervals cluster tightly around 7 and 8 days, with very low variance. The mean interval is ~8.0 days, standard deviation ~1.0 day. This regularity is inconsistent with a genuine supplier.

```python
fraud_dates = (
    df[df["counterparty"] == EMBEZZLEMENT_COUNTERPARTY]["date"]
    .pipe(pd.to_datetime)
    .sort_values()
)
intervals = fraud_dates.diff().dt.days.dropna()
print(f"Mean interval: {intervals.mean():.1f} days")
print(f"Std dev:       {intervals.std():.1f} days")
print(f"Min/Max:       {intervals.min()} / {intervals.max()} days")
# Red flag: std dev < 2 days for 230 payments
```

---

### Method 5: Cross-Branch Vendor Absence

**What it is**: A genuine supplier who regularly serves the Florence branch — the Medici's home base and one of the largest branches — would plausibly also supply other nearby branches (Milan, Geneva).

**How to apply it**: List all branches where each Supplies vendor appears.

**What you will find**: "Ser Benedetto Forniture" appears **only in Florence**. No other record of this vendor exists in the Rome, Venice, Milan, Geneva, Bruges, London, or Avignon branches.

```python
vendor_branches = (
    df[df["counterparty"] == "Ser Benedetto Forniture"]["branch"]
    .value_counts()
)
print(vendor_branches)
# Expected output: only Florence
```

---

### Method 6: Temporal Anomaly — New Vendor, Immediate Volume

**What it is**: A brand-new vendor appearing suddenly in 1420 and immediately generating 18,000+ florins in year one, with no ramp-up period, is suspicious.

**How to apply it**: Find vendors that first appear in the dataset after 1415 and immediately have high annual volumes.

**What you will find**: Most new vendors (appearing after 1415) generate modest initial volumes that grow over time. "Ser Benedetto Forniture" starts at full volume on day one — 46 payments totalling ~18,500 florins in its very first year.

---

## 4. Discussion Questions for Students

Use these questions to guide post-analysis discussion:

### On Detection
1. Which of the six detection methods above would you run first on an unfamiliar dataset, and why?
2. Which method alone is **sufficient** to identify the fraud? Which require corroboration?
3. Benford's Law detected the fraud — but what could a more sophisticated fraudster do to defeat Benford's Law detection?
4. If you could add only one field to the transaction schema to make fraud detection easier, what would it be?

### On the Accounting
5. The fraudulent transactions are perfectly balanced (debits = credits). Does this mean the double-entry system failed? Why or why not?
6. What internal controls (process-level, not analytical) would have prevented this fraud?
7. A real auditor would request **supporting documentation** (invoices, delivery records) for supply payments above a certain threshold. What threshold would have caught this fraud the earliest?

### On Data Engineering
8. Write the SQL (or pandas) query that computes the **annual Supplies spend per vendor per branch**, sorted by percentage share. Which rows flag the fraud?
9. Design a pipeline rule that would automatically alert an auditor to a vendor accounting for > 10% of any expense category in a branch within a single quarter.
10. How would you test that your anomaly detection rule is working correctly? What test data would you create?

### On Ethics and Context
11. Ser Benedetto chose amounts that individually looked unremarkable. What does this tell us about how fraudsters think about detection risk?
12. The fraud lasted 5 years before detection. What organisational factors make long-running fraud possible?

---

## 5. Expected Student Work Products

When assigning this exercise, students should produce:

1. **A Jupyter notebook** or Python script that:
   - Loads `medici_transactions.csv`
   - Applies at least three detection methods from Section 3
   - Produces visualisations (Benford's Law bar chart, vendor concentration table, payment interval histogram)
   - Identifies the fraudulent counterparty and date range
   - Calculates the total amount embezzled

2. **A short report** (1–2 pages) describing:
   - What they found and how
   - Which method was most efficient
   - What internal controls they would recommend
   - How the pipeline spec in `DATA_PIPELINE_SPEC.md` could be extended to detect this automatically

---

## 6. Grading Notes

| Finding | Points |
|---------|--------|
| Correctly identifies "Ser Benedetto Forniture" as the suspect | 20 |
| Correctly identifies Florence as the only branch affected | 10 |
| Correctly identifies the date range (1420–1424) | 10 |
| Reports total within ±5% of actual (~95,610 florins) | 15 |
| Applies Benford's Law correctly and interprets result | 20 |
| Applies at least one additional detection method | 15 |
| Recommends at least two realistic internal controls | 10 |
| **Total** | **100** |

---

## 7. Technical Details for the Instructor

### How the Embezzlement Was Injected

The transactions were generated by the function `generate_embezzlement_transactions()` in `generate_additional_data.py`. Key characteristics:

- **Seed**: `random.seed(7)` — fully deterministic and reproducible
- **Date range**: `2020-01-03` to `2024-12-28` (i.e., 1420 to 1424 in the Medici timeline)
- **Interval**: 8 days ± 1 day (controlled by `interval_days + random.randint(-1, 1)`)
- **Amount pool**: 25 fixed values between 250 and 600 florins, all round multiples of 25
- **Occasional variation**: 25% of payments have an additional irregular amount (7.50, 12.50, 15.00, 17.50, or 22.50 florins) added to simulate slight irregularity
- **Transaction type**: `operating_expense`, matching the other supply payments in the dataset
- **Account**: `debit_account = "Supplies"` — merges with legitimate supplies payments

### Verifying the Fraud Is Present

```bash
grep "Ser Benedetto Forniture" medici_transactions.csv | wc -l
# Expected: 230

python3 -c "
import csv
total = 0
count = 0
with open('medici_transactions.csv') as f:
    for row in csv.DictReader(f):
        if row['counterparty'] == 'Ser Benedetto Forniture':
            total += float(row['debit_amount'])
            count += 1
print(f'{count} transactions, {total:,.2f} florins total')
"
# Expected: 230 transactions, 95,610.00 florins total
```

### Why These Numbers

The target was "about 100,000 florins." The actual total (~95,610) is within 5% of that target. The slight shortfall is because the scheme ends in late December 1424 rather than running a full fifth year, and the random payment pool averages slightly below 416 florins.

---

## 8. References

- Singleton, T.W. & Singleton, A.J. (2010). *Fraud Auditing and Forensic Accounting* (4th ed.). Wiley.
- Nigrini, M.J. (2012). *Benford's Law: Applications for Forensic Accounting, Auditing, and Fraud Detection*. Wiley.
- de Roover, R. (1963). *The Rise and Decline of the Medici Bank*. Harvard University Press.
- `DATA_PIPELINE_SPEC.md` — anomaly detection rules (Rules A–G) that model the detection methods above
- `generate_additional_data.py` — source code for the embezzlement transaction generator

---

*Document prepared for instructor use. Version 1.0. Do not distribute to students.*
