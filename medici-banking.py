"""
Medici Banking System - Double-Entry Accounting in Python

This implementation showcases the core principles of double-entry accounting, using florins as
the currency in honor of the Medici banking dynasty. Here's what the code demonstrates:

1. **The Fundamental Principle**: Every transaction affects at least two accounts
   (the double-entry principle), and the sum of debits must always equal the sum of credits.

2. **Five Main Account Types**:
   - Assets: Resources owned by the business
   - Liabilities: Debts owed by the business
   - Equity: Owner's interest in the business
   - Revenue: Income earned by the business
   - Expenses: Costs incurred by the business

3. **Account Balance Rules**:
   - Assets and Expenses: Increased by debits, decreased by credits
   - Liabilities, Equity, and Revenue: Increased by credits, decreased by debits

4. **Key Financial Reports**:
   - Trial Balance: Verifies that total debits equal total credits
   - Balance Sheet: Shows Assets = Liabilities + Equity
   - Income Statement: Shows Revenue - Expenses = Net Income

The example simulates transactions for the Medici Bank in the year 1397,
including initial capitalization, loans with interest (a key banking activity),
property acquisition, and operating expenses.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
from enum import Enum, auto
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
import csv
import json


class AccountType(Enum):
    """The different types of accounts in double-entry accounting"""
    ASSET = auto()      # Resources owned by the business
    LIABILITY = auto()  # Debts owed by the business
    EQUITY = auto()     # Owner's interest in the business
    REVENUE = auto()    # Income earned by the business
    EXPENSE = auto()    # Costs incurred by the business


class Account:
    """Represents a financial account in the double-entry system"""
    
    def __init__(self, name: str, account_type: AccountType):
        self.name = name
        self.type = account_type
        self._balance = Decimal('0')
    
    @property
    def balance(self) -> Decimal:
        """Get the current balance of the account"""
        return self._balance
    
    def debit(self, amount: Decimal) -> None:
        """
        Apply a debit to the account
        
        Debits increase ASSET and EXPENSE accounts
        Debits decrease LIABILITY, EQUITY, and REVENUE accounts
        """
        if self.type in (AccountType.ASSET, AccountType.EXPENSE):
            self._balance += amount
        else:
            self._balance -= amount
    
    def credit(self, amount: Decimal) -> None:
        """
        Apply a credit to the account
        
        Credits decrease ASSET and EXPENSE accounts
        Credits increase LIABILITY, EQUITY, and REVENUE accounts
        """
        if self.type in (AccountType.ASSET, AccountType.EXPENSE):
            self._balance -= amount
        else:
            self._balance += amount
    
    def __str__(self) -> str:
        return f"{self.name} ({self.type.name}): {self._balance} florins"
    
    def __repr__(self) -> str:
        return f"Account('{self.name}', {self.type})"


@dataclass
class TransactionEntry:
    """Represents a single entry in a transaction"""
    account: Account
    amount: Decimal
    
    def __post_init__(self):
        # Ensure amount is a Decimal
        self.amount = Decimal(str(self.amount))


@dataclass
class Transaction:
    """Represents a complete financial transaction in the double-entry system"""
    date: date
    description: str
    debits: List[TransactionEntry] = field(default_factory=list)
    credits: List[TransactionEntry] = field(default_factory=list)
    
    def add_debit(self, entry: TransactionEntry) -> None:
        """Add a debit entry to the transaction"""
        self.debits.append(entry)
    
    def add_credit(self, entry: TransactionEntry) -> None:
        """Add a credit entry to the transaction"""
        self.credits.append(entry)
    
    def is_balanced(self) -> bool:
        """Check if the transaction is balanced (debits = credits)"""
        total_debits = sum(entry.amount for entry in self.debits)
        total_credits = sum(entry.amount for entry in self.credits)
        return total_debits == total_credits
    
    def post(self) -> None:
        """Post the transaction to update account balances"""
        # Apply all debits
        for entry in self.debits:
            entry.account.debit(entry.amount)
        
        # Apply all credits
        for entry in self.credits:
            entry.account.credit(entry.amount)
    
    def __str__(self) -> str:
        lines = [f"Transaction: {self.date} - {self.description}"]
        
        lines.append("  Debits:")
        for entry in self.debits:
            lines.append(f"    {entry.account.name}: {entry.amount} florins")
        
        lines.append("  Credits:")
        for entry in self.credits:
            lines.append(f"    {entry.account.name}: {entry.amount} florins")
        
        return '\n'.join(lines)


class Ledger:
    """The main ledger that keeps track of all accounts and transactions"""
    
    def __init__(self, name: str):
        self.name = name
        self.accounts: List[Account] = []
        self.transactions: List[Transaction] = []
        self._silent_mode = False  # Flag for suppressing transaction output
    
    def create_account(self, name: str, account_type: AccountType) -> Account:
        """Create a new account and add it to the ledger"""
        account = Account(name, account_type)
        self.accounts.append(account)
        return account
    
    def get_or_create_account(self, name: str, account_type: AccountType) -> Account:
        """Get an existing account by name or create a new one if it doesn't exist"""
        for account in self.accounts:
            if account.name == name:
                return account
        return self.create_account(name, account_type)
    
    def record_transaction(self, date: date, description: str, 
                          *entries: TransactionEntry) -> None:
        """
        Records a transaction with any number of debits and credits,
        ensuring that debits = credits (the fundamental principle of double-entry)
        """
        transaction = Transaction(date, description)
        
        # Separate entries into debits and credits based on account type
        for entry in entries:
            account = entry.account
            
            # For asset and expense accounts, positive amounts are debits
            # For liability, equity, and revenue accounts, positive amounts are credits
            if account.type in (AccountType.ASSET, AccountType.EXPENSE):
                if entry.amount >= 0:
                    transaction.add_debit(entry)
                else:
                    # Negative amount means we're crediting the account
                    transaction.add_credit(TransactionEntry(account, abs(entry.amount)))
            else:
                if entry.amount >= 0:
                    transaction.add_credit(entry)
                else:
                    # Negative amount means we're debiting the account
                    transaction.add_debit(TransactionEntry(account, abs(entry.amount)))
        
        # Verify that the transaction is balanced
        if not transaction.is_balanced():
            raise ValueError("Transaction is not balanced: debits must equal credits")
        
        # Post the transaction to update account balances
        transaction.post()
        
        # Record the transaction in the ledger
        self.transactions.append(transaction)
        
        # Print only if not in silent mode
        if not self._silent_mode:
            print(transaction)
    
    def print_trial_balance(self) -> None:
        """Prints a trial balance to verify that debits = credits across all accounts"""
        total_debits = Decimal('0')
        total_credits = Decimal('0')
        
        print(f"{'Account':<30} {'Debit (Florins)':<15} {'Credit (Florins)':<15}")
        print("-" * 60)
        
        for account in self.accounts:
            balance = account.balance
            
            # For the trial balance, we show positive balances in their normal position
            if account.type in (AccountType.ASSET, AccountType.EXPENSE):
                if balance > 0:
                    print(f"{account.name:<30} {balance.quantize(Decimal('0.01')):<15} {'':15}")
                    total_debits += balance
                elif balance < 0:
                    print(f"{account.name:<30} {'':15} {abs(balance).quantize(Decimal('0.01')):<15}")
                    total_credits += abs(balance)
            else:
                if balance > 0:
                    print(f"{account.name:<30} {'':15} {balance.quantize(Decimal('0.01')):<15}")
                    total_credits += balance
                elif balance < 0:
                    print(f"{account.name:<30} {abs(balance).quantize(Decimal('0.01')):<15} {'':15}")
                    total_debits += abs(balance)
        
        print("-" * 60)
        print(f"{'TOTAL':<30} {total_debits.quantize(Decimal('0.01')):<15} "
              f"{total_credits.quantize(Decimal('0.01')):<15}")
        
        if total_debits == total_credits:
            print("\nThe books are balanced! ✓")
        else:
            print("\nWARNING: The books are NOT balanced! ✗")
    
    def print_balance_sheet(self) -> None:
        """Prints a balance sheet (Assets = Liabilities + Equity)"""
        total_assets = Decimal('0')
        total_liabilities = Decimal('0')
        total_equity = Decimal('0')
        
        # Print Assets
        print("ASSETS")
        print("-" * 40)
        for account in self.accounts:
            if account.type == AccountType.ASSET and account.balance != 0:
                print(f"{account.name:<30} {account.balance.quantize(Decimal('0.01')):>10}")
                total_assets += account.balance
        print("-" * 40)
        print(f"{'TOTAL ASSETS':<30} {total_assets.quantize(Decimal('0.01')):>10}")
        print()
        
        # Print Liabilities
        print("LIABILITIES")
        print("-" * 40)
        for account in self.accounts:
            if account.type == AccountType.LIABILITY and account.balance != 0:
                print(f"{account.name:<30} {account.balance.quantize(Decimal('0.01')):>10}")
                total_liabilities += account.balance
        print("-" * 40)
        print(f"{'TOTAL LIABILITIES':<30} {total_liabilities.quantize(Decimal('0.01')):>10}")
        print()
        
        # Print Equity
        print("EQUITY")
        print("-" * 40)
        for account in self.accounts:
            if account.type == AccountType.EQUITY and account.balance != 0:
                print(f"{account.name:<30} {account.balance.quantize(Decimal('0.01')):>10}")
                total_equity += account.balance
        print("-" * 40)
        print(f"{'TOTAL EQUITY':<30} {total_equity.quantize(Decimal('0.01')):>10}")
        print()
        
        # Verify the accounting equation: Assets = Liabilities + Equity
        print("ACCOUNTING EQUATION")
        print("-" * 40)
        print(f"{'Total Assets':<30} {total_assets.quantize(Decimal('0.01')):>10}")
        print(f"{'Total Liabilities + Equity':<30} "
              f"{(total_liabilities + total_equity).quantize(Decimal('0.01')):>10}")
        
        if total_assets == total_liabilities + total_equity:
            print("\nThe accounting equation is balanced! ✓")
        else:
            print("\nWARNING: The accounting equation is NOT balanced! ✗")
    
    def print_income_statement(self) -> None:
        """Prints an income statement (Revenue - Expenses = Net Income)"""
        total_revenue = Decimal('0')
        total_expenses = Decimal('0')
        
        # Print Revenue
        print("REVENUE")
        print("-" * 40)
        for account in self.accounts:
            if account.type == AccountType.REVENUE and account.balance != 0:
                print(f"{account.name:<30} {account.balance.quantize(Decimal('0.01')):>10}")
                total_revenue += account.balance
        print("-" * 40)
        print(f"{'TOTAL REVENUE':<30} {total_revenue.quantize(Decimal('0.01')):>10}")
        print()
        
        # Print Expenses
        print("EXPENSES")
        print("-" * 40)
        for account in self.accounts:
            if account.type == AccountType.EXPENSE and account.balance != 0:
                print(f"{account.name:<30} {account.balance.quantize(Decimal('0.01')):>10}")
                total_expenses += account.balance
        print("-" * 40)
        print(f"{'TOTAL EXPENSES':<30} {total_expenses.quantize(Decimal('0.01')):>10}")
        print()
        
        # Calculate Net Income
        net_income = total_revenue - total_expenses
        print("SUMMARY")
        print("-" * 40)
        print(f"{'Total Revenue':<30} {total_revenue.quantize(Decimal('0.01')):>10}")
        print(f"{'Total Expenses':<30} {total_expenses.quantize(Decimal('0.01')):>10}")
        print("-" * 40)
        print(f"{'NET INCOME':<30} {net_income.quantize(Decimal('0.01')):>10}")
    
    def export_transactions_to_csv(self, filename: str) -> int:
        """
        Export all transactions to a CSV file
        
        Args:
            filename: Path to the CSV file to create
            
        Returns:
            Number of transactions exported
        """
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'id', 'date', 'description', 'debit_account', 'debit_amount',
                'credit_account', 'credit_amount', 'credit_account_2', 'credit_amount_2'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for idx, transaction in enumerate(self.transactions, 1):
                # Get the total debits and credits
                total_debits = sum(entry.amount for entry in transaction.debits)
                total_credits = sum(entry.amount for entry in transaction.credits)
                
                # Format the transaction for CSV
                row = {
                    'id': idx,
                    'date': transaction.date.isoformat(),
                    'description': transaction.description,
                    'debit_account': ', '.join([entry.account.name for entry in transaction.debits]),
                    'debit_amount': str(total_debits),
                    'credit_account': transaction.credits[0].account.name if transaction.credits else '',
                    'credit_amount': str(transaction.credits[0].amount) if transaction.credits else '0',
                    'credit_account_2': transaction.credits[1].account.name if len(transaction.credits) > 1 else '',
                    'credit_amount_2': str(transaction.credits[1].amount) if len(transaction.credits) > 1 else ''
                }
                writer.writerow(row)
        
        return len(self.transactions)
    
    def export_transactions_to_json(self, filename: str) -> int:
        """
        Export all transactions to a JSON file
        
        Args:
            filename: Path to the JSON file to create
            
        Returns:
            Number of transactions exported
        """
        transactions_data = []
        
        for idx, transaction in enumerate(self.transactions, 1):
            trans_dict = {
                'id': idx,
                'date': transaction.date.isoformat(),
                'description': transaction.description,
                'debits': [
                    {
                        'account': entry.account.name,
                        'account_type': entry.account.type.name,
                        'amount': str(entry.amount)
                    }
                    for entry in transaction.debits
                ],
                'credits': [
                    {
                        'account': entry.account.name,
                        'account_type': entry.account.type.name,
                        'amount': str(entry.amount)
                    }
                    for entry in transaction.credits
                ]
            }
            transactions_data.append(trans_dict)
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(transactions_data, jsonfile, indent=2)
        
        return len(self.transactions)
    
    def import_transactions_from_csv(self, filename: str, verbose: bool = False) -> int:
        """
        Import transactions from a CSV file
        
        Args:
            filename: Path to the CSV file to import
            verbose: If True, print each transaction as it's imported
            
        Returns:
            Number of transactions imported
        """
        count = 0
        row_num = 1  # Track row number (1 = header)
        
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                row_num += 1
                try:
                    # Parse the transaction date
                    trans_date = datetime.fromisoformat(row['date']).date()
                    description = row['description']
                    
                    # Parse debit entries
                    debit_accounts = [acc.strip() for acc in row.get('debit_account', '').split(',') if acc.strip()]
                    debit_amount = Decimal(row.get('debit_amount', '0'))
                    
                    # Parse credit entries
                    credit_account = row.get('credit_account', '').strip()
                    credit_amount = Decimal(row.get('credit_amount', '0'))
                    credit_account_2 = row.get('credit_account_2', '').strip()
                    credit_amount_2 = Decimal(row.get('credit_amount_2', '0')) if row.get('credit_amount_2') else Decimal('0')
                    
                    # Create the transaction directly
                    transaction = Transaction(trans_date, description)
                    
                    # Add debit entries
                    # Note: CSV format doesn't track individual debit amounts, so we
                    # distribute the total equally. For precise multi-debit transactions,
                    # use JSON format which preserves individual amounts.
                    for debit_acc_name in debit_accounts:
                        account_type = self._infer_account_type(debit_acc_name)
                        debit_account = self.get_or_create_account(debit_acc_name, account_type)
                        transaction.add_debit(TransactionEntry(debit_account, debit_amount / len(debit_accounts)))
                    
                    # Add credit entries
                    if credit_account:
                        account_type = self._infer_account_type(credit_account)
                        credit_acc = self.get_or_create_account(credit_account, account_type)
                        transaction.add_credit(TransactionEntry(credit_acc, credit_amount))
                    
                    if credit_account_2 and credit_amount_2 > 0:
                        account_type = self._infer_account_type(credit_account_2)
                        credit_acc_2 = self.get_or_create_account(credit_account_2, account_type)
                        transaction.add_credit(TransactionEntry(credit_acc_2, credit_amount_2))
                    
                    # Verify that the transaction is balanced
                    if not transaction.is_balanced():
                        raise ValueError("Transaction is not balanced: debits must equal credits")
                    
                    # Post the transaction to update account balances
                    transaction.post()
                    
                    # Record the transaction in the ledger
                    self.transactions.append(transaction)
                    
                    # Print if verbose
                    if verbose:
                        print(transaction)
                    
                    count += 1
                    
                except (ValueError, KeyError) as e:
                    if verbose:
                        print(f"Warning: Skipping invalid transaction at row {row_num}: {e}")
                    continue
        
        return count
    
    def import_transactions_from_json(self, filename: str, verbose: bool = False) -> int:
        """
        Import transactions from a JSON file
        
        Args:
            filename: Path to the JSON file to import
            verbose: If True, print each transaction as it's imported
            
        Returns:
            Number of transactions imported
        """
        count = 0
        
        with open(filename, 'r', encoding='utf-8') as jsonfile:
            transactions_data = json.load(jsonfile)
        
        for trans_dict in transactions_data:
            try:
                # Parse the transaction
                trans_date = datetime.fromisoformat(trans_dict['date']).date()
                description = trans_dict['description']
                
                # Create the transaction directly
                transaction = Transaction(trans_date, description)
                
                # Add debit entries
                for debit_entry in trans_dict.get('debits', []):
                    account_type = AccountType[debit_entry['account_type']]
                    debit_account = self.get_or_create_account(debit_entry['account'], account_type)
                    amount = Decimal(debit_entry['amount'])
                    transaction.add_debit(TransactionEntry(debit_account, amount))
                
                # Add credit entries
                for credit_entry in trans_dict.get('credits', []):
                    account_type = AccountType[credit_entry['account_type']]
                    credit_account = self.get_or_create_account(credit_entry['account'], account_type)
                    amount = Decimal(credit_entry['amount'])
                    transaction.add_credit(TransactionEntry(credit_account, amount))
                
                # Verify that the transaction is balanced
                if not transaction.is_balanced():
                    raise ValueError("Transaction is not balanced: debits must equal credits")
                
                # Post the transaction to update account balances
                transaction.post()
                
                # Record the transaction in the ledger
                self.transactions.append(transaction)
                
                # Print if verbose
                if verbose:
                    print(transaction)
                
                count += 1
                
            except (ValueError, KeyError) as e:
                if verbose:
                    print(f"Warning: Skipping invalid transaction: {e}")
                continue
        
        return count
    
    def _infer_account_type(self, account_name: str) -> AccountType:
        """
        Infer the account type from the account name
        This is a heuristic-based approach for CSV imports where type isn't explicit.
        
        Note: Defaults to ASSET if account type cannot be determined. This is a safe
        default for unknown accounts as most banking transactions involve asset accounts.
        For precise type control, use JSON import which preserves account types.
        """
        name_lower = account_name.lower()
        
        # Asset accounts
        if any(keyword in name_lower for keyword in ['cash', 'receivable', 'inventory', 'land', 'building', 'equipment', 'asset']):
            return AccountType.ASSET
        
        # Liability accounts
        if any(keyword in name_lower for keyword in ['payable', 'loan', 'debt', 'liability', 'deposits payable']):
            return AccountType.LIABILITY
        
        # Equity accounts
        if any(keyword in name_lower for keyword in ['capital', 'equity', 'retained earnings', 'owner']):
            return AccountType.EQUITY
        
        # Revenue accounts
        if any(keyword in name_lower for keyword in ['revenue', 'income', 'sales', 'interest income', 'fee']):
            return AccountType.REVENUE
        
        # Expense accounts
        if any(keyword in name_lower for keyword in ['expense', 'wages', 'rent', 'supplies', 'maintenance', 'courier', 'cost']):
            return AccountType.EXPENSE
        
        # Default to ASSET if we can't determine
        return AccountType.ASSET


