from copy import deepcopy
from decimal import Decimal
from analytics.account_types import infer_account_type

def enrich_transaction(transaction):
    enriched = deepcopy(transaction)
    # return branch in the same format
    branch = enriched.get("branch", "")
    enriched["branch"] = str(branch).strip().title()
    # return day in yyyy-mm
    txn_date = enriched["date"]
    enriched["year"] = txn_date.year
    enriched["month"] = txn_date.month
    # return quarter as Q#
    quarter = (txn_date.month - 1) // 3 + 1
    enriched["quarter"] = f"Q{quarter}"
    # return fiscal year yyyy
    enriched["fiscal_year"] = txn_date.year

    enriched["period"] = f"{txn_date.year}-{txn_date.month:02d}"

    return enriched

def group_transactions(transactions):
    groups = {}

    for transaction in transactions:
        key = (transaction["branch"], transaction["period"])
        groups.setdefault(key, [])
        groups[key].append(transaction)

    return groups

#===============================
# CASH POSITION METRICS
#===============================
def calc_total_cash_inflows(transactions):
    total = Decimal("0")
    for transaction in transactions:
        if transaction["debit_account"] == "Cash":
           total += transaction["debit_amount"]

    return total

def calc_total_cash_outflows(transactions):
    total_out = Decimal("0")
    for transaction in transactions:
        if transaction["credit_account"] == "Cash":
            total_out += transaction["credit_amount"]

    return total_out

def calc_net_cash_movement(transactions):
    # Net cash movement = total cash inflows - total cash outflows
    total_inflows = calc_total_cash_inflows(transactions)
    total_outflows = calc_total_cash_outflows(transactions)

    total_move = total_inflows - total_outflows
    return total_move

def calc_closing_cash_bal(period_groups):
    running_balance = Decimal("0")
    closing_balances = {}
    for period in sorted(period_groups):
        net_movement = calc_net_cash_movement(period_groups[period])
        running_balance += net_movement
        closing_balances[period] = running_balance

    return closing_balances

#===============================
# DEP & W/D METRICS
#===============================

def calc_total_deposits(transactions):
    total = Decimal("0")
    for transaction in transactions:
        if transaction["type"] == "deposit":
            total += transaction["debit_amount"]
    
    return total

def calc_total_withdrawals(transactions):
    total = Decimal("0")
    for transaction in transactions:
        if transaction["type"] == "withdrawal":
            total += transaction["debit_amount"]

    return total

def calc_deposit_count(transactions):
    count = 0
    for transaction in transactions:
        if transaction["type"] == "deposit":
            count += 1
    return count

def calc_withdrawal_count(transactions):
    count = 0
    for transaction in transactions:
        if transaction["type"] == "withdrawal":
            count += 1

    return count

def calc_avg_deposit_size(transactions):
    total_deposits = calc_total_deposits(transactions)
    deposit_count = calc_deposit_count(transactions)

    if deposit_count == 0:
        return Decimal("0")
   
    avg_deposit_size = total_deposits / deposit_count
    return avg_deposit_size.quantize(Decimal("0.01"))

def calc_avg_withdrawal_size(transactions):
    total_withdrawals = calc_total_withdrawals(transactions)
    withdrawal_count  = calc_withdrawal_count(transactions)

    if withdrawal_count == 0:
        return Decimal("0")

    avg_withdrawal_size = total_withdrawals / withdrawal_count
    # return avg_withdrawal_size
    return avg_withdrawal_size.quantize(Decimal("0.01"))

#===============================
# LOAN PORTFOLIO METRICS
#===============================

def calc_loans_issued(transactions):
    total = Decimal("0")
    for transaction in transactions:
        if transaction["type"] == "loan_issuance":
            total += transaction["debit_amount"]

    return total

def calc_loans_repaid(transactions):
    total = Decimal("0")
    for transaction in transactions:
        if transaction["type"] == "loan_repayment":
            total += transaction["credit_amount"]

    return total

def calc_interest_earned(transactions):
    total = Decimal("0")
    for transaction in transactions:
        if transaction["type"] == "loan_repayment":
            total += transaction.get("credit_amount_2") or Decimal("0")

    return total

