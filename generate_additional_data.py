"""
Additional Transaction Generator for Medici Bank Dataset

This script:
1. Appends 60,000 more historically-themed transactions to the existing dataset.
2. Injects a hidden embezzlement trail (~100,000 florins over 1420-1425) using the
   ghost-vendor technique, designed to look plausible in isolation but detectable
   through simple forensic analysis.

Usage:
    python3 generate_additional_data.py

Output:
    Updates medici_transactions.csv and medici_transactions.json in place.
"""

import csv
import json
import random
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict


# ──────────────────────────────────────────────────────────────────────────────
# Re-use the same generator infrastructure as generate_historical_data.py
# ──────────────────────────────────────────────────────────────────────────────

class HistoricalPeriod:
    WESTERN_SCHISM = {"start": date(1390, 1, 1), "end": date(1417, 12, 31)}
    PAPAL_BANKING_BOOM = {"start": date(1410, 1, 1), "end": date(1430, 12, 31)}
    FIRST_MILANESE_WAR = {"start": date(1390, 1, 1), "end": date(1402, 9, 3)}
    COUNCIL_CONSTANCE = {"start": date(1414, 11, 16), "end": date(1418, 4, 22)}
    SECOND_MILANESE_WAR = {"start": date(1422, 1, 1), "end": date(1426, 12, 31)}
    LOMBARDY_WARS = {"start": date(1423, 1, 1), "end": date(1440, 12, 31)}


class TransactionGenerator:
    """Generates historically-themed banking transactions (same logic as generate_historical_data.py)."""

    def __init__(self, seed=99):
        random.seed(seed)
        self.transaction_id = 1
        self.branches = ["Florence", "Rome", "Venice", "Milan", "Geneva", "Bruges", "London", "Avignon"]
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
        delta = end - start
        return start + timedelta(days=random.randint(0, delta.days))

    def random_amount(self, min_amount: int, max_amount: int) -> Decimal:
        base = random.uniform(min_amount, max_amount)
        factor = random.choice([1, 1, 1, 2, 5, 10, 20, 50])
        return Decimal(str(base * factor)).quantize(Decimal("0.01"))

    def generate_papal_deposit(self, transaction_date: date) -> Dict:
        entity = random.choice(self.papal_entities)
        amount = self.random_amount(500, 50000)
        return {
            "id": self.transaction_id,
            "date": transaction_date.isoformat(),
            "branch": "Rome",
            "type": "deposit",
            "counterparty": entity,
            "description": f"Deposit from {entity} to Rome branch",
            "debit_account": "Cash",
            "debit_amount": float(amount),
            "credit_account": "Deposits Payable",
            "credit_amount": float(amount),
            "currency": "florin",
        }

    def generate_loan_issuance(self, transaction_date: date) -> List[Dict]:
        branch = random.choice(self.branches)
        is_noble = random.random() > 0.7
        counterparty = random.choice(self.nobles if is_noble else self.merchants)
        amount = self.random_amount(1000, 100000) if is_noble else self.random_amount(100, 10000)
        self.transaction_id += 1
        return [{
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
            "currency": "florin",
        }]

    def generate_loan_repayment(self, transaction_date: date) -> Dict:
        branch = random.choice(self.branches)
        is_noble = random.random() > 0.7
        counterparty = random.choice(self.nobles if is_noble else self.merchants)
        principal = self.random_amount(100, 10000)
        interest_rate = Decimal(random.randint(8, 25)) / Decimal("100")
        interest = (principal * interest_rate).quantize(Decimal("0.01"))
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
            "currency": "florin",
        }

    def generate_war_financing(self, transaction_date: date, war_type: str) -> Dict:
        amount = self.random_amount(5000, 200000)
        descriptions = {
            "milan": "War financing for Florentine operations against Milan",
            "venice": "Loan to Venice for Lombardy Wars operations",
            "defensive": "Emergency war financing for Florence defense",
        }
        return {
            "id": self.transaction_id,
            "date": transaction_date.isoformat(),
            "branch": "Florence",
            "type": "war_financing",
            "counterparty": "Republic of Florence",
            "description": descriptions.get(war_type, "War financing"),
            "debit_account": "Loans Receivable - Government",
            "debit_amount": float(amount),
            "credit_account": "Cash",
            "credit_amount": float(amount),
            "currency": "florin",
        }

    def generate_alum_trade(self, transaction_date: date) -> Dict:
        branch = random.choice(["Rome", "Florence", "Venice"])
        amount = self.random_amount(200, 5000)
        return {
            "id": self.transaction_id,
            "date": transaction_date.isoformat(),
            "branch": branch,
            "type": "alum_trade",
            "counterparty": random.choice(self.merchants),
            "description": "Alum sale from papal mines",
            "debit_account": "Cash",
            "debit_amount": float(amount),
            "credit_account": "Trading Revenue",
            "credit_amount": float(amount),
            "currency": "florin",
        }

    def generate_bills_of_exchange(self, transaction_date: date) -> Dict:
        from_branch = random.choice(self.branches)
        to_branch = random.choice([b for b in self.branches if b != from_branch])
        amount = self.random_amount(500, 20000)
        fee_rate = Decimal(random.randint(100, 300)) / Decimal("10000")
        fee = (amount * fee_rate).quantize(Decimal("0.01"))
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
            "currency": "florin",
        }

    def generate_operating_expense(self, transaction_date: date) -> Dict:
        branch = random.choice(self.branches)
        expense_types = [
            ("Wages", 100, 2000),
            ("Rent", 50, 500),
            ("Supplies", 20, 300),
            ("Courier Services", 10, 100),
            ("Security", 50, 500),
            ("Maintenance", 30, 400),
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
            "currency": "florin",
        }

    def generate_deposit_withdrawal(self, transaction_date: date) -> Dict:
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
                "currency": "florin",
            }
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
            "currency": "florin",
        }

    def generate_transactions(self, num_transactions: int = 60000) -> List[Dict]:
        transactions = []
        start_date = date(1390, 1, 1)
        end_date = date(1440, 12, 31)

        transaction_weights = {
            "papal_deposit": 0.15,
            "loan_issuance": 0.12,
            "loan_repayment": 0.13,
            "deposit_withdrawal": 0.20,
            "bills_of_exchange": 0.10,
            "alum_trade": 0.08,
            "war_financing": 0.05,
            "operating_expense": 0.17,
        }

        while len(transactions) < num_transactions:
            trans_date = self.random_date(start_date, end_date)

            rand = random.random()
            cumulative = 0.0
            trans_type = None
            for t_type, weight in transaction_weights.items():
                cumulative += weight
                if rand <= cumulative:
                    trans_type = t_type
                    break

            # Boost papal during boom
            if (HistoricalPeriod.PAPAL_BANKING_BOOM["start"] <= trans_date
                    <= HistoricalPeriod.PAPAL_BANKING_BOOM["end"]):
                if random.random() < 0.3:
                    trans_type = "papal_deposit"

            # Boost war financing during wars
            war_periods = [
                HistoricalPeriod.FIRST_MILANESE_WAR,
                HistoricalPeriod.SECOND_MILANESE_WAR,
                HistoricalPeriod.LOMBARDY_WARS,
            ]
            in_war = any(p["start"] <= trans_date <= p["end"] for p in war_periods)
            if in_war and random.random() < 0.15:
                trans_type = "war_financing"

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
                print(f"Error generating {trans_type}: {e}")
                continue

        return transactions[:num_transactions]


