"""
Transaction Data Validation Script

Validates that the generated historical transactions maintain proper
double-entry accounting principles and can be loaded into the Medici ledger.
"""

import csv
import json
from decimal import Decimal
from datetime import datetime
from collections import defaultdict


def validate_csv_structure(filename: str) -> bool:
    """Validate the CSV file structure"""
    print(f"\n{'='*60}")
    print(f"VALIDATING CSV FILE: {filename}")
    print(f"{'='*60}\n")
    
    required_fields = {'id', 'date', 'branch', 'type', 'description', 
                      'debit_account', 'debit_amount', 'credit_account', 'credit_amount'}
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames)
            
            # Check if all required fields are present
            missing_fields = required_fields - fieldnames
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            print(f"✓ All required fields present")
            print(f"  Total fields: {len(fieldnames)}")
            print(f"  Fields: {', '.join(sorted(fieldnames))}\n")
            
            # Validate each transaction
            transaction_count = 0
            error_count = 0
            total_debits = Decimal('0')
            total_credits = Decimal('0')
            
            for idx, row in enumerate(reader, 1):
                transaction_count += 1
                
                # Validate date format
                try:
                    datetime.fromisoformat(row['date'])
                except ValueError:
                    print(f"❌ Invalid date format in transaction {idx}: {row['date']}")
                    error_count += 1
                    continue
                
                # Validate amounts
                try:
                    debit_amt = Decimal(str(row['debit_amount']))
                    credit_amt = Decimal(str(row['credit_amount']))
                    
                    # Check for additional credit account
                    if row.get('credit_amount_2'):
                        if not row.get('credit_account_2'):
                            print(f"❌ Missing credit_account_2 for transaction {idx} with credit_amount_2")
                            error_count += 1
                            continue
                        credit_amt += Decimal(str(row['credit_amount_2']))
                    
                    total_debits += debit_amt
                    total_credits += credit_amt
                    
                    # Check if transaction is balanced
                    # Allow for small floating point differences
                    if abs(debit_amt - credit_amt) > Decimal('0.01'):
                        print(f"❌ Unbalanced transaction {idx}: "
                              f"Debit={debit_amt}, Credit={credit_amt}")
                        error_count += 1
                        
                except (ValueError, KeyError) as e:
                    print(f"❌ Invalid amounts in transaction {idx}: {e}")
                    error_count += 1
                    continue
            
            print(f"\nValidation Results:")
            print(f"  Total transactions: {transaction_count}")
            print(f"  Errors found: {error_count}")
            print(f"  Total debits:  {total_debits:,.2f} florins")
            print(f"  Total credits: {total_credits:,.2f} florins")
            print(f"  Difference:    {abs(total_debits - total_credits):,.2f} florins")
            
            if error_count == 0:
                print(f"\n✓ All transactions are valid!")
                return True
            else:
                print(f"\n❌ Found {error_count} errors")
                return False
                
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False


def analyze_transaction_distribution(filename: str):
    """Analyze the distribution of transactions"""
    print(f"\n{'='*60}")
    print(f"TRANSACTION DISTRIBUTION ANALYSIS")
    print(f"{'='*60}\n")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Collect statistics
            by_type = defaultdict(int)
            by_branch = defaultdict(int)
            by_year = defaultdict(int)
            amounts_by_type = defaultdict(list)
            
            for row in reader:
                trans_type = row['type']
                branch = row['branch']
                year = row['date'][:4]
                amount = float(row['debit_amount'])
                
                by_type[trans_type] += 1
                by_branch[branch] += 1
                by_year[year] += 1
                amounts_by_type[trans_type].append(amount)
            
            # Print by type
            print("Transactions by Type:")
            for t_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
                avg_amount = sum(amounts_by_type[t_type]) / len(amounts_by_type[t_type])
                print(f"  {t_type:25s}: {count:5d} (avg: {avg_amount:>12,.2f} florins)")
            
            # Print by branch
            print("\nTransactions by Branch:")
            for branch, count in sorted(by_branch.items(), key=lambda x: x[1], reverse=True):
                print(f"  {branch:15s}: {count:5d}")
            
            # Print by year (sample)
            print("\nTransactions by Year (sample):")
            years_sample = sorted(by_year.items())[:10]
            for year, count in years_sample:
                print(f"  {year}: {count:5d}")
            print(f"  ... ({len(by_year)} total years)")
            
    except Exception as e:
        print(f"❌ Error analyzing distribution: {e}")


