"""The bookkeeping database: schema, default chart of accounts, create/open,
and the queries behind the dashboard and ledger screens.

No GUI imports.  The application API (``api.py`` / ``webapp.py``) builds on
this module.
"""

import os

import accounting
import db_calls as db
import iceberg_time
import invoice_lifecycle
import reconciliation
from iceberg_utils import format_currency
from repository import (AccountRepository, CustomerRepository, InvoiceRepository, OwnerRepository,
                        PropertyRepository, SkuRepository, VendorRepository)
from session import CONSOLE_LOG_SCHEMA

DEFAULT_ACCOUNTS = [
    (10001, "Fixed Asset Real Estate", "Notes:"),
    (10002, "Fixed Asset Bank Account Checking", "Notes:"),
    (10003, "Misc Property", "Notes:"),
    (10004, "Cash", "Notes:"),
    (10005, "Product Inventory", "Notes:"),
    (10006, "Accounts Receivable", "Notes:"),
    (11001, "Office Supplies and Postage", "Notes:"),
    (11002, "Advertising", "Notes:"),
    (11003, "Commissions and Fees", "Notes:"),
    (11004, "Contract Labor", "Notes:"),
    (11005, "Asset Depreciations", "Notes:"),
    (11006, "Insurance", "Notes:"),
    (11007, "Mortgage Interest", "Notes:"),
    (11008, "Legal and Professional Services", "Notes:"),
    (11009, "Rent or Lease of Personal Property", "Notes:"),
    (11010, "Rent or Lease of Real Property", "Notes:"),
    (11011, "Repairs and Maintenance", "Notes:"),
    (11012, "Supplies Expense - Non-Inventory", "Notes:"),
    (11013, "Taxes and Licenses", "Notes:"),
    (11014, "Business Travel Expenses", "Notes:"),
    (11015, "Business Deductible Meals", "Notes:  SEE IRS INSTRUCTIONS"),
    (11016, "Utilties", "Notes:"),
    (11017, "Other Expenses", "Notes: SEE IRS INSTRUCTIONS"),
    (11018, "Cost of Goods Sold", "Notes:"),
    (12001, "Owner Equity Withdrawals", "Notes:"),
    (12002, "Owner Equity: Unclaimable Expenses", "Notes:"),
    (12003, "Owner Equity: Ask Accountant", "Notes: Accountant or tax professional to review for claimable expenses."),
    (13001, "Liabilities", "Notes:"),
    (13002, "Accounts Payable", "Notes:"),
    (13003, "Sales Tax Payable", "Notes:"),
    (14001, "Owner Equity Deposits", "Notes:"),
    (15001, "Sales", "Notes:"),
    (15002, "Real Estate Equity", "Notes:"),
    (15003, "Other Revenue", "Notes:"),
]

PROPERTY_NAMES = {
    "business_name": "Business Name",
    "address": "Address",
    "owner_name": "Owner or Financial Officer Name",
    "owner_title": "Title or Position",
    "phone": "Phone Number",
    "email": "Email",
    "notes": "Notes",
    "ein": "EIN or SSN",
    "receipts_location": "Receipts Repository Location",
    "ledger_name": "Ledger Name",
    "sales_tax": "Sales Tax",
}


def ledger_schema(ledger_name):
    return f"""CREATE TABLE {ledger_name} (Transaction_ID INTEGER NOT NULL,
        Credit_Acct CHAR(5) NOT NULL, Debit_Acct CHAR(5) NOT NULL, Amount INTEGER NOT NULL,
        Name VARCHAR(9999) NOT NULL, Notes VARCHAR(9999), Created_Time VARCHAR(9999) NOT NULL,
        Edited_Time VARCHAR(9999) NOT NULL, Transaction_Date DATE NOT NULL, Record_Image VARCHAR(9999) NOT NULL,
        Vendor VARCHAR(9999), Customer VARCHAR(9999),
        PRIMARY KEY ("Transaction_ID" AUTOINCREMENT), CONSTRAINT chk CHECK (Amount>0));"""


def ledger_table_name(db_name, year=None):
    stem = db_name[:-4] if db_name.endswith(".icb") else db_name
    year = year or iceberg_time.local_now().year
    return f"tbl_ledger_{stem}_CY{year}"


