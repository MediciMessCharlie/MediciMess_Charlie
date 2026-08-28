from datetime import date
from decimal import Decimal
from analytics.kpis import (
    enrich_transaction,
    group_transactions,
    calc_total_cash_inflows,
    calc_total_cash_outflows,
    calc_net_cash_movement,
    calc_closing_cash_bal,
    calc_total_deposits,
    calc_total_withdrawals,
    calc_deposit_count,
    calc_withdrawal_count,
    calc_avg_deposit_size,
    calc_avg_withdrawal_size,
    calc_loans_issued,
    calc_loans_repaid,
    calc_interest_earned,
    calc_loan_portfolio_bal,
    calc_int_yield,
    calc_total_operating_expenses,
    calc_expenses_by_category,
    calc_expense_per_transaction,
    calc_top_payees_by_expense,
    calc_exchange_fee_revenue,
    calc_interest_income,
    calc_trading_revenue,
    calc_total_revenue,
    calc_net_income,
    calc_net_income_margin,
    calculate_kpis,
)

# -------------------------
# Cash KPI Tests
# -------------------------

transactions = [
    {
        "id": 1,
        "date": date(1420, 1, 5),
        "branch": "Florence",
        "type": "deposit",
        "counterparty": "Merchant A",
        "description": "Customer deposit",
        "debit_account": "Cash",
        "debit_amount": Decimal("1000.00"),
        "credit_account": "Deposits Payable",
        "credit_amount": Decimal("1000.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
    {
        "id": 2,
        "date": date(1420, 1, 10),
        "branch": "Florence",
        "type": "loan_issuance",
        "counterparty": "Merchant B",
        "description": "Loan issued",
        "debit_account": "Loans Receivable",
        "debit_amount": Decimal("300.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("300.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
    {
        "id": 3,
        "date": date(1420, 2, 3),
        "branch": "Florence",
        "type": "trading",
        "counterparty": "Merchant C",
        "description": "Trading revenue",
        "debit_account": "Cash",
        "debit_amount": Decimal("500.00"),
        "credit_account": "Trading Revenue",
        "credit_amount": Decimal("500.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
]

enriched = [enrich_transaction(t) for t in transactions]
groups = group_transactions(enriched)

jan_transactions = groups[("Florence", "1420-01")]

assert calc_total_cash_inflows(jan_transactions) == Decimal("1000.00")
assert calc_total_cash_outflows(jan_transactions) == Decimal("300.00")
assert calc_net_cash_movement(jan_transactions) == Decimal("700.00")

florence_periods = {
    period: txns
    for (branch, period), txns in groups.items()
    if branch == "Florence"
}

closing_balances = calc_closing_cash_bal(florence_periods)

assert closing_balances["1420-01"] == Decimal("700.00")
assert closing_balances["1420-02"] == Decimal("1200.00")

print("All cash KPI tests passed!")

# -------------------------
# Deposit / Withdrawal KPI Tests
# -------------------------

deposit_withdrawal_transactions = [
    {
        "id": 10,
        "date": date(1420, 3, 1),
        "branch": "Florence",
        "type": "deposit",
        "counterparty": "Merchant D",
        "description": "Deposit",
        "debit_account": "Cash",
        "debit_amount": Decimal("1000.00"),
        "credit_account": "Deposits Payable",
        "credit_amount": Decimal("1000.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
    {
        "id": 11,
        "date": date(1420, 3, 2),
        "branch": "Florence",
        "type": "deposit",
        "counterparty": "Merchant E",
        "description": "Deposit",
        "debit_account": "Cash",
        "debit_amount": Decimal("500.00"),
        "credit_account": "Deposits Payable",
        "credit_amount": Decimal("500.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
    {
        "id": 12,
        "date": date(1420, 3, 3),
        "branch": "Florence",
        "type": "withdrawal",
        "counterparty": "Merchant F",
        "description": "Withdrawal",
        "debit_account": "Deposits Payable",
        "debit_amount": Decimal("300.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("300.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
    {
        "id": 13,
        "date": date(1420, 3, 4),
        "branch": "Florence",
        "type": "withdrawal",
        "counterparty": "Merchant G",
        "description": "Withdrawal",
        "debit_account": "Deposits Payable",
        "debit_amount": Decimal("200.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("200.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
]

assert calc_total_deposits(deposit_withdrawal_transactions) == Decimal("1500.00")
assert calc_total_withdrawals(deposit_withdrawal_transactions) == Decimal("500.00")
assert calc_deposit_count(deposit_withdrawal_transactions) == 2
assert calc_withdrawal_count(deposit_withdrawal_transactions) == 2
assert calc_avg_deposit_size(deposit_withdrawal_transactions) == Decimal("750.00")
assert calc_avg_withdrawal_size(deposit_withdrawal_transactions) == Decimal("250.00")

no_deposits = [
    {
        "id": 14,
        "date": date(1420, 3, 5),
        "branch": "Florence",
        "type": "withdrawal",
        "counterparty": "Merchant H",
        "description": "Withdrawal",
        "debit_account": "Deposits Payable",
        "debit_amount": Decimal("100.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("100.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    }
]

assert calc_avg_deposit_size(no_deposits) == Decimal("0")

print("All deposit/withdrawal KPI tests passed!")

# -------------------------
# Loan KPI Tests
# -------------------------

loan_transactions = [
    {
        "id": 20,
        "date": date(1420, 1, 15),
        "branch": "Florence",
        "type": "loan_issuance",
        "counterparty": "Wool Merchant",
        "description": "Loan issued",
        "debit_account": "Loans Receivable",
        "debit_amount": Decimal("10000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("10000.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
    {
        "id": 21,
        "date": date(1420, 1, 20),
        "branch": "Florence",
        "type": "loan_repayment",
        "counterparty": "Wool Merchant",
        "description": "Loan repayment with interest",
        "debit_account": "Cash",
        "debit_amount": Decimal("2200.00"),
        "credit_account": "Loans Receivable",
        "credit_amount": Decimal("2000.00"),
        "credit_account_2": "Interest Income",
        "credit_amount_2": Decimal("200.00"),
        "currency": "florin",
    },
    {
        "id": 22,
        "date": date(1420, 2, 10),
        "branch": "Florence",
        "type": "loan_issuance",
        "counterparty": "Silk Merchant",
        "description": "Loan issued",
        "debit_account": "Loans Receivable",
        "debit_amount": Decimal("5000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("5000.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
    {
        "id": 23,
        "date": date(1420, 2, 18),
        "branch": "Florence",
        "type": "loan_repayment",
        "counterparty": "Silk Merchant",
        "description": "Loan repayment with interest",
        "debit_account": "Cash",
        "debit_amount": Decimal("1100.00"),
        "credit_account": "Loans Receivable",
        "credit_amount": Decimal("1000.00"),
        "credit_account_2": "Interest Income",
        "credit_amount_2": Decimal("100.00"),
        "currency": "florin",
    },
]

assert calc_loans_issued(loan_transactions) == Decimal("15000.00")
assert calc_loans_repaid(loan_transactions) == Decimal("3000.00")
assert calc_interest_earned(loan_transactions) == Decimal("300.00")
# assert calc_int_yield(loan_transactions) == Decimal("10.0")
assert calc_int_yield(loan_transactions) == Decimal("10.00")

loan_enriched = [enrich_transaction(t) for t in loan_transactions]
loan_groups = group_transactions(loan_enriched)

florence_loan_periods = {
    period: txns
    for (branch, period), txns in loan_groups.items()
    if branch == "Florence"
}

loan_balances = calc_loan_portfolio_bal(florence_loan_periods)

assert loan_balances["1420-01"] == Decimal("8000.00")
assert loan_balances["1420-02"] == Decimal("12000.00")

print("All loan KPI tests passed!")

# -------------------------
# Operating Expense KPI Tests
# -------------------------

expense_transactions = [
    {
        "id": 30,
        "date": date(1420, 4, 1),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Florence Workers Guild",
        "description": "Wages expense",
        "debit_account": "Wages Expense",
        "debit_amount": Decimal("5000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("5000.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
    {
        "id": 31,
        "date": date(1420, 4, 5),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Medici Properties",
        "description": "Rent expense",
        "debit_account": "Rent Expense",
        "debit_amount": Decimal("2000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("2000.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
    {
        "id": 32,
        "date": date(1420, 4, 10),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Florence Workers Guild",
        "description": "Wages expense",
        "debit_account": "Wages Expense",
        "debit_amount": Decimal("3000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("3000.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
    {
        "id": 33,
        "date": date(1420, 4, 15),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Florence Security Guild",
        "description": "Security expense",
        "debit_account": "Security Expense",
        "debit_amount": Decimal("1000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("1000.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
]

assert calc_total_operating_expenses(expense_transactions) == Decimal("11000.00")

expected_categories = {
    "Wages Expense": Decimal("8000.00"),
    "Rent Expense": Decimal("2000.00"),
    "Security Expense": Decimal("1000.00"),
}

assert calc_expenses_by_category(expense_transactions) == expected_categories
assert calc_expense_per_transaction(expense_transactions) == Decimal("2750.00")

expected_payees = [
    {
        "counterparty": "Florence Workers Guild",
        "amount": Decimal("8000.00"),
    },
    {
        "counterparty": "Medici Properties",
        "amount": Decimal("2000.00"),
    },
    {
        "counterparty": "Florence Security Guild",
        "amount": Decimal("1000.00"),
    },
]

assert calc_top_payees_by_expense(expense_transactions) == expected_payees

print("All operating expense KPI tests passed!")

# -------------------------
# Revenue / Net Income KPI Tests
# -------------------------

revenue_transactions = [
    {
        "id": 40,
        "date": date(1420, 5, 1),
        "branch": "Florence",
        "type": "bill_of_exchange",
        "counterparty": "Venice Merchant",
        "description": "Bill of exchange",
        "debit_account": "Cash",
        "debit_amount": Decimal("1050.00"),
        "credit_account": "Accounts Receivable",
        "credit_amount": Decimal("1000.00"),
        "credit_account_2": "Exchange Fee Revenue",
        "credit_amount_2": Decimal("50.00"),
        "currency": "florin",
    },
    {
        "id": 41,
        "date": date(1420, 5, 5),
        "branch": "Florence",
        "type": "loan_repayment",
        "counterparty": "Wool Merchant",
        "description": "Loan repayment with interest",
        "debit_account": "Cash",
        "debit_amount": Decimal("2200.00"),
        "credit_account": "Loans Receivable",
        "credit_amount": Decimal("2000.00"),
        "credit_account_2": "Interest Income",
        "credit_amount_2": Decimal("200.00"),
        "currency": "florin",
    },
    {
        "id": 42,
        "date": date(1420, 5, 10),
        "branch": "Florence",
        "type": "trading",
        "counterparty": "Silk Merchant",
        "description": "Trading revenue",
        "debit_account": "Cash",
        "debit_amount": Decimal("3000.00"),
        "credit_account": "Trading Revenue",
        "credit_amount": Decimal("3000.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
    {
        "id": 43,
        "date": date(1420, 5, 15),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Florence Workers Guild",
        "description": "Wages expense",
        "debit_account": "Wages Expense",
        "debit_amount": Decimal("1000.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("1000.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    },
]

assert calc_exchange_fee_revenue(revenue_transactions) == Decimal("50.00")
assert calc_interest_income(revenue_transactions) == Decimal("200.00")
assert calc_trading_revenue(revenue_transactions) == Decimal("3000.00")
assert calc_total_revenue(revenue_transactions) == Decimal("3250.00")
assert calc_net_income(revenue_transactions) == Decimal("2250.00")

# expected_margin = (Decimal("2250.00") / Decimal("3250.00")) * Decimal("100")
expected_margin = Decimal("69.23")
assert calc_net_income_margin(revenue_transactions) == expected_margin

no_revenue_transactions = [
    {
        "id": 44,
        "date": date(1420, 5, 20),
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Florence Security Guild",
        "description": "Security expense",
        "debit_account": "Security Expense",
        "debit_amount": Decimal("500.00"),
        "credit_account": "Cash",
        "credit_amount": Decimal("500.00"),
        "credit_account_2": None,
        "credit_amount_2": None,
        "currency": "florin",
    }
]

assert calc_net_income_margin(revenue_transactions) == expected_margin

print("All revenue and net income KPI tests passed!")

# -------------------------
# Full KPI Integration Test
# -------------------------

all_test_transactions = (
    transactions
    + deposit_withdrawal_transactions
    + loan_transactions
    + expense_transactions
    + revenue_transactions
)

kpi_results = calculate_kpis(all_test_transactions)

assert isinstance(kpi_results, list)
assert len(kpi_results) > 0

for record in kpi_results:
    assert "branch" in record
    assert "period" in record
    assert "total_cash_inflows" in record
    assert "total_cash_outflows" in record
    assert "net_cash_movement" in record
    assert "closing_cash_balance" in record
    assert "total_deposits" in record
    assert "total_withdrawals" in record
    assert "deposit_count" in record
    assert "withdrawal_count" in record
    assert "avg_deposit_size" in record
    assert "avg_withdrawal_size" in record
    assert "loans_issued" in record
    assert "loans_repaid" in record
    assert "interest_earned" in record
    assert "loan_portfolio_balance" in record
    assert "interest_yield" in record
    assert "total_operating_expenses" in record
    assert "expenses_by_category" in record
    assert "expense_per_transaction" in record
    assert "top_payees_by_expense" in record
    assert "exchange_fee_revenue" in record
    assert "interest_income" in record
    assert "trading_revenue" in record
    assert "total_revenue" in record
    assert "net_income" in record
    assert "net_income_margin" in record

print("Full KPI integration test passed!")