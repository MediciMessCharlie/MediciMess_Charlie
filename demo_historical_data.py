"""
Demonstration: Analyzing Historical Transaction Data

This script demonstrates how to analyze the historical transaction dataset
and provides summary statistics and insights.
"""

import csv
from decimal import Decimal
from datetime import datetime
from collections import defaultdict, Counter


def analyze_transactions(filename, max_display=20):
    """
    Analyze transactions from CSV
    
    Args:
        filename: Path to the CSV file
        max_display: Maximum number of sample transactions to display
    """
    print(f"\nAnalyzing transactions from {filename}...\n")
    
    # Statistics collectors
    total_volume = Decimal('0')
    by_type = defaultdict(lambda: {'count': 0, 'volume': Decimal('0')})
    by_branch = defaultdict(lambda: {'count': 0, 'volume': Decimal('0')})
    by_year = defaultdict(lambda: {'count': 0, 'volume': Decimal('0')})
    
    all_transactions = []
    transaction_count = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            transaction_count += 1
            all_transactions.append(row)
            
            # Extract data
            trans_type = row['type']
            branch = row['branch']
            year = row['date'][:4]
            amount = Decimal(row['debit_amount'])
            
            # Accumulate statistics
            total_volume += amount
            by_type[trans_type]['count'] += 1
            by_type[trans_type]['volume'] += amount
            by_branch[branch]['count'] += 1
            by_branch[branch]['volume'] += amount
            by_year[year]['count'] += 1
            by_year[year]['volume'] += amount
    
    return {
        'total_count': transaction_count,
        'total_volume': total_volume,
        'by_type': dict(by_type),
        'by_branch': dict(by_branch),
        'by_year': dict(by_year),
        'transactions': all_transactions[:max_display]
    }


def print_analysis(stats):
    """Print analysis results"""
    
    print("="*70)
    print("OVERALL STATISTICS")
    print("="*70)
    print(f"Total Transactions: {stats['total_count']:,}")
    print(f"Total Volume: {stats['total_volume']:,.2f} florins")
    print(f"Average Transaction: {stats['total_volume'] / stats['total_count']:,.2f} florins")
    
    print("\n" + "="*70)
    print("TRANSACTIONS BY TYPE")
    print("="*70)
    print(f"{'Type':<25} {'Count':<10} {'Volume (florins)':<20} {'Avg':<15}")
    print("-"*70)
    for t_type, data in sorted(stats['by_type'].items(), 
                               key=lambda x: x[1]['count'], reverse=True):
        avg = data['volume'] / data['count']
        pct = (data['count'] / stats['total_count']) * 100
        print(f"{t_type:<25} {data['count']:<10} {data['volume']:>18,.2f} "
              f"{avg:>13,.2f}")
    
    print("\n" + "="*70)
    print("TRANSACTIONS BY BRANCH")
    print("="*70)
    print(f"{'Branch':<15} {'Count':<10} {'% of Total':<12} {'Volume (florins)':<20}")
    print("-"*70)
    for branch, data in sorted(stats['by_branch'].items(), 
                               key=lambda x: x[1]['count'], reverse=True):
        pct = (data['count'] / stats['total_count']) * 100
        print(f"{branch:<15} {data['count']:<10} {pct:>10.2f}% "
              f"{data['volume']:>18,.2f}")
    
    print("\n" + "="*70)
    print("SAMPLE TRANSACTIONS (First 20)")
    print("="*70)
    print(f"{'Date':<12} {'Branch':<10} {'Type':<20} {'Amount':<15}")
    print("-"*70)
    for trans in stats['transactions']:
        amount = float(trans['debit_amount'])
        print(f"{trans['date']:<12} {trans['branch']:<10} "
              f"{trans['type']:<20} {amount:>13,.2f}")


def find_significant_events(filename):
    """Find and display significant historical events"""
    print("\n" + "="*70)
    print("SIGNIFICANT HISTORICAL EVENTS")
    print("="*70)
    
    events_found = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Look for the ransom payment
            if 'ransom' in row['type'].lower() or 'John XXIII' in row.get('description', ''):
                events_found.append({
                    'name': 'Council of Constance Ransom',
                    'date': row['date'],
                    'amount': float(row['debit_amount']),
                    'description': row['description']
                })
            
            # Look for very large transactions (>500,000 florins)
            elif float(row['debit_amount']) > 500000:
                events_found.append({
                    'name': 'Major Transaction',
                    'date': row['date'],
                    'amount': float(row['debit_amount']),
                    'description': row['description'][:60] + '...' if len(row['description']) > 60 else row['description']
                })
    
    # Sort by amount descending
    events_found.sort(key=lambda x: x['amount'], reverse=True)
    
    print("\nTop 10 Largest Transactions:\n")
    for i, event in enumerate(events_found[:10], 1):
        print(f"{i}. {event['name']}")
        print(f"   Date: {event['date']}")
        print(f"   Amount: {event['amount']:,.2f} florins")
        print(f"   {event['description']}")
        print()


def main():
    """Main demonstration function"""
    print("="*70)
    print("MEDICI BANK - HISTORICAL TRANSACTION DATA ANALYSIS")
    print("="*70)
    print("\nThis analysis examines the full dataset of 20,000 historical")
    print("transactions from the Medici Bank operations (1390-1440).\n")
    
    try:
        # Analyze the data
        stats = analyze_transactions('medici_transactions.csv', max_display=20)
        
        # Print analysis
        print_analysis(stats)
        
        # Find significant events
        find_significant_events('medici_transactions.csv')
        
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)
        print("\nFor more details, see:")
        print("  - medici_transactions.csv (full dataset)")
        print("  - medici_transactions.json (JSON format)")
        print("  - TRANSACTION_DATA.md (documentation)")
        print("  - validate_transactions.py (data validation)")
        print("="*70)
        
        return 0
        
    except FileNotFoundError:
        print("\n❌ Error: medici_transactions.csv not found.")
        print("Please run generate_historical_data.py first.")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