def create_schema(connection, ledger_name, timestamp=None):
    """Create every table and the default chart of accounts on ``connection``."""
    timestamp = timestamp or iceberg_time.storage_timestamp()
    db.create_tables(connection, CONSOLE_LOG_SCHEMA)
    db.create_tables(connection, ledger_schema(ledger_name))
    accounts = AccountRepository(connection)
    accounts.create_table()
    for account_id, name, notes in DEFAULT_ACCOUNTS:
        accounts.insert(account_id, name, notes, timestamp, timestamp, "", "", "", "")
    OwnerRepository(connection).create_table()
    VendorRepository(connection).create_table()
    CustomerRepository(connection).create_table()
    InvoiceRepository(connection).create_table()
    PropertyRepository(connection).create_table()
    SkuRepository(connection).create_table()
    invoice_lifecycle.ensure_schema(connection)
    reconciliation.ensure_schema(connection, ledger_name)


def write_properties(connection, ledger_name, properties, timestamp=None):
    """Insert the tbl_Properties rows.  ``properties`` uses PROPERTY_NAMES keys."""
    timestamp = timestamp or iceberg_time.storage_timestamp()
    repo = PropertyRepository(connection)
    values = dict(properties)
    values["ledger_name"] = ledger_name
    for key, label in PROPERTY_NAMES.items():
        value = values.get(key, "")
        if key == "sales_tax":
            value = f"{value}"
        repo.insert(label, accounting.sql_text(value), "", timestamp, timestamp)


def read_properties(connection):
    repo = PropertyRepository(connection)
    return {key: (repo.get(label) or "") for key, label in PROPERTY_NAMES.items()}


class BooksError(Exception):
    pass


def create_database(db_name, properties, key_folder, folder="."):
    """Create, populate, encrypt and write a new database.

    Returns ``{"connection", "db_name", "db_path", "key_path", "ledger_name"}``.
    Raises ``BooksError`` if the file exists or the save fails; nothing is
    left on disk on failure.
    """
    db_path = os.path.join(folder, db_name)
    if os.path.exists(db_path):
        raise BooksError(f"A database named {db_name} already exists in the Iceberg folder.")
    ledger_name = ledger_table_name(db_name)
    connection = db.create_connection(":memory:")
    create_schema(connection, ledger_name)
    write_properties(connection, ledger_name, properties)
    key, key_filename = db.generate_filekey(db_name, key_folder)
    key_path = os.path.join(key_folder, key_filename)
    result = db.save_encrypted_database(connection, db_path, key_path, backup=False)
    if not result.ok:
        connection.close()
        for path in (db_path, key_path):
            if os.path.exists(path):
                os.remove(path)
        raise BooksError(result.message)
    return {"connection": connection, "db_name": db_name, "db_path": os.path.abspath(db_path),
            "key_path": os.path.abspath(key_path), "ledger_name": ledger_name}


def open_database(key_path, folder="."):
    """Open the .icb that belongs to ``key_path``; upgrades optional tables."""
    key_path = os.path.abspath(key_path)
    key_name = os.path.basename(key_path)
    if not key_name.lower().endswith(".icbkey"):
        raise BooksError("Select a filekey (.icbkey) to open a database.")
    db_name = key_name[:-3]
    db_path = os.path.join(folder, db_name)
    try:
        connection, _ = db.open_encrypted_database(db_path, key_path)
    except db.DatabaseError as error:
        raise BooksError(str(error))
    ledger_name = PropertyRepository(connection).get(PROPERTY_NAMES["ledger_name"]) or ""
    if not ledger_name:
        raise BooksError("This database has no ledger name property; it may be damaged.")
    invoice_lifecycle.ensure_schema(connection)
    reconciliation.ensure_schema(connection, ledger_name)
    db.create_tables(connection, CONSOLE_LOG_SCHEMA)
    return {"connection": connection, "db_name": db_name, "db_path": os.path.abspath(db_path),
            "key_path": key_path, "ledger_name": ledger_name}


# ----------------------------------------------------------------- queries


def dashboard_summary(rows, accounts):
    """The headline figures shown on the dashboard (cents)."""
    by_type = {d: 0 for d in "012345"}
    debits = credits = 0
    ids = [str(a["Account_ID"]) for a in accounts]
    totals = accounting.balances(rows, ids)
    for account_id, value in totals.items():
        by_type[accounting.type_digit(account_id)] += value
    for row in rows:
        debits += int(row["Amount"])
        credits += int(row["Amount"])
    assets, expenses, withdrawals = by_type["0"], by_type["1"], by_type["2"]
    liabilities, owner_equity, revenue = by_type["3"], by_type["4"], by_type["5"]
    return {
        "total_debits": debits,
        "total_credits": credits,
        "in_balance": debits == credits,
        "assets": assets,
        "expenses": expenses,
        "withdrawals": withdrawals,
        "liabilities": liabilities,
        "owner_equity": owner_equity,
        "revenue": revenue,
        "net_assets": assets - liabilities,
        "total_equity": owner_equity + revenue - expenses - withdrawals,
        "retained_earnings": revenue - expenses - withdrawals,
        "business_income": revenue - expenses,
        "transaction_count": len(rows),
    }


