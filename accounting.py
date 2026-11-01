"""Core double-entry helpers shared by reports, reconciliation, and exports.

Account numbers are five digits.  The second digit is the type:

    0 Assets            debit-normal   permanent
    1 Expenses          debit-normal   temporary (income statement)
    2 Equity withdrawals debit-normal  temporary
    3 Liabilities       credit-normal  permanent
    4 Owner equity      credit-normal  permanent
    5 Revenue           credit-normal  temporary (income statement)

All amounts are integers in cents.
"""

import db_calls as db

TYPE_NAMES = {
    "0": "Assets",
    "1": "Expenses",
    "2": "Equity Withdrawals",
    "3": "Liabilities",
    "4": "Owner Equity",
    "5": "Revenue",
}
DEBIT_NORMAL = {"0", "1", "2"}
TEMPORARY = {"1", "2", "5"}

ACCOUNTS_RECEIVABLE = "10006"
SALES_TAX_PAYABLE = "13003"
SALES = "15001"


def type_digit(account_id):
    return str(account_id)[1]


def type_name(account_id):
    return TYPE_NAMES.get(type_digit(account_id), "Unknown")


def is_debit_normal(account_id):
    return type_digit(account_id) in DEBIT_NORMAL


def is_temporary(account_id):
    return type_digit(account_id) in TEMPORARY


def signed_effect(account_id, transaction):
    """Change to ``account_id``'s normal balance caused by ``transaction``.

    Positive means the balance grew (e.g. a debit to an asset or a credit to
    revenue); zero if the account is not part of the transaction.
    """
    account_id = str(account_id)
    amount = int(transaction["Amount"])
    debit = str(transaction["Debit_Acct"])
    credit = str(transaction["Credit_Acct"])
    effect = 0
    if debit == account_id:
        effect += amount
    if credit == account_id:
        effect -= amount
    if not is_debit_normal(account_id):
        effect = -effect
    return effect


def read_ledger(connection, ledger_name, start=None, end=None):
    """Return ledger rows (dicts) ordered by date then id, optionally bounded.

    ``start``/``end`` are inclusive ``YYYY-MM-DD`` strings.
    """
    clauses = []
    if start:
        clauses.append(f"Transaction_Date >= '{start}'")
    if end:
        clauses.append(f"Transaction_Date <= '{end}'")
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM {ledger_name}{where} ORDER BY Transaction_Date, Transaction_ID;"
    rows = db.execute_read_query_dict(connection, query)
    if not isinstance(rows, list):
        return []
    return rows


def ledger_columns(connection, ledger_name):
    rows = db.execute_read_query_dict(connection, f"PRAGMA table_info({ledger_name});")
    if not isinstance(rows, list):
        return []
    return [row["name"] for row in rows]


def account_name_map(accounts):
    return {str(a["Account_ID"]): a["Name"] for a in accounts}


def balances(rows, account_ids):
    """Return ``{account_id: balance}`` over ``rows`` for the given accounts."""
    totals = {str(a): 0 for a in account_ids}
    for row in rows:
        for key in (str(row["Debit_Acct"]), str(row["Credit_Acct"])):
            if key in totals:
                totals[key] += signed_effect(key, row)
    return totals


def next_transaction_id(connection, ledger_name):
    result = db.execute_read_query_dict(connection, f"SELECT MAX(Transaction_ID) AS Last_ID FROM {ledger_name};")
    if isinstance(result, list) and result and result[0]["Last_ID"] is not None:
        return int(result[0]["Last_ID"]) + 1
    return 1


def sql_text(value):
    """Escape a value for inclusion inside single quotes in SQL."""
    return str("" if value is None else value).replace("'", "''")
