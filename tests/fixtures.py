"""Shared in-memory database fixture for the accounting feature tests."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db_calls
from repository import AccountRepository, InvoiceRepository, CustomerRepository

LEDGER = "tbl_ledger_Test_CY2025"

LEDGER_SCHEMA = f"""CREATE TABLE {LEDGER} (Transaction_ID INTEGER NOT NULL,
    Credit_Acct CHAR(5) NOT NULL, Debit_Acct CHAR(5) NOT NULL, Amount INTEGER NOT NULL,
    Name VARCHAR(9999) NOT NULL, Notes VARCHAR(9999), Created_Time VARCHAR(9999) NOT NULL,
    Edited_Time VARCHAR(9999) NOT NULL, Transaction_Date DATE NOT NULL, Record_Image VARCHAR(9999) NOT NULL,
    Vendor VARCHAR(9999), Customer VARCHAR(9999),
    PRIMARY KEY ("Transaction_ID" AUTOINCREMENT), CONSTRAINT chk CHECK (Amount>0));"""

ACCOUNTS = [
    (10002, "Checking", "First Bank"),
    (10004, "Cash", ""),
    (10006, "Accounts Receivable", ""),
    (10001, "Fixed Asset Real Estate", ""),
    (11001, "Office Supplies and Postage", ""),
    (11010, "Rent or Lease of Real Property", ""),
    (12001, "Owner Equity Withdrawals", ""),
    (13002, "Accounts Payable", ""),
    (13003, "Sales Tax Payable", ""),
    (14001, "Owner Equity Deposits", ""),
    (15001, "Sales", ""),
]


def make_database():
    conn = db_calls.create_connection(":memory:")
    db_calls.create_tables(conn, LEDGER_SCHEMA)
    repo = AccountRepository(conn)
    repo.create_table()
    for account_id, name, institution in ACCOUNTS:
        repo.insert(account_id, name, "", "2025-01-01T00:00:00+00:00", "2025-01-01T00:00:00+00:00", institution, "", "", "")
    InvoiceRepository(conn).create_table()
    CustomerRepository(conn).create_table()
    return conn


def add_transaction(conn, date, name, amount, debit, credit, notes="", transaction_id=None):
    columns = "Credit_Acct, Debit_Acct, Amount, Name, Notes, Created_Time, Edited_Time, Transaction_Date, Record_Image, Vendor, Customer"
    values = f"'{credit}', '{debit}', {amount}, '{name}', '{notes}', '2025-01-01T00:00:00+00:00', '2025-01-01T00:00:00+00:00', '{date}', '', '', ''"
    if transaction_id is not None:
        columns = "Transaction_ID, " + columns
        values = f"{transaction_id}, " + values
    result = db_calls.execute_query(conn, f"INSERT INTO {LEDGER} ({columns}) VALUES ({values});")
    assert result == "Query executed successfully", result
    return conn.execute("SELECT MAX(Transaction_ID) FROM " + LEDGER).fetchone()[0]


def seed_sample_books(conn):
    """A small but complete year of activity (amounts in cents)."""
    add_transaction(conn, "2025-01-02", "Owner investment", 1000000, "10002", "14001")      # +10,000 checking
    add_transaction(conn, "2025-01-05", "Office rent January", 120000, "11010", "10002")    # -1,200
    add_transaction(conn, "2025-01-10", "Printer paper", 4218, "11001", "10002")            # -42.18
    add_transaction(conn, "2025-02-01", "Office rent February", 120000, "11010", "10002")   # -1,200
    add_transaction(conn, "2025-02-14", "Consulting fee", 250000, "10002", "15001")         # +2,500 revenue
    add_transaction(conn, "2025-03-01", "Office rent March", 120000, "11010", "10002")      # -1,200
    add_transaction(conn, "2025-03-15", "Cash sale", 30000, "10004", "15001")               # +300 cash revenue
    add_transaction(conn, "2025-03-20", "Owner draw", 50000, "12001", "10002")              # -500
    add_transaction(conn, "2025-03-25", "Bought land", 500000, "10001", "10002")            # -5,000 investing
    add_transaction(conn, "2025-03-28", "Supplier on credit", 20000, "11001", "13002")      # payable, no cash
    add_transaction(conn, "2025-04-02", "Move cash to bank", 10000, "10002", "10004")       # transfer
    return conn