def ledger_years(rows):
    years = sorted({str(r["Transaction_Date"])[:4] for r in rows}, reverse=True)
    return years


def chart_of_accounts(rows, accounts, type_prefix=None, year=None):
    """Rows for the chart of accounts table.

    Permanent accounts (assets, liabilities, owner equity) accumulate all
    history through the selected year; temporary accounts (expenses,
    withdrawals, revenue) show the selected year only - matching the
    classic dashboard.
    """
    out = []
    for account in sorted(accounts, key=lambda a: str(a["Account_ID"])):
        key = str(account["Account_ID"])
        if type_prefix and not key.startswith(str(type_prefix)):
            continue
        debits = credits = 0
        for row in rows:
            row_year = str(row["Transaction_Date"])[:4]
            if year:
                if accounting.is_temporary(key) and row_year != str(year):
                    continue
                if not accounting.is_temporary(key) and row_year > str(year):
                    continue
            if str(row["Debit_Acct"]) == key:
                debits += int(row["Amount"])
            if str(row["Credit_Acct"]) == key:
                credits += int(row["Amount"])
        balance = (debits - credits) if accounting.is_debit_normal(key) else (credits - debits)
        out.append({
            "id": key,
            "name": account["Name"],
            "type": accounting.type_name(key),
            "credits": credits,
            "debits": debits,
            "balance": balance,
            "institution": account.get("Institution") or "",
        })
    return out


def search_ledger(rows, search="", year=None, names=None):
    """Filter ledger rows by a free-text search and year; newest first."""
    names = names or {}
    term = (search or "").strip().casefold()
    out = []
    for row in rows:
        if year and str(row["Transaction_Date"])[:4] != str(year):
            continue
        haystack = " ".join(str(row.get(k) or "") for k in ("Transaction_ID", "Name", "Notes", "Debit_Acct", "Credit_Acct", "Vendor", "Customer", "Transaction_Date"))
        haystack += " " + names.get(str(row["Debit_Acct"]), "") + " " + names.get(str(row["Credit_Acct"]), "")
        haystack += " " + format_currency(int(row["Amount"]))
        if term and term not in haystack.casefold():
            continue
        out.append(row)
    out.sort(key=lambda r: (str(r["Transaction_Date"]), int(r["Transaction_ID"])), reverse=True)
    return out


def add_transaction(connection, ledger_name, cleaned, record_image="", customer=""):
    """Insert a validated transaction (``validation.validate_transaction`` output)."""
    stamp = iceberg_time.storage_timestamp()
    transaction_id = accounting.next_transaction_id(connection, ledger_name)
    connection.execute(
        f"""INSERT INTO {ledger_name} (Transaction_ID, Credit_Acct, Debit_Acct, Amount, Name, Notes, Created_Time, Edited_Time,
            Transaction_Date, Record_Image, Vendor, Customer) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
        (transaction_id, cleaned["credit_account"], cleaned["debit_account"], cleaned["amount"], cleaned["name"],
         cleaned.get("notes", ""), stamp, stamp, cleaned["date"], record_image, cleaned.get("vendor", ""), customer),
    )
    connection.commit()
    return transaction_id


def update_transaction(connection, ledger_name, transaction_id, cleaned):
    stamp = iceberg_time.storage_timestamp()
    connection.execute(
        f"""UPDATE {ledger_name} SET Credit_Acct = ?, Debit_Acct = ?, Amount = ?, Name = ?, Notes = ?, Edited_Time = ?,
            Transaction_Date = ?, Vendor = ? WHERE Transaction_ID = ?;""",
        (cleaned["credit_account"], cleaned["debit_account"], cleaned["amount"], cleaned["name"], cleaned.get("notes", ""),
         stamp, cleaned["date"], cleaned.get("vendor", ""), int(transaction_id)),
    )
    connection.commit()
    return int(transaction_id)


def get_transaction(connection, ledger_name, transaction_id):
    rows = db.execute_read_query_dict(connection, f"SELECT * FROM {ledger_name} WHERE Transaction_ID = {int(transaction_id)};")
    return rows[0] if isinstance(rows, list) and rows else None
