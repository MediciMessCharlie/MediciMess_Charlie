"""
Medici Bank Historical Transaction Data Generator

Generates approximately 20,000 historical transactions based on actual events
from the Medici Bank's operations during 1390-1440, including:
- Western Schism and Papal Banking
- Florentine-Milanese Wars
- Council of Constance
- Wars in Lombardy
- Regular banking operations across branches
"""

import csv
import json
import random
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple

# Historical context and transaction types
class HistoricalPeriod:
    """Defines major historical periods and their characteristics"""
    
    WESTERN_SCHISM = {
        "start": date(1390, 1, 1),
        "end": date(1417, 12, 31),
        "description": "Western Schism period with papal banking opportunities"
    }
    
    PAPAL_BANKING_BOOM = {
        "start": date(1410, 1, 1),
        "end": date(1430, 12, 31),
        "description": "Peak papal banking period after John XXIII appointment"
    }
    
    FIRST_MILANESE_WAR = {
        "start": date(1390, 1, 1),
        "end": date(1402, 9, 3),
        "description": "First Florentine-Milanese War under Gian Galeazzo"
    }
    
    COUNCIL_CONSTANCE = {
        "start": date(1414, 11, 16),
        "end": date(1418, 4, 22),
        "description": "Council of Constance and John XXIII ransom"
    }
    
    SECOND_MILANESE_WAR = {
        "start": date(1422, 1, 1),
        "end": date(1426, 12, 31),
        "description": "Second Florentine-Milanese War"
    }
    
    LOMBARDY_WARS = {
        "start": date(1423, 1, 1),
        "end": date(1440, 12, 31),
        "description": "Wars in Lombardy between Venice and Milan"
    }
    
    COSIMO_EXILE = {
        "start": date(1433, 9, 7),
        "end": date(1434, 10, 6),
        "description": "Cosimo's exile to Venice and return"
    }