def main():
    """
    A double-entry accounting system implementation inspired by the
    Florentine banking practices of the Medici family.
    """
    # Create a new ledger for our banking operations
    medici_ledger = Ledger("Medici Family Bank")
    
    # Define our chart of accounts
    cash = medici_ledger.create_account("Cash", AccountType.ASSET)
    accounts_receivable = medici_ledger.create_account("Accounts Receivable", AccountType.ASSET)
    inventory = medici_ledger.create_account("Inventory", AccountType.ASSET)
    land = medici_ledger.create_account("Land", AccountType.ASSET)
    
    accounts_payable = medici_ledger.create_account("Accounts Payable", AccountType.LIABILITY)
    loans = medici_ledger.create_account("Loans", AccountType.LIABILITY)
    
    capital = medici_ledger.create_account("Owner's Capital", AccountType.EQUITY)
    retained_earnings = medici_ledger.create_account("Retained Earnings", AccountType.EQUITY)
    
    revenue = medici_ledger.create_account("Revenue", AccountType.REVENUE)
    interest_income = medici_ledger.create_account("Interest Income", AccountType.REVENUE)
    
    expenses = medici_ledger.create_account("Expenses", AccountType.EXPENSE)
    wages = medici_ledger.create_account("Wages", AccountType.EXPENSE)
    
    # Starting our banking operations with initial capital
    print("=== STARTING THE MEDICI BANK ===")
    medici_ledger.record_transaction(
        date(1397, 1, 1),
        "Initial investment from Giovanni de' Medici",
        TransactionEntry(cash, Decimal("10000.00")),
        TransactionEntry(capital, Decimal("10000.00"))
    )
    
    # Recording a loan to a wool merchant
    medici_ledger.record_transaction(
        date(1397, 2, 15),
        "Loan to Wool Merchant",
        TransactionEntry(accounts_receivable, Decimal("2000.00")),
        TransactionEntry(cash, Decimal("-2000.00"))
    )
    
    # Receiving partial payment with interest
    medici_ledger.record_transaction(
        date(1397, 8, 10),
        "Partial loan repayment from Wool Merchant with interest",
        TransactionEntry(cash, Decimal("1200.00")),
        TransactionEntry(accounts_receivable, Decimal("-1000.00")),
        TransactionEntry(interest_income, Decimal("200.00"))
    )
    
    # Purchasing land for a new banking house
    medici_ledger.record_transaction(
        date(1397, 9, 5),
        "Purchase of land for new Medici banking house",
        TransactionEntry(land, Decimal("3000.00")),
        TransactionEntry(cash, Decimal("-3000.00"))
    )
    
    # Paying wages to bank employees
    medici_ledger.record_transaction(
        date(1397, 12, 1),
        "Quarterly wages for bank employees",
        TransactionEntry(wages, Decimal("800.00")),
        TransactionEntry(cash, Decimal("-800.00"))
    )
    
    # Print the trial balance to verify our accounting is balanced
    print("\n=== MEDICI BANK TRIAL BALANCE (Year 1397) ===")
    medici_ledger.print_trial_balance()
    
    # Print the balance sheet
    print("\n=== MEDICI BANK BALANCE SHEET (Year 1397) ===")
    medici_ledger.print_balance_sheet()
    
    # Print the income statement
    print("\n=== MEDICI BANK INCOME STATEMENT (Year 1397) ===")
    medici_ledger.print_income_statement()


if __name__ == "__main__":
    main()