def calc_loan_portfolio_bal(period_groups):
    running_balance = Decimal("0")
    portfolio_balances = {}

    for period in sorted(period_groups):
        transactions = period_groups[period]

        loans_issued = calc_loans_issued(transactions)
        loans_repaid = calc_loans_repaid(transactions)

        net_loan_movement = loans_issued - loans_repaid
        running_balance += net_loan_movement

        portfolio_balances[period] = running_balance

    return portfolio_balances

def calc_int_yield(transactions):
    interest_earned = calc_interest_earned(transactions)
    loans_repaid = calc_loans_repaid(transactions)

    if loans_repaid == 0:
        return Decimal("0.00")

    interest_yield = (
        (interest_earned / loans_repaid) * Decimal("100")
    )

    return interest_yield.quantize(Decimal("0.01"))

def calculate_loan_details(transactions):
    """Return observable monthly loan activity by branch and counterparty.

    The source data has no loan IDs, so these records intentionally report
    activity rather than claiming to identify open loans or matched balances.
    """
    grouped = {}

    for transaction in transactions:
        if transaction["type"] not in {"loan_issuance", "loan_repayment"}:
            continue

        enriched = enrich_transaction(transaction)
        key = (
            enriched["branch"],
            enriched["period"],
            enriched["counterparty"],
        )
        detail = grouped.setdefault(
            key,
            {
                "branch": key[0],
                "period": key[1],
                "counterparty": key[2],
                "loans_issued": Decimal("0"),
                "loans_repaid": Decimal("0"),
                "interest_earned": Decimal("0"),
                "net_loan_movement": Decimal("0"),
            },
        )

        if enriched["type"] == "loan_issuance":
            detail["loans_issued"] += enriched["debit_amount"]
        else:
            detail["loans_repaid"] += enriched["credit_amount"]
            detail["interest_earned"] += (
                enriched.get("credit_amount_2") or Decimal("0")
            )

        detail["net_loan_movement"] = (
            detail["loans_issued"] - detail["loans_repaid"]
        )

    return [grouped[key] for key in sorted(grouped)]

#===============================
# OPERATING EXPENSE METRICS
#===============================
def calc_total_operating_expenses(transactions):
    total = Decimal("0")
    for transaction in transactions:
        if transaction["type"] == "operating_expense":
            total += transaction["debit_amount"]

    return total

def calc_expenses_by_category(transactions):
    categories = {}

    for transaction in transactions:
        if transaction["type"] == "operating_expense":
            category = transaction["debit_account"]
            amount = transaction["debit_amount"]

            categories.setdefault(category, Decimal("0"))
            categories[category] += amount

    return categories

def calc_expense_per_transaction(transactions):
    operating_exp = calc_total_operating_expenses(transactions)
    trans_ct = 0
    for transaction in transactions:
        if transaction["type"] == "operating_expense":
            trans_ct += 1

    if trans_ct == 0:
        return Decimal("0")

    exp_per_trans = operating_exp / trans_ct
    # return exp_per_trans
    return exp_per_trans.quantize(Decimal("0.01"))

def calc_top_payees_by_expense(transactions):
    payees = {}
    for transaction in transactions:
        if transaction["type"] == "operating_expense":
            counterparty = transaction["counterparty"]
            amount = transaction["debit_amount"]
            payees.setdefault(counterparty, Decimal("0"))
            payees[counterparty] += amount

    sorted_payees = sorted(payees.items(), key=lambda item: item[1],
        reverse=True
    )
    top_payees = []

    for counterparty, amount in sorted_payees:
        top_payees.append({
            "counterparty": counterparty,
            "amount": amount
        })

    return top_payees

def calculate_expense_details(transactions):
    """Return monthly expenses by branch, category, and counterparty."""
    grouped = {}

    for transaction in transactions:
        if transaction["type"] != "operating_expense":
            continue

        enriched = enrich_transaction(transaction)
        key = (
            enriched["branch"],
            enriched["period"],
            enriched["debit_account"],
            enriched["counterparty"],
        )
        detail = grouped.setdefault(
            key,
            {
                "branch": key[0],
                "period": key[1],
                "category": key[2],
                "counterparty": key[3],
                "transaction_count": 0,
                "amount": Decimal("0"),
            },
        )
        detail["transaction_count"] += 1
        detail["amount"] += enriched["debit_amount"]

    return [grouped[key] for key in sorted(grouped)]