class TransactionGenerator:
    """Generates historically-themed banking transactions"""
    
    def __init__(self, seed=42):
        random.seed(seed)
        self.transaction_id = 1
        self.branches = ["Florence", "Rome", "Venice", "Milan", "Geneva", "Bruges", "London", "Avignon"]
        self.currencies = ["florin", "ducat", "scudo", "lira"]
        
        # Transaction categories with historical context
        self.merchants = [
            "Wool Merchant", "Silk Trader", "Spice Merchant", "Cloth Merchant",
            "Wine Trader", "Gold Merchant", "Jewel Trader", "Grain Merchant",
            "Armor Smith", "Textile Merchant", "Banking House", "Trading Company"
        ]
        
        self.nobles = [
            "Duke of Milan", "Doge of Venice", "King of Naples", "Cardinal",
            "Archbishop", "Count of Urbino", "Marquis", "Baron", "Lord"
        ]
        
        self.papal_entities = [
            "Papal Curia", "Vatican Treasury", "Cardinal's Office", "Papal Court",
            "Holy See", "Apostolic Chamber", "Sacred College"
        ]
        
    def random_date(self, start: date, end: date) -> date:
        """Generate a random date between start and end"""
        delta = end - start
        random_days = random.randint(0, delta.days)
        return start + timedelta(days=random_days)
    
    def random_amount(self, min_amount: int, max_amount: int) -> Decimal:
        """Generate a random amount in florins"""
        # Use exponential distribution to get realistic banking amounts
        # (most transactions small, some very large)
        base = random.uniform(min_amount, max_amount)
        factor = random.choice([1, 1, 1, 2, 5, 10, 20, 50])  # Weighted toward smaller multipliers
        amount = base * factor
        # Use Decimal.quantize for precise decimal handling
        return Decimal(str(amount)).quantize(Decimal('0.01'))
    
    def generate_papal_deposit(self, transaction_date: date) -> Dict:
        """Generate papal banking deposits (major income source)"""
        branch = "Rome"
        entity = random.choice(self.papal_entities)
        amount = self.random_amount(500, 50000)  # Large deposits from papal sources
        
        return {
            "id": self.transaction_id,
            "date": transaction_date.isoformat(),
            "branch": branch,
            "type": "deposit",
            "counterparty": entity,
            "description": f"Deposit from {entity} to Rome branch",
            "debit_account": "Cash",
            "debit_amount": float(amount),
            "credit_account": "Deposits Payable",
            "credit_amount": float(amount),
            "currency": "florin"
        }
    
    def generate_loan_issuance(self, transaction_date: date) -> List[Dict]:
        """Generate loan to merchant or noble"""
        branch = random.choice(self.branches)
        is_noble = random.random() > 0.7
        counterparty = random.choice(self.nobles if is_noble else self.merchants)
        
        # Nobles get larger loans
        if is_noble:
            amount = self.random_amount(1000, 100000)
        else:
            amount = self.random_amount(100, 10000)
        
        transactions = []
        
        # Loan disbursement
        self.transaction_id += 1
        transactions.append({
            "id": self.transaction_id,
            "date": transaction_date.isoformat(),
            "branch": branch,
            "type": "loan_issuance",
            "counterparty": counterparty,
            "description": f"Loan issued to {counterparty} from {branch} branch",
            "debit_account": "Loans Receivable",
            "debit_amount": float(amount),
            "credit_account": "Cash",
            "credit_amount": float(amount),
            "currency": "florin"
        })
        
        return transactions
    
    def generate_loan_repayment(self, transaction_date: date) -> Dict:
        """Generate loan repayment with interest"""
        branch = random.choice(self.branches)
        is_noble = random.random() > 0.7
        counterparty = random.choice(self.nobles if is_noble else self.merchants)
        
        principal = self.random_amount(100, 10000)
        # Generate interest rate as Decimal to avoid floating-point precision issues
        interest_rate = Decimal(random.randint(8, 25)) / Decimal('100')  # 8-25% interest
        interest = principal * interest_rate
        total = principal + interest
        
        return {
            "id": self.transaction_id,
            "date": transaction_date.isoformat(),
            "branch": branch,
            "type": "loan_repayment",
            "counterparty": counterparty,
            "description": f"Loan repayment from {counterparty} with interest",
            "debit_account": "Cash",
            "debit_amount": float(total),
            "credit_account": "Loans Receivable",
            "credit_amount": float(principal),
            "credit_account_2": "Interest Income",
            "credit_amount_2": float(interest),
            "currency": "florin"
        }
    
    def generate_war_financing(self, transaction_date: date, war_type: str) -> Dict:
        """Generate war-related financing transactions"""
        amount = self.random_amount(5000, 200000)  # Wars are expensive
        
        description_map = {
            "milan": f"War financing for Florentine operations against Milan",
            "venice": f"Loan to Venice for Lombardy Wars operations",
            "defensive": f"Emergency war financing for Florence defense"
        }
        
        return {
            "id": self.transaction_id,
            "date": transaction_date.isoformat(),
            "branch": "Florence",
            "type": "war_financing",
            "counterparty": "Republic of Florence",
            "description": description_map.get(war_type, "War financing"),
            "debit_account": "Loans Receivable - Government",
            "debit_amount": float(amount),
            "credit_account": "Cash",
            "credit_amount": float(amount),
            "currency": "florin"
        }
    
    def generate_alum_trade(self, transaction_date: date) -> Dict:
        """Generate alum trade transactions (papal monopoly)"""
        branch = random.choice(["Rome", "Florence", "Venice"])
        amount = self.random_amount(200, 5000)
        
        return {
            "id": self.transaction_id,
            "date": transaction_date.isoformat(),
            "branch": branch,
            "type": "alum_trade",
            "counterparty": random.choice(self.merchants),
            "description": f"Alum sale from papal mines",
            "debit_account": "Cash",
            "debit_amount": float(amount),
            "credit_account": "Trading Revenue",
            "credit_amount": float(amount),
            "currency": "florin"
        }
    
    def generate_bills_of_exchange(self, transaction_date: date) -> Dict:
        """Generate bills of exchange (international banking innovation)"""
        from_branch = random.choice(self.branches)
        to_branch = random.choice([b for b in self.branches if b != from_branch])
        amount = self.random_amount(500, 20000)
        
        # Small exchange fee (profit center) - use Decimal for precision
        fee_rate = Decimal(random.randint(100, 300)) / Decimal('10000')  # 1-3% fee
        fee = amount * fee_rate
        
        return {
            "id": self.transaction_id,
            "date": transaction_date.isoformat(),
            "branch": from_branch,
            "type": "bill_of_exchange",
            "counterparty": f"Transfer to {to_branch}",
            "description": f"Bill of exchange from {from_branch} to {to_branch}",
            "debit_account": f"Due from {to_branch}",
            "debit_amount": float(amount),
            "credit_account": "Cash",
            "credit_amount": float(amount - fee),
            "credit_account_2": "Exchange Fee Revenue",
            "credit_amount_2": float(fee),
            "currency": "florin"
        }
    
    def generate_operating_expense(self, transaction_date: date) -> Dict:
        """Generate daily operating expenses"""
        branch = random.choice(self.branches)
        expense_types = [
            ("Wages", 100, 2000),
            ("Rent", 50, 500),
            ("Supplies", 20, 300),
            ("Courier Services", 10, 100),
            ("Security", 50, 500),
            ("Maintenance", 30, 400)
        ]
        
        expense_type, min_amt, max_amt = random.choice(expense_types)
        amount = self.random_amount(min_amt, max_amt)
        
        return {
            "id": self.transaction_id,
            "date": transaction_date.isoformat(),
            "branch": branch,
            "type": "operating_expense",
            "counterparty": f"{branch} Operations",
            "description": f"{expense_type} expense for {branch} branch",
            "debit_account": expense_type,
            "debit_amount": float(amount),
            "credit_account": "Cash",
            "credit_amount": float(amount),
            "currency": "florin"
        }
    
    def generate_deposit_withdrawal(self, transaction_date: date) -> Dict:
        """Generate customer deposit or withdrawal"""
        branch = random.choice(self.branches)
        is_withdrawal = random.random() > 0.5
        counterparty = random.choice(self.merchants + self.nobles)
        amount = self.random_amount(100, 15000)
        
        if is_withdrawal:
            return {
                "id": self.transaction_id,
                "date": transaction_date.isoformat(),
                "branch": branch,
                "type": "withdrawal",
                "counterparty": counterparty,
                "description": f"Withdrawal by {counterparty}",
                "debit_account": "Deposits Payable",
                "debit_amount": float(amount),
                "credit_account": "Cash",
                "credit_amount": float(amount),
                "currency": "florin"
            }
        else:
            return {
                "id": self.transaction_id,
                "date": transaction_date.isoformat(),
                "branch": branch,
                "type": "deposit",
                "counterparty": counterparty,
                "description": f"Deposit by {counterparty}",
                "debit_account": "Cash",
                "debit_amount": float(amount),
                "credit_account": "Deposits Payable",
                "credit_amount": float(amount),
                "currency": "florin"
            }
    
    def generate_constance_ransom(self) -> List[Dict]:
        """Generate the specific 35,000 florin ransom for Pope John XXIII"""
        transactions = []
        ransom_date = date(1415, 5, 29)  # John XXIII deposed
        total_ransom = Decimal('35000.00')
        
        # The ransom payment (major historical event)
        self.transaction_id += 1
        transactions.append({
            "id": self.transaction_id,
            "date": ransom_date.isoformat(),
            "branch": "Constance",
            "type": "ransom_payment",
            "counterparty": "Council of Constance - Pope John XXIII Ransom",
            "description": "Payment of 35,000 florin ransom for Pope John XXIII",
            "debit_account": "Papal Receivable",
            "debit_amount": float(total_ransom),
            "credit_account": "Cash",
            "credit_amount": float(total_ransom),
            "currency": "florin"
        })
        
        return transactions
    
    def generate_transactions(self, num_transactions: int = 20000) -> List[Dict]:
        """Generate the full set of historical transactions"""
        transactions = []
        
        # Start and end dates for our simulation
        start_date = date(1390, 1, 1)
        end_date = date(1440, 12, 31)
        
        # Special historical event: Council of Constance ransom
        constance_transactions = self.generate_constance_ransom()
        transactions.extend(constance_transactions)
        self.transaction_id += 1
        
        # Distribution of transaction types (percentages)
        transaction_weights = {
            "papal_deposit": 0.15,      # 15% - Major income source
            "loan_issuance": 0.12,      # 12% - Core banking activity
            "loan_repayment": 0.13,     # 13% - Core banking activity
            "deposit_withdrawal": 0.20,  # 20% - Regular customer activity
            "bills_of_exchange": 0.10,   # 10% - International banking
            "alum_trade": 0.08,          # 8% - Papal monopoly trade
            "war_financing": 0.05,       # 5% - Wars (high amounts)
            "operating_expense": 0.17    # 17% - Daily operations
        }
        
        # Generate remaining transactions
        while len(transactions) < num_transactions:
            # Random date in our historical period
            trans_date = self.random_date(start_date, end_date)
            
            # Choose transaction type based on weights
            rand = random.random()
            cumulative = 0
            trans_type = None
            
            for t_type, weight in transaction_weights.items():
                cumulative += weight
                if rand <= cumulative:
                    trans_type = t_type
                    break
            
            # Increase papal banking during boom period
            if (HistoricalPeriod.PAPAL_BANKING_BOOM["start"] <= trans_date 
                <= HistoricalPeriod.PAPAL_BANKING_BOOM["end"]):
                if random.random() < 0.3:  # 30% chance to override with papal transaction
                    trans_type = "papal_deposit"
            
            # Increase war financing during war periods
            war_periods = [
                HistoricalPeriod.FIRST_MILANESE_WAR,
                HistoricalPeriod.SECOND_MILANESE_WAR,
                HistoricalPeriod.LOMBARDY_WARS
            ]
            
            in_war_period = any(period["start"] <= trans_date <= period["end"] 
                               for period in war_periods)
            if in_war_period and random.random() < 0.15:  # 15% chance during wars
                trans_type = "war_financing"
            
            # Generate transaction based on type
            try:
                if trans_type == "papal_deposit":
                    trans = self.generate_papal_deposit(trans_date)
                elif trans_type == "loan_issuance":
                    trans_list = self.generate_loan_issuance(trans_date)
                    transactions.extend(trans_list)
                    continue
                elif trans_type == "loan_repayment":
                    trans = self.generate_loan_repayment(trans_date)
                elif trans_type == "deposit_withdrawal":
                    trans = self.generate_deposit_withdrawal(trans_date)
                elif trans_type == "bills_of_exchange":
                    trans = self.generate_bills_of_exchange(trans_date)
                elif trans_type == "alum_trade":
                    trans = self.generate_alum_trade(trans_date)
                elif trans_type == "war_financing":
                    war_type = random.choice(["milan", "venice", "defensive"])
                    trans = self.generate_war_financing(trans_date, war_type)
                elif trans_type == "operating_expense":
                    trans = self.generate_operating_expense(trans_date)
                else:
                    continue
                
                self.transaction_id += 1
                transactions.append(trans)
                
            except (ValueError, KeyError) as e:
                # Specific exceptions for transaction generation failures
                print(f"Error generating {trans_type}: {e}")
                continue
        
        # Sort by date
        transactions.sort(key=lambda x: x["date"])
        
        # Renumber transactions sequentially
        for idx, trans in enumerate(transactions, 1):
            trans["id"] = idx
        
        return transactions[:num_transactions]


