# Medici Bank Historical Transaction Data

## Overview

This directory contains approximately **80,000 historically-themed banking transactions** generated based on actual events from the Medici Bank's operations during 1390-1440. The data represents major financial and political events in Renaissance Italy.

The dataset was expanded from the original 20,000 transactions by running `generate_additional_data.py`, which:
- Appended 60,000 more legitimate transactions (same historical distribution)
- Injected a hidden embezzlement trail (~230 transactions, ~95,610 florins, 1420–1424) for forensic analysis exercises

## Files

### Generated Data Files

- **`medici_transactions.csv`** (~11 MB) - Transaction data in CSV format (~80,000 rows)
- **`medici_transactions.json`** (~29 MB) - Transaction data in JSON format (~80,000 records)

### Scripts

- **`generate_historical_data.py`** - Script to generate the initial 20,000 historical transactions
- **`generate_additional_data.py`** - Script to expand to 80,000+ transactions and inject the embezzlement trail
- **`validate_transactions.py`** - Script to validate the generated data

## Data Structure

Each transaction contains the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique transaction identifier |
| `date` | ISO Date | Transaction date (YYYY-MM-DD) |
| `branch` | String | Branch location (Florence, Rome, Venice, etc.) |
| `type` | String | Transaction type (see types below) |
| `counterparty` | String | The other party in the transaction |
| `description` | String | Detailed transaction description |
| `debit_account` | String | Account to debit |
| `debit_amount` | Decimal | Amount to debit (in florins) |
| `credit_account` | String | Primary account to credit |
| `credit_amount` | Decimal | Amount to credit (in florins) |
| `credit_account_2` | String | Secondary credit account (optional) |
| `credit_amount_2` | Decimal | Secondary credit amount (optional) |
| `currency` | String | Currency used (typically "florin") |

## Transaction Types

The data includes the following transaction types based on historical banking operations:

1. **deposit** (31.7%) - Customer deposits, especially from papal sources
2. **operating_expense** (13.6%) - Daily operating costs (wages, rent, supplies, etc.)
3. **war_financing** (13.1%) - Loans to Florence, Venice for various wars
4. **loan_repayment** (10.3%) - Loan repayments with interest
5. **loan_issuance** (9.2%) - Loans to merchants and nobles
6. **bill_of_exchange** (8.0%) - International money transfers (Medici innovation)
7. **withdrawal** (7.8%) - Customer withdrawals
8. **alum_trade** (6.3%) - Trade in alum from papal mines
9. **ransom_payment** (<0.1%) - Special: Council of Constance ransom (35,000 florins)

## Historical Context

The data is based on real historical events:

### Western Schism and Papal Banking (1402-1420s)
- In 1410, Pope John XXIII appointed the Medici as papal bankers
- The Rome branch held ~100,000 florins in papal deposits
- This was the bank's most important client relationship

### Council of Constance (1414-1418)
- The data includes the famous 35,000 florin ransom payment (May 29, 1415)
- Giovanni di Bicci de' Medici paid this to secure Pope John XXIII's release
- This was almost half the bank's profits from its first 20 years

### Florentine-Milanese Wars
- **First War (1390-1402)**: Against Gian Galeazzo Visconti
- **Second War (1422-1426)**: Against Duke Filippo Maria of Milan
- Significant war financing transactions during these periods

### Wars in Lombardy (1423-1454)
- Conflicts between Venice and Milan
- Medici financed Florence's participation
- Data shows increased war financing during this period

### Branches Represented
- **Rome** (33.1%) - Papal banking center
- **Florence** (22.1%) - Home base
- **Venice** (9.7%) - Major trading partner
- **London, Bruges, Avignon, Geneva, Milan** - International network

## Data Validation

All transactions maintain proper double-entry accounting:
- **Total Transactions**: ~80,230
- Every transaction is perfectly balanced (debits = credits).

## Usage

### Viewing the Data

```bash
# View first 10 transactions in CSV
head -11 medici_transactions.csv

# Count total transactions
wc -l medici_transactions.csv

# Search for specific events
grep "ransom" medici_transactions.csv
grep "war_financing" medici_transactions.csv
```

### Generating New Data

```bash
# Generate fresh transaction data
python3 generate_historical_data.py
```

This will create new `medici_transactions.csv` and `medici_transactions.json` files.

### Validating the Data

```bash
# Run validation checks
python3 validate_transactions.py
```

This validates:
- CSV and JSON structure
- Double-entry accounting (debits = credits)
- Date formats
- Transaction distributions
- Historical event coverage

## Sample Transactions

### Council of Constance Ransom
```csv
date,branch,type,amount,description
1415-05-29,Constance,ransom_payment,35000.0,"Payment of 35,000 florin ransom for Pope John XXIII"
```

### Papal Deposit
```csv
date,branch,type,amount,description
1390-01-05,Rome,deposit,38176.7,"Deposit from Vatican Treasury to Rome branch"
```

### War Financing
```csv
date,branch,type,amount,description
1390-01-01,Florence,war_financing,82833.66,"Emergency war financing for Florence defense"
```

### Loan with Interest
```csv
date,branch,type,debit,credit,credit2,description
1390-01-06,Florence,loan_repayment,829.16,720.31,108.85,"Loan repayment from Duke of Milan with interest"
```

## Historical Accuracy

The data is designed to reflect:
- ✓ Realistic transaction amounts (exponential distribution)
- ✓ Historical interest rates (8-25% per annum)
- ✓ Branch distribution (Rome dominant for papal banking)
- ✓ Seasonal patterns in business activity
- ✓ War periods showing increased financing
- ✓ Major historical events (Council of Constance ransom)
- ✓ Banking innovations (bills of exchange)
- ✓ Papal monopolies (alum trade)

## Hidden Forensic Exercise

The dataset includes a deliberately embedded embezzlement scenario for use in data engineering and forensic analysis exercises. A fictitious supplier named "Ser Benedetto Forniture" appears in the Florence branch operating expense records between 1420 and 1424, representing ~230 fraudulent transactions totalling approximately 95,610 florins.

The fraud is designed to be **plausible on casual inspection** but **detectable through simple statistical analysis**, including:
- Benford's Law analysis of first digits
- Vendor concentration analysis
- Round-number clustering
- Payment frequency analysis

**For instructors**: Full details of the scheme, detection methods, discussion questions, and grading rubric are in [`INSTRUCTOR_EMBEZZLEMENT_GUIDE.md`](INSTRUCTOR_EMBEZZLEMENT_GUIDE.md). **Do not distribute to students before the exercise.**

## Integration with Existing Code

This data can be imported into the existing `medici-banking.py` ledger system for demonstration purposes. Each transaction follows the double-entry accounting principles implemented in the main codebase.

## Sources

The historical context is drawn from:
- Raymond de Roover's "The Rise and Decline of the Medici Bank" (1963)
- Contemporary chronicles and papal records
- Historical research on Renaissance Italian banking

## License

This data is part of the MediciMess educational project and is released under the MIT License.
