# Transaction Data Generation - Technical Notes

## Overview
This document provides technical details about the transaction data generation process and design decisions.

## Decimal Precision

### Design Decision
The transaction generator uses Python's `Decimal` type for all financial calculations to ensure precision. However, the final output is stored as floating-point numbers in CSV/JSON for broader compatibility.

### Rationale
- **Generation**: All calculations (interest rates, fees, amounts) use `Decimal` with `quantize()` to maintain precision
- **Storage**: Output uses float for:
  - Wide compatibility with data analysis tools (Excel, pandas, R, etc.)
  - JSON standard number format
  - Acceptable precision loss for test data (amounts rounded to 2 decimal places)

### Precision Loss
Maximum precision loss per transaction: ±0.005 florins (due to rounding to 2 decimal places)
For 20,000 transactions, cumulative rounding effects are negligible (<0.01% of total volume).

## Data Validation

### Double-Entry Accounting
All transactions maintain the fundamental principle: **Debits = Credits**

Validation results:
- Total debits: 5,376,606,368.51 florins
- Total credits: 5,376,606,368.51 florins
- Difference: 0.00 florins ✓

### Transaction Structure
Each transaction has:
- **Single debit account** with amount
- **One or more credit accounts** with amounts
- Validation ensures sum(debits) = sum(credits) for each transaction

## Historical Accuracy

### Transaction Distribution
The generator uses weighted probabilities to reflect historical banking patterns:
- 31% deposits (reflecting strong papal banking relationship)
- 13% war financing (reflecting frequent conflicts)
- 13% operating expenses (daily operations across 8 branches)
- 10% loan repayments with realistic interest (8-25% per annum)
- 9% loan issuances (core banking activity)
- 8% bills of exchange (Medici innovation in international banking)
- 8% withdrawals (customer activity)
- 6% alum trade (papal monopoly)

### Amount Distribution
Amounts use exponential distribution to reflect realistic banking:
- Most transactions are small (daily operations)
- Some transactions are very large (war financing, major loans)
- Multiplier weights favor smaller amounts (1x, 1x, 1x, 2x, 5x, 10x, 20x, 50x)

### Historical Events
Special transactions represent documented historical events:
1. **Council of Constance Ransom** (May 29, 1415): Exactly 35,000 florins
   - Historical fact: Giovanni di Bicci paid this to free Pope John XXIII
   - Represented almost half of the bank's first 20 years of profits

2. **War Financing Spikes**: During documented war periods
   - First Milanese War (1390-1402)
   - Second Milanese War (1422-1426)
   - Wars in Lombardy (1423-1454)

3. **Papal Banking Boom**: After 1410 when John XXIII appointed Medici as papal bankers
   - Increased deposit activity at Rome branch
   - Rome branch shows 32% of all transactions

## Branch Distribution

### Geographical Spread
The Medici banking network spanned Europe:
- **Rome** (32%): Papal banking center
- **Florence** (22%): Home base and headquarters
- **Venice** (10%): Major trading partner
- **London, Bruges, Avignon, Geneva, Milan** (6-7% each): International branches

### Realistic Operations
Each branch conducts appropriate activities:
- Rome: Heavy papal deposits and religious institution transactions
- Florence: War financing and government loans
- All branches: Customer deposits/withdrawals, loans, operating expenses

## Data Generation Algorithm

### Process Flow
1. Initialize with known historical event (Council of Constance ransom)
2. Generate random dates across 1390-1440 time period
3. Select transaction type based on weighted probabilities
4. Adjust probabilities during historical events (wars, papal banking boom)
5. Generate realistic amounts using exponential distribution
6. Ensure each transaction is balanced (debits = credits)
7. Sort all transactions by date
8. Renumber sequentially

### Randomness
- Seed: 42 (for reproducibility)
- Same seed always generates same dataset
- Change seed to generate different but statistically similar dataset

## File Formats

### CSV Format
- **Pros**: Universal compatibility, human-readable, easy to import
- **Cons**: Less type safety, potential for precision loss
- **Usage**: Best for spreadsheet analysis and general data exploration

### JSON Format
- **Pros**: Structured data, better for programmatic access
- **Cons**: Larger file size (7.2 MB vs 2.9 MB for CSV)
- **Usage**: Best for application integration and API usage

## Performance

### Generation Time
- 20,000 transactions: ~2-3 seconds on modern hardware
- Primarily limited by random number generation and list operations

### File Size
- CSV: 2.9 MB (145 bytes per transaction average)
- JSON: 7.2 MB (360 bytes per transaction average)

### Memory Usage
- Peak memory: ~50 MB (all transactions held in memory)
- Could be optimized for streaming if generating millions of transactions

## Extensibility

### Adding New Transaction Types
1. Create generator method in `TransactionGenerator` class
2. Add to `transaction_weights` dictionary
3. Update documentation

### Modifying Historical Events
1. Update `HistoricalPeriod` class with new date ranges
2. Add conditional logic in `generate_transactions()` method
3. Create specific transaction for major events

### Scaling
To generate more transactions:
- Simply change `num_transactions` parameter
- Current algorithm is O(n) and can handle 100,000+ transactions
- For millions of transactions, consider streaming output

## Testing and Validation

### Automated Validation
The `validate_transactions.py` script checks:
- ✓ CSV/JSON structure validity
- ✓ Required fields present
- ✓ Date format correctness
- ✓ Transaction balance (debits = credits)
- ✓ Historical event presence
- ✓ Data distribution

### Manual Verification
Spot checks recommended:
- View sample transactions
- Verify historical events (Council of Constance)
- Check branch distribution
- Examine transaction type distribution

## Known Limitations

1. **Simplified Accounting**: Real Medici records would have more complex account structures
2. **Historical Estimates**: Exact transaction amounts are estimated based on historical research
3. **Currency Simplification**: All amounts in florins; real operations used multiple currencies
4. **Float Precision**: Output uses float instead of preserving full Decimal precision
5. **Static Data**: Generated once; doesn't reflect temporal business growth patterns

## Future Enhancements

Potential improvements:
- [ ] Add temporal business growth (increasing volumes over time)
- [ ] Multi-currency support with exchange rates
- [ ] More complex transaction types (partnerships, investments)
- [ ] Customer relationship tracking
- [ ] Seasonal business variations
- [ ] Regional economic events impact
- [ ] Employee and merchant name generation
- [ ] Full ledger account hierarchy

## References

1. de Roover, Raymond. "The Rise and Decline of the Medici Bank" (1963)
2. Historical records of Renaissance Italian banking
3. Python Decimal documentation for financial calculations
4. Double-entry accounting principles

---

**Version**: 1.0  
**Last Updated**: 2025-11-21  
**Author**: GitHub Copilot  
**License**: MIT