def check_historical_events(filename: str):
    """Check for specific historical events in the data"""
    print(f"\n{'='*60}")
    print(f"HISTORICAL EVENT VERIFICATION")
    print(f"{'='*60}\n")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            events_found = {
                'ransom': False,
                'papal_deposits': 0,
                'war_financing': 0,
                'alum_trade': 0,
                'bills_of_exchange': 0
            }
            
            for row in reader:
                trans_type = row['type']
                
                # Check for Council of Constance ransom
                if 'ransom' in trans_type.lower() or 'John XXIII' in row.get('description', ''):
                    events_found['ransom'] = True
                    print(f"✓ Found Council of Constance Ransom:")
                    print(f"  Date: {row['date']}")
                    print(f"  Amount: {row['debit_amount']} florins")
                    print(f"  Description: {row['description']}\n")
                
                # Count major transaction types
                if trans_type == 'deposit' and row['branch'] == 'Rome':
                    events_found['papal_deposits'] += 1
                elif trans_type == 'war_financing':
                    events_found['war_financing'] += 1
                elif trans_type == 'alum_trade':
                    events_found['alum_trade'] += 1
                elif trans_type == 'bill_of_exchange':
                    events_found['bills_of_exchange'] += 1
            
            print("Historical Event Coverage:")
            print(f"  {'Council of Constance Ransom:':<35} {'✓ Found' if events_found['ransom'] else '❌ Missing'}")
            print(f"  {'Papal deposits (Rome branch):':<35} {events_found['papal_deposits']:>6} transactions")
            print(f"  {'War financing operations:':<35} {events_found['war_financing']:>6} transactions")
            print(f"  {'Alum trade (papal monopoly):':<35} {events_found['alum_trade']:>6} transactions")
            print(f"  {'Bills of exchange (innovation):':<35} {events_found['bills_of_exchange']:>6} transactions")
            
            return events_found
            
    except Exception as e:
        print(f"❌ Error checking historical events: {e}")
        return None


def validate_json_structure(filename: str) -> bool:
    """Validate the JSON file structure"""
    print(f"\n{'='*60}")
    print(f"VALIDATING JSON FILE: {filename}")
    print(f"{'='*60}\n")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"❌ JSON should contain a list of transactions")
            return False
        
        print(f"✓ Valid JSON structure")
        print(f"  Total transactions: {len(data)}")
        
        # Validate a sample
        if len(data) > 0:
            sample = data[0]
            print(f"  Sample transaction keys: {', '.join(sorted(sample.keys()))}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False


def main():
    """Main validation function"""
    print("\n" + "="*60)
    print("MEDICI BANK TRANSACTION DATA VALIDATION")
    print("="*60)
    
    # Validate CSV
    csv_valid = validate_csv_structure('medici_transactions.csv')
    
    # Validate JSON
    json_valid = validate_json_structure('medici_transactions.json')
    
    # Analyze distribution
    analyze_transaction_distribution('medici_transactions.csv')
    
    # Check historical events
    check_historical_events('medici_transactions.csv')
    
    # Final summary
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"CSV Validation:  {'✓ PASSED' if csv_valid else '❌ FAILED'}")
    print(f"JSON Validation: {'✓ PASSED' if json_valid else '❌ FAILED'}")
    
    if csv_valid and json_valid:
        print(f"\n✓ All validations passed! Data is ready for use.")
        return 0
    else:
        print(f"\n❌ Some validations failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
