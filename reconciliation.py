"""Account reconciliation against a bank or card statement (ST-006).

Workflow:

1. ``ensure_schema`` adds a ``Reconciled_Date`` column to the ledger (once)
   and a ``tbl_Reconciliations`` table that records each completed statement.
2. ``start`` collects every transaction touching the account dated on or
   before the statement date that has not been reconciled yet (the
   "unmatched" candidates) and the balance already reconciled by earlier
   statements.
3. ``summarize`` computes, for a chosen set of cleared transaction IDs, the
   cleared balance, the difference from the statement's ending balance, and
   the still-unmatched transactions.
4. ``complete`` stores the reconciliation when the difference is zero and
   marks the cleared transactions with the statement date.

All amounts are integers in cents.  Signs follow the account's normal
balance, so a deposit to a checking account and a charge to a credit card
both appear positive.
"""

import accounting
import db_calls as db
import iceberg_time

RECONCILED_COLUMN = "Reconciled_Date"

RECONCILIATIONS_SCHEMA = """CREATE TABLE IF NOT EXISTS tbl_Reconciliations (
    Reconciliation_ID INTEGER NOT NULL,
    Account_ID CHAR(5) NOT NULL,
    Statement_Date DATE NOT NULL,
    Statement_Balance INTEGER NOT NULL,
    Cleared_Balance INTEGER NOT NULL,
    Cleared_Count INTEGER NOT NULL,
    Transaction_IDs VARCHAR(9999) NOT NULL,
    Created_Time VARCHAR(9999) NOT NULL,
    PRIMARY KEY ("Reconciliation_ID" AUTOINCREMENT)
);"""


class ReconciliationError(Exception):
    pass