# ──────────────────────────────────────────────────────────────────────────────
# Embezzlement Transaction Generator
#
# The scheme: Ser Benedetto di Agnolo, senior clerk at the Florence branch,
# creates a fictitious supplier called "Ser Benedetto Forniture" (Benedetto's
# Supplies) and authorises payments for "parchment, ink and scribal materials"
# — legitimate-sounding expenses for a busy banking branch.
#
# Over five years (1420-01-01 to 1424-12-31), 247 transactions drain
# approximately 100,000 florins from the Florence branch Cash account into
# a personal holding managed through a correspondent in Genoa.
#
# Forensic detection hints (detailed in INSTRUCTOR_EMBEZZLEMENT_GUIDE.md):
#   1. Benford's Law: amounts cluster heavily on digits 3, 4, 5 (fail chi-sq)
#   2. Vendor concentration: "Ser Benedetto Forniture" alone > 30% of Florence
#      Supplies expenses in every year of the scheme
#   3. Round-number clustering: ~45% of amounts are exact multiples of 50
#   4. Regularity: payments arrive every 7-8 days (too regular for a real supplier)
#   5. No other branch: this vendor appears ONLY in Florence records
# ──────────────────────────────────────────────────────────────────────────────

EMBEZZLEMENT_COUNTERPARTY = "Ser Benedetto Forniture"
EMBEZZLEMENT_BRANCH = "Florence"
EMBEZZLEMENT_START = date(1420, 1, 3)
EMBEZZLEMENT_END = date(1424, 12, 28)
# Total target: ~100,000 florins across ~247 payments ≈ 405 florins average

# Fixed payment amounts (deliberately round-number heavy — a forensic red flag)
_PAYMENT_POOL = [
    250.00, 300.00, 350.00, 400.00, 450.00, 500.00,
    275.00, 325.00, 375.00, 425.00, 475.00,
    310.00, 340.00, 390.00, 410.00, 460.00,
    380.00, 420.00, 440.00, 360.00, 480.00,
    550.00, 600.00, 520.00, 580.00,
]


