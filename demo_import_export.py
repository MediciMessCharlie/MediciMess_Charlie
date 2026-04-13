#!/usr/bin/env python3
"""
Demo script showing how to import and export transaction data for the Medici Bank.

This demonstrates:
1. Exporting transactions to CSV and JSON
2. Importing transactions from CSV and JSON
3. Verifying that imported data maintains double-entry accounting principles
"""

import sys
from decimal import Decimal
from datetime import date

# Import the banking system
exec(open('medici-banking.py').read())


def demo_export():
    """Demonstrate exporting transactions to CSV and JSON"""
    print("="*70)
    print("DEMO: EXPORTING TRANSACTIONS")
    print("="*70)
    
    # Create a ledger with sample transactions
    ledger = Ledger("Export Demo Bank")
    
    # Create accounts
    cash = ledger.create_account("Cash", AccountType.ASSET)
    revenue = ledger.create_account("Service Revenue", AccountType.REVENUE)
    expenses = ledger.create_account("Operating Expenses", AccountType.EXPENSE)
    capital = ledger.create_account("Owner's Capital", AccountType.EQUITY)
    
    # Add some transactions
    print("\nRecording sample transactions...")
    ledger.record_transaction(
        date(2024, 1, 1),
        "Initial capital investment",
        TransactionEntry(cash, Decimal("10000.00")),
        TransactionEntry(capital, Decimal("10000.00"))
    )
    
    ledger.record_transaction(
        date(2024, 1, 15),
        "Service revenue received",
        TransactionEntry(cash, Decimal("1500.00")),
        TransactionEntry(revenue, Decimal("1500.00"))
    )
    
    ledger.record_transaction(
        date(2024, 1, 30),
        "Operating expenses paid",
        TransactionEntry(expenses, Decimal("500.00")),
        TransactionEntry(cash, Decimal("-500.00"))
    )
    
    # Export to CSV
    print("\n" + "-"*70)
    csv_count = ledger.export_transactions_to_csv("exported_transactions.csv")
    print(f"✓ Exported {csv_count} transactions to 'exported_transactions.csv'")
    
    # Export to JSON
    json_count = ledger.export_transactions_to_json("exported_transactions.json")
    print(f"✓ Exported {json_count} transactions to 'exported_transactions.json'")
    
    return ledger


def demo_import_csv():
    """Demonstrate importing transactions from CSV"""
    print("\n" + "="*70)
    print("DEMO: IMPORTING TRANSACTIONS FROM CSV")
    print("="*70)
    
    # Create a new ledger
    ledger = Ledger("CSV Import Demo Bank")
    
    # Import from CSV
    print("\nImporting transactions from 'exported_transactions.csv'...")
    count = ledger.import_transactions_from_csv("exported_transactions.csv", verbose=False)
    print(f"✓ Imported {count} transactions from CSV")
    
    # Verify the books are balanced
    print("\n" + "-"*70)
    print("Verifying imported transactions:")
    print("-"*70)
    ledger.print_trial_balance()
    
    return ledger


def demo_import_json():
    """Demonstrate importing transactions from JSON"""
    print("\n" + "="*70)
    print("DEMO: IMPORTING TRANSACTIONS FROM JSON")
    print("="*70)
    
    # Create a new ledger
    ledger = Ledger("JSON Import Demo Bank")
    
    # Import from JSON
    print("\nImporting transactions from 'exported_transactions.json'...")
    count = ledger.import_transactions_from_json("exported_transactions.json", verbose=False)
    print(f"✓ Imported {count} transactions from JSON")
    
    # Verify the books are balanced
    print("\n" + "-"*70)
    print("Verifying imported transactions:")
    print("-"*70)
    ledger.print_trial_balance()
    
    return ledger


def demo_historical_data():
    """Demonstrate importing the large historical dataset"""
    print("\n" + "="*70)
    print("DEMO: IMPORTING HISTORICAL DATA (20,000 transactions)")
    print("="*70)
    
    # Create a new ledger
    ledger = Ledger("Medici Historical Bank")
    
    # Check if the historical data file exists
    import os
    if not os.path.exists("medici_transactions.csv"):
        print("\n❌ Historical data file 'medici_transactions.csv' not found.")
        print("   Run 'python3 generate_historical_data.py' to generate it first.")
        return None
    
    print("\nImporting 20,000 historical transactions...")
    print("(This may take a few seconds...)")
    
    # Import the historical data
    count = ledger.import_transactions_from_csv("medici_transactions.csv", verbose=False)
    print(f"\n✓ Successfully imported {count} transactions!")
    
    # Show some statistics
    print("\n" + "-"*70)
    print("Account Statistics:")
    print("-"*70)
    print(f"Total accounts created: {len(ledger.accounts)}")
    print(f"Total transactions: {len(ledger.transactions)}")
    
    # Calculate total debits and credits
    total_debits = Decimal('0')
    total_credits = Decimal('0')
    for transaction in ledger.transactions:
        total_debits += sum(entry.amount for entry in transaction.debits)
        total_credits += sum(entry.amount for entry in transaction.credits)
    
    print(f"\nTotal debits:  {total_debits.quantize(Decimal('0.01'))}")
    print(f"Total credits: {total_credits.quantize(Decimal('0.01'))}")
    print(f"Difference:    {(total_debits - total_credits).quantize(Decimal('0.01'))}")
    
    if total_debits == total_credits:
        print("\n✓ All transactions are properly balanced!")
    else:
        print("\n❌ WARNING: Transactions are not balanced!")
    
    return ledger


def main():
    """Run all demos"""
    print("\n" + "#"*70)
    print("# MEDICI BANK - IMPORT/EXPORT DEMONSTRATION")
    print("#"*70)
    
    # Demo 1: Export transactions
    export_ledger = demo_export()
    
    # Demo 2: Import from CSV
    csv_ledger = demo_import_csv()
    
    # Demo 3: Import from JSON
    json_ledger = demo_import_json()
    
    # Demo 4: Import historical data (optional)
    print("\n" + "="*70)
    response = input("Do you want to import the 20,000 historical transactions? (y/N): ")
    if response.lower() in ['y', 'yes']:
        historical_ledger = demo_historical_data()
    
    print("\n" + "#"*70)
    print("# DEMONSTRATION COMPLETE")
    print("#"*70)
    print("\nYou can now use the import/export methods in your own code:")
    print("  - ledger.export_transactions_to_csv('filename.csv')")
    print("  - ledger.export_transactions_to_json('filename.json')")
    print("  - ledger.import_transactions_from_csv('filename.csv')")
    print("  - ledger.import_transactions_from_json('filename.json')")


if __name__ == "__main__":
    main()