def _rows(connection, query, params=()):
    """Run a parameterised query and return the rows as plain dicts."""
    cursor = connection.execute(query, params)
    columns = [c[0] for c in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _one(connection, query, params=()):
    rows = _rows(connection, query, params)
    return rows[0] if rows else None


def ensure_schema(connection, ledger_name):
    """Idempotent migration: reconciled flag on the ledger, history table.

    ``ledger_name`` and ``RECONCILED_COLUMN`` are identifiers, not values, so
    they cannot be bound as ``?`` parameters; both are internally derived
    (``books.ledger_table_name`` sanitises the ledger name) rather than raw
    user text, so building them into the DDL string here is safe.
    """
    if RECONCILED_COLUMN not in accounting.ledger_columns(connection, ledger_name):
        db.execute_query(connection, f"ALTER TABLE {ledger_name} ADD COLUMN {RECONCILED_COLUMN} DATE;")
    db.create_tables(connection, RECONCILIATIONS_SCHEMA)


def _row_view(account_id, row):
    return {
        "Transaction_ID": int(row["Transaction_ID"]),
        "Transaction_Date": str(row["Transaction_Date"])[:10],
        "Name": row["Name"],
        "Amount": accounting.signed_effect(account_id, row),
        "Counter_Account": str(row["Credit_Acct"]) if str(row["Debit_Acct"]) == str(account_id) else str(row["Debit_Acct"]),
        "Reconciled_Date": row.get(RECONCILED_COLUMN),
    }


def start(connection, ledger_name, account_id, statement_date):
    """Return the data needed to reconcile ``account_id`` through ``statement_date``.

    Result keys: ``candidates`` (unreconciled transactions, oldest first),
    ``reconciled_balance`` (sum of already-reconciled transactions through
    the date), ``reconciled_count``, ``later_reconciled`` (transactions dated
    after the statement that were reconciled on an earlier statement - a sign
    of a wrong date).
    """
    ensure_schema(connection, ledger_name)
    account_id = str(account_id)
    rows = _rows(
        connection,
        f"SELECT * FROM {ledger_name} WHERE Debit_Acct = ? OR Credit_Acct = ? ORDER BY Transaction_Date, Transaction_ID;",
        (account_id, account_id),
    )
    if not isinstance(rows, list):
        rows = []
    candidates, reconciled_balance, reconciled_count, later = [], 0, 0, []
    for row in rows:
        view = _row_view(account_id, row)
        if view["Reconciled_Date"]:
            if view["Transaction_Date"] <= statement_date:
                reconciled_balance += view["Amount"]
                reconciled_count += 1
            else:
                later.append(view)
        elif view["Transaction_Date"] <= statement_date:
            candidates.append(view)
    return {
        "account_id": account_id,
        "statement_date": statement_date,
        "candidates": candidates,
        "reconciled_balance": reconciled_balance,
        "reconciled_count": reconciled_count,
        "later_reconciled": later,
    }


def summarize(session, cleared_ids, statement_balance):
    """Compute the running reconciliation figures for the chosen cleared IDs."""
    cleared_ids = {int(i) for i in cleared_ids}
    cleared, unmatched = [], []
    for view in session["candidates"]:
        (cleared if view["Transaction_ID"] in cleared_ids else unmatched).append(view)
    cleared_total = sum(v["Amount"] for v in cleared)
    cleared_balance = session["reconciled_balance"] + cleared_total
    return {
        "statement_balance": int(statement_balance),
        "reconciled_balance": session["reconciled_balance"],
        "cleared_total": cleared_total,
        "cleared_count": len(cleared),
        "cleared_balance": cleared_balance,
        "difference": int(statement_balance) - cleared_balance,
        "cleared": cleared,
        "unmatched": unmatched,
        "unmatched_total": sum(v["Amount"] for v in unmatched),
        "balanced": int(statement_balance) == cleared_balance,
    }


def complete(connection, ledger_name, session, cleared_ids, statement_balance):
    """Persist a balanced reconciliation.  Raises ReconciliationError otherwise."""
    summary = summarize(session, cleared_ids, statement_balance)
    if not summary["balanced"]:
        raise ReconciliationError(
            f"The statement balance differs from the cleared balance by "
            f"{summary['difference'] / 100:,.2f}. Clear the matching transactions, or record the missing "
            "transaction (bank fee, interest, deposit) and try again."
        )
    if summary["cleared_count"] == 0 and session["reconciled_count"] == 0 and int(statement_balance) != 0:
        raise ReconciliationError("No transactions were cleared.")
    ids = sorted(int(i) for i in cleared_ids)
    if ids:
        placeholders = ",".join("?" * len(ids))
        connection.execute(
            f"UPDATE {ledger_name} SET {RECONCILED_COLUMN} = ? WHERE Transaction_ID IN ({placeholders});",
            (session["statement_date"], *ids),
        )
    connection.execute(
        """INSERT INTO tbl_Reconciliations (Account_ID, Statement_Date, Statement_Balance, Cleared_Balance, Cleared_Count, Transaction_IDs, Created_Time)
        VALUES (?, ?, ?, ?, ?, ?, ?);""",
        (
            session["account_id"],
            session["statement_date"],
            int(statement_balance),
            summary["cleared_balance"],
            len(ids),
            ",".join(str(i) for i in ids),
            iceberg_time.storage_timestamp(),
        ),
    )
    connection.commit()
    return summary


def history(connection, account_id=None):
    """Completed reconciliations, newest first."""
    db.create_tables(connection, RECONCILIATIONS_SCHEMA)
    if account_id:
        return _rows(
            connection,
            "SELECT * FROM tbl_Reconciliations WHERE Account_ID = ? ORDER BY Statement_Date DESC, Reconciliation_ID DESC;",
            (str(account_id),),
        )
    return _rows(connection, "SELECT * FROM tbl_Reconciliations ORDER BY Statement_Date DESC, Reconciliation_ID DESC;")


def undo_last(connection, ledger_name, account_id):
    """Remove the most recent reconciliation for an account and unflag its transactions."""
    ensure_schema(connection, ledger_name)
    last = history(connection, account_id)
    if not last:
        raise ReconciliationError("There is no reconciliation to undo for this account.")
    record = last[0]
    if record["Transaction_IDs"]:
        ids = [int(i) for i in record["Transaction_IDs"].split(",") if i]
        placeholders = ",".join("?" * len(ids))
        connection.execute(
            f"UPDATE {ledger_name} SET {RECONCILED_COLUMN} = NULL WHERE Transaction_ID IN ({placeholders});",
            tuple(ids),
        )
    connection.execute("DELETE FROM tbl_Reconciliations WHERE Reconciliation_ID = ?;", (int(record["Reconciliation_ID"]),))
    connection.commit()
    return record