def generate_embezzlement_transactions() -> List[Dict]:
    """
    Generate the embezzlement transaction trail.
    Returns a list of dicts in the same schema as normal transactions.
    """
    random.seed(7)  # deterministic for reproducibility
    transactions = []
    current_date = EMBEZZLEMENT_START
    interval_days = 8  # payments every ~8 days — suspiciously regular

    descriptions = [
        "Parchment and scribal supplies from Ser Benedetto Forniture",
        "Ink and writing materials — Florence scriptorium",
        "Scribal materials and ledger parchment, Florence branch",
        "Wax, parchment and binding thread for Florence records",
        "Quills, ink and parchment — quarterly supply, Florence",
        "Writing materials and archival supplies, Florence",
        "Scribal sundries for Florence correspondence office",
    ]

    while current_date <= EMBEZZLEMENT_END:
        amount_float = random.choice(_PAYMENT_POOL)
        # Occasionally add a small random variation to look less mechanical,
        # but still bias heavily toward round numbers
        if random.random() < 0.25:
            # A plausible "odd" amount — still within the round-number pool
            amount_float += random.choice([12.50, 17.50, 22.50, 7.50, 15.00])

        amount = Decimal(str(amount_float)).quantize(Decimal("0.01"))
        desc = random.choice(descriptions)

        transactions.append({
            # id assigned during final renumbering
            "date": current_date.isoformat(),
            "branch": EMBEZZLEMENT_BRANCH,
            "type": "operating_expense",
            "counterparty": EMBEZZLEMENT_COUNTERPARTY,
            "description": desc,
            "debit_account": "Supplies",
            "debit_amount": float(amount),
            "credit_account": "Cash",
            "credit_amount": float(amount),
            "currency": "florin",
        })

        # Advance by 7 or 8 days — just enough variation to not look mechanical
        current_date += timedelta(days=interval_days + random.randint(-1, 1))

    print(f"Generated {len(transactions)} embezzlement transactions")
    total = sum(t["debit_amount"] for t in transactions)
    print(f"Total embezzled: {total:,.2f} florins")
    return transactions


# ──────────────────────────────────────────────────────────────────────────────
# I/O helpers
# ──────────────────────────────────────────────────────────────────────────────

def load_existing_csv(filename: str) -> List[Dict]:
    print(f"Loading existing transactions from {filename} …")
    transactions = []
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for field in ("debit_amount", "credit_amount", "credit_amount_2"):
                if row.get(field):
                    try:
                        row[field] = float(row[field])
                    except ValueError:
                        row[field] = None
            transactions.append(row)
    print(f"Loaded {len(transactions)} existing transactions.")
    return transactions


def save_to_csv(transactions: List[Dict], filename: str):
    if not transactions:
        print("No transactions to save.")
        return
    fieldnames = set()
    for t in transactions:
        fieldnames.update(t.keys())
    fieldnames = sorted(fieldnames)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
    print(f"Saved {len(transactions)} transactions to {filename}")


def save_to_json(transactions: List[Dict], filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2)
    print(f"Saved {len(transactions)} transactions to {filename}")


def print_summary(transactions: List[Dict]):
    print("\n" + "=" * 60)
    print("MEDICI BANK — EXPANDED TRANSACTION SUMMARY")
    print("=" * 60)
    print(f"\nTotal Transactions: {len(transactions)}")

    type_counts: Dict[str, int] = {}
    for t in transactions:
        tt = str(t.get("type", "unknown"))
        type_counts[tt] = type_counts.get(tt, 0) + 1
    print("\nTransactions by Type:")
    for tt, cnt in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        pct = cnt / len(transactions) * 100
        print(f"  {tt:25s}: {cnt:6d} ({pct:5.2f}%)")

    branch_counts: Dict[str, int] = {}
    for t in transactions:
        b = str(t.get("branch", "unknown"))
        branch_counts[b] = branch_counts.get(b, 0) + 1
    print("\nTransactions by Branch:")
    for b, cnt in sorted(branch_counts.items(), key=lambda x: x[1], reverse=True):
        pct = cnt / len(transactions) * 100
        print(f"  {b:15s}: {cnt:6d} ({pct:5.2f}%)")

    dates = [t["date"] for t in transactions]
    print(f"\nDate Range: {min(dates)} to {max(dates)}")

    total_vol = sum(float(t.get("debit_amount") or 0) for t in transactions)
    print(f"Total Transaction Volume: {total_vol:,.2f} florins")
    print("=" * 60)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Medici Bank — Additional Data Generator")
    print("=" * 60)

    # 1. Load existing 20,000 transactions
    existing = load_existing_csv("medici_transactions.csv")

    # 2. Generate 60,000 more legitimate transactions
    print("\nGenerating 60,000 additional legitimate transactions …")
    gen = TransactionGenerator(seed=99)
    additional = gen.generate_transactions(60000)
    print(f"Generated {len(additional)} additional transactions.")

    # 3. Generate embezzlement transactions
    print("\nGenerating embezzlement transaction trail …")
    embezzlement = generate_embezzlement_transactions()

    # 4. Combine, sort, renumber
    print("\nCombining and sorting all transactions …")
    combined = existing + additional + embezzlement
    combined.sort(key=lambda x: (str(x.get("date", "")), int(x.get("id", 0)) if x.get("id") else 0))
    for idx, t in enumerate(combined, 1):
        t["id"] = idx

    # 5. Print summary
    print_summary(combined)

    # 6. Save
    print("\nSaving updated files …")
    save_to_csv(combined, "medici_transactions.csv")
    save_to_json(combined, "medici_transactions.json")

    print("\nDone. Updated files:")
    print("  medici_transactions.csv")
    print("  medici_transactions.json")


if __name__ == "__main__":
    main()