def save_to_csv(transactions: List[Dict], filename: str):
    """Save transactions to CSV file"""
    if not transactions:
        print("No transactions to save")
        return
    
    # Get all unique field names
    fieldnames = set()
    for trans in transactions:
        fieldnames.update(trans.keys())
    
    fieldnames = sorted(list(fieldnames))
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
    
    print(f"Saved {len(transactions)} transactions to {filename}")


def save_to_json(transactions: List[Dict], filename: str):
    """Save transactions to JSON file"""
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(transactions, jsonfile, indent=2)
    
    print(f"Saved {len(transactions)} transactions to {filename}")


def print_summary(transactions: List[Dict]):
    """Print summary statistics of generated transactions"""
    print("\n" + "="*60)
    print("MEDICI BANK HISTORICAL TRANSACTION SUMMARY")
    print("="*60)
    
    print(f"\nTotal Transactions: {len(transactions)}")
    
    # Count by type
    type_counts = {}
    for trans in transactions:
        t_type = trans.get("type", "unknown")
        type_counts[t_type] = type_counts.get(t_type, 0) + 1
    
    print("\nTransactions by Type:")
    for t_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(transactions)) * 100
        print(f"  {t_type:25s}: {count:5d} ({percentage:5.2f}%)")
    
    # Count by branch
    branch_counts = {}
    for trans in transactions:
        branch = trans.get("branch", "unknown")
        branch_counts[branch] = branch_counts.get(branch, 0) + 1
    
    print("\nTransactions by Branch:")
    for branch, count in sorted(branch_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(transactions)) * 100
        print(f"  {branch:15s}: {count:5d} ({percentage:5.2f}%)")
    
    # Date range
    dates = [trans["date"] for trans in transactions]
    print(f"\nDate Range: {min(dates)} to {max(dates)}")
    
    # Calculate total monetary volume
    total_volume = sum(trans.get("debit_amount", 0) for trans in transactions)
    print(f"\nTotal Transaction Volume: {total_volume:,.2f} florins")
    
    print("="*60)


def main():
    """Main function to generate historical transaction data"""
    print("Generating Medici Bank Historical Transaction Data...")
    print("Based on events from 1390-1440")
    print()
    
    # Create generator
    generator = TransactionGenerator(seed=42)
    
    # Generate 20,000 transactions
    num_transactions = 20000
    transactions = generator.generate_transactions(num_transactions)
    
    # Print summary
    print_summary(transactions)
    
    # Save to files
    save_to_csv(transactions, "medici_transactions.csv")
    save_to_json(transactions, "medici_transactions.json")
    
    print("\nData generation complete!")
    print("\nGenerated files:")
    print("  - medici_transactions.csv")
    print("  - medici_transactions.json")


if __name__ == "__main__":
    main()