#===============================
# REVENUE METRICS
#===============================

def calc_exchange_fee_revenue(transactions):
    total = Decimal("0")

    for transaction in transactions:
        if transaction["type"] == "bill_of_exchange":
            total += transaction.get("credit_amount_2") or Decimal("0")

    return total

def calc_interest_income(transactions):
    total = Decimal("0")

    for transaction in transactions:
        if transaction.get("credit_account_2") == "Interest Income":
            total += transaction.get("credit_amount_2") or Decimal("0")

    return total

def calc_trading_revenue(transactions):
    total = Decimal("0")

    for transaction in transactions:
        if transaction.get("credit_account") == "Trading Revenue":
            total += transaction.get("credit_amount") or Decimal("0")

    return total

def calc_total_revenue(transactions):
    total = Decimal("0")

    for transaction in transactions:
        credit_account = transaction.get("credit_account")
        credit_account_2 = transaction.get("credit_account_2")

        if infer_account_type(credit_account) == "REVENUE":
            total += transaction.get("credit_amount") or Decimal("0")

        if credit_account_2 and infer_account_type(credit_account_2) == "REVENUE":
            total += transaction.get("credit_amount_2") or Decimal("0")

    return total

#===============================
# NET INCOME
#===============================
def calc_net_income(transactions):
    total_revenue = calc_total_revenue(transactions)
    total_expenses = calc_total_operating_expenses(transactions)

    net_income = total_revenue - total_expenses

    return net_income

def calc_net_income_margin(transactions):
    total_revenue = calc_total_revenue(transactions)
    net_income = calc_net_income(transactions)

    if total_revenue == 0:
        return Decimal("0.00")

    net_income_margin = (
        (net_income / total_revenue) * Decimal("100")
    )

    return net_income_margin.quantize(Decimal("0.01"))

def calculate_kpis(transactions):
    enriched_transactions = []

    for transaction in transactions:
        enriched = enrich_transaction(transaction)
        enriched_transactions.append(enriched)

    groups = group_transactions(enriched_transactions)
    results = []

    cash_balances_by_branch = {}
    loan_balances_by_branch = {}
    branch_periods = {}

    for (branch, period), txns in groups.items():
        branch_periods.setdefault(branch, {})
        branch_periods[branch][period] = txns

    for branch, periods in branch_periods.items():
        cash_balances_by_branch[branch] = calc_closing_cash_bal(periods)
        loan_balances_by_branch[branch] = calc_loan_portfolio_bal(periods)

    for (branch, period), txns in groups.items():
        kpi_record = {
            "branch": branch,
            "period": period,

            "total_cash_inflows": calc_total_cash_inflows(txns),
            "total_cash_outflows": calc_total_cash_outflows(txns),
            "net_cash_movement": calc_net_cash_movement(txns),
            "closing_cash_balance": cash_balances_by_branch[branch][period],

            "total_deposits": calc_total_deposits(txns),
            "total_withdrawals": calc_total_withdrawals(txns),
            "deposit_count": calc_deposit_count(txns),
            "withdrawal_count": calc_withdrawal_count(txns),
            "avg_deposit_size": calc_avg_deposit_size(txns),
            "avg_withdrawal_size": calc_avg_withdrawal_size(txns),

            "loans_issued": calc_loans_issued(txns),
            "loans_repaid": calc_loans_repaid(txns),
            "interest_earned": calc_interest_earned(txns),
            "loan_portfolio_balance": loan_balances_by_branch[branch][period],
            "interest_yield": calc_int_yield(txns),

            "total_operating_expenses": calc_total_operating_expenses(txns),
            "expenses_by_category": calc_expenses_by_category(txns),
            "expense_per_transaction": calc_expense_per_transaction(txns),
            "top_payees_by_expense": calc_top_payees_by_expense(txns),

            "exchange_fee_revenue": calc_exchange_fee_revenue(txns),
            "interest_income": calc_interest_income(txns),
            "trading_revenue": calc_trading_revenue(txns),
            "total_revenue": calc_total_revenue(txns),

            "net_income": calc_net_income(txns),
            "net_income_margin": calc_net_income_margin(txns),
        }

        results.append(kpi_record)

    return results
