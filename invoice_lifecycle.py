"""Invoice lifecycle: status transitions, their ledger entries, and an
auditable history (ST-008).

Statuses and allowed transitions::

    Due      -> Overdue, Paid, Canceled
    Overdue  -> Paid, Canceled
    Paid     -> Refunded
    Refunded -> (final)
    Canceled -> (final)

Ledger entries (all amounts in cents; AR = 10006 Accounts Receivable,
Sales = 15001, Sales Tax Payable = 13003):

    Post (Due/Overdue):   Dr AR            / Cr Sales      subtotal
                          Dr AR            / Cr Sales Tax  tax
    Post (Paid at once):  Dr deposit acct  / Cr Sales      subtotal
                          Dr deposit acct  / Cr Sales Tax  tax
    Paid later:           Dr deposit acct  / Cr AR         subtotal
                          Dr deposit acct  / Cr AR         tax
    Refunded:             Dr Sales         / Cr refund acct subtotal
                          Dr Sales Tax     / Cr refund acct tax
    Canceled (unpaid):    Dr Sales         / Cr AR         subtotal
                          Dr Sales Tax     / Cr AR         tax

Every transition writes a row to ``tbl_Invoice_History`` naming the event,
the previous and new status, the amount, the account used, and the ledger
transaction IDs it created, so the full story of an invoice can be shown
and audited.  ``timeline`` merges that history with the ledger entries that
carry the invoice's tracking code, so invoices created before this table
existed still get a history derived from the ledger.
"""

import accounting
import db_calls as db
import iceberg_time

STATUSES = ("Due", "Overdue", "Paid", "Refunded", "Canceled")
TRANSITIONS = {
    "Due": {"Overdue", "Paid", "Canceled"},
    "Overdue": {"Paid", "Canceled"},
    "Paid": {"Refunded"},
    "Refunded": set(),
    "Canceled": set(),
}
NEEDS_ACCOUNT = {"Paid", "Refunded"}

HISTORY_SCHEMA = """CREATE TABLE IF NOT EXISTS tbl_Invoice_History (
    History_ID INTEGER NOT NULL,
    Invoice_ID INTEGER NOT NULL,
    Event VARCHAR(9999) NOT NULL,
    From_Status VARCHAR(16),
    To_Status VARCHAR(16) NOT NULL,
    Amount INTEGER NOT NULL,
    Account CHAR(5),
    Transaction_IDs VARCHAR(9999),
    Notes VARCHAR(9999),
    Created_Time VARCHAR(9999) NOT NULL,
    PRIMARY KEY ("History_ID" AUTOINCREMENT)
);"""


class InvoiceError(Exception):
    pass


def ensure_schema(connection):
    db.create_tables(connection, HISTORY_SCHEMA)


def allowed_transitions(status):
    return set(TRANSITIONS.get(status, set()))


def check_transition(current, new):
    """Return an error message if ``current -> new`` is not allowed, else None."""
    if new == current:
        return f"The invoice is already {current}."
    if new not in STATUSES:
        return f"'{new}' is not an invoice status."
    if new not in TRANSITIONS.get(current, set()):
        options = ", ".join(sorted(TRANSITIONS.get(current, set()))) or "none"
        explanations = {
            ("Paid", "Canceled"): "A paid invoice cannot be canceled; refund it instead.",
            ("Due", "Refunded"): "Only a paid invoice can be refunded.",
            ("Overdue", "Refunded"): "Only a paid invoice can be refunded.",
        }
        return explanations.get((current, new), f"An invoice that is {current} can only change to: {options}.")
    return None


# ---------------------------------------------------------------- ledger


def _insert_entry(connection, ledger_name, invoice, credit, debit, amount, name, date):
    transaction_id = accounting.next_transaction_id(connection, ledger_name)
    stamp = iceberg_time.storage_timestamp()
    query = f"""INSERT INTO {ledger_name} (Transaction_ID, Credit_Acct, Debit_Acct, Amount, Name, Notes, Created_Time,
        Edited_Time, Transaction_Date, Record_Image, Vendor, Customer)
        VALUES ({transaction_id}, '{credit}', '{debit}', {int(amount)}, '{accounting.sql_text(name)}',
        '{accounting.sql_text(invoice['Tracking_Code'])}', '{stamp}', '{stamp}', '{date}',
        '{accounting.sql_text(invoice.get('Location', ''))}', '', '{accounting.sql_text(invoice['Customer_ID'])}');"""
    outcome = db.execute_query(connection, query)
    if outcome != "Query executed successfully":
        raise InvoiceError(f"Ledger entry '{name}' could not be written: {outcome}")
    return transaction_id


def _post_pair(connection, ledger_name, invoice, debit_sub, credit_sub, debit_tax, credit_tax, label, date):
    """Write the subtotal entry and, when there is tax, the tax entry."""
    ids = [_insert_entry(connection, ledger_name, invoice, credit_sub, debit_sub, int(invoice["Subtotal"]), label, date)]
    if int(invoice.get("Sales_Tax") or 0) > 0:
        ids.append(_insert_entry(connection, ledger_name, invoice, credit_tax, debit_tax, int(invoice["Sales_Tax"]), f"{label} Sales Tax", date))
    return ids


def record_history(connection, invoice_id, event, from_status, to_status, amount=0, account=None, transaction_ids=None, notes=""):
    ensure_schema(connection)
    ids = ",".join(str(i) for i in (transaction_ids or []))
    query = f"""INSERT INTO tbl_Invoice_History (Invoice_ID, Event, From_Status, To_Status, Amount, Account, Transaction_IDs, Notes, Created_Time)
        VALUES ({int(invoice_id)}, '{accounting.sql_text(event)}', {"NULL" if from_status is None else "'" + accounting.sql_text(from_status) + "'"},
        '{accounting.sql_text(to_status)}', {int(amount)}, {"NULL" if not account else "'" + accounting.sql_text(account) + "'"},
        '{ids}', '{accounting.sql_text(notes)}', '{iceberg_time.storage_timestamp()}');"""
    return db.execute_query(connection, query)


# ------------------------------------------------------------- transitions


def post_invoice(connection, ledger_name, invoice, deposit_account=None, date=None):
    """Write the ledger entries for a newly created invoice and its history row.

    ``invoice`` must already be saved in ``tbl_Invoices``.  For a Paid
    invoice ``deposit_account`` is the asset account that received the
    money; otherwise Accounts Receivable is debited.
    """
    date = date or iceberg_time.local_date_string()
    status = invoice["Status"]
    if status == "Paid":
        if not deposit_account:
            raise InvoiceError("A deposit account is required for an invoice that is already paid.")
        debit = str(deposit_account)
    else:
        debit = accounting.ACCOUNTS_RECEIVABLE
    ids = _post_pair(
        connection, ledger_name, invoice,
        debit_sub=debit, credit_sub=accounting.SALES,
        debit_tax=debit, credit_tax=accounting.SALES_TAX_PAYABLE,
        label=f"Invoice {invoice['Invoice_ID']}", date=date,
    )
    record_history(
        connection, invoice["Invoice_ID"], "Invoice created", None, status,
        amount=int(invoice["Total"]), account=debit if status == "Paid" else accounting.ACCOUNTS_RECEIVABLE,
        transaction_ids=ids, notes=f"Due {invoice.get('Due_Date', '')}",
    )
    return ids


def change_status(connection, ledger_name, invoice, new_status, account=None, date=None, invoice_repo=None):
    """Apply a status change, posting ledger entries and history.

    Returns ``{"ok": bool, "message": str, "transaction_ids": [...], "status": new_status}``.
    Nothing is written when the transition is not allowed.
    """
    current = invoice["Status"]
    problem = check_transition(current, new_status)
    if problem:
        return {"ok": False, "message": problem, "transaction_ids": [], "status": current}
    if new_status in NEEDS_ACCOUNT and not account:
        what = "deposit" if new_status == "Paid" else "refund source"
        return {"ok": False, "message": f"Select the {what} account.", "transaction_ids": [], "status": current}
    account = str(account) if account else None
    date = date or iceberg_time.local_date_string()
    total = int(invoice["Total"])
    label = f"Invoice {invoice['Invoice_ID']}"
    try:
        if new_status == "Overdue":
            ids = []
            event, amount, used = "Marked overdue", 0, None
        elif new_status == "Paid":
            ids = _post_pair(
                connection, ledger_name, invoice,
                debit_sub=account, credit_sub=accounting.ACCOUNTS_RECEIVABLE,
                debit_tax=account, credit_tax=accounting.ACCOUNTS_RECEIVABLE,
                label=f"{label} Paid", date=date,
            )
            event, amount, used = "Payment received", total, account
        elif new_status == "Refunded":
            ids = _post_pair(
                connection, ledger_name, invoice,
                debit_sub=accounting.SALES, credit_sub=account,
                debit_tax=accounting.SALES_TAX_PAYABLE, credit_tax=account,
                label=f"{label} Refunded", date=date,
            )
            event, amount, used = "Refund issued", total, account
        elif new_status == "Canceled":
            ids = _post_pair(
                connection, ledger_name, invoice,
                debit_sub=accounting.SALES, credit_sub=accounting.ACCOUNTS_RECEIVABLE,
                debit_tax=accounting.SALES_TAX_PAYABLE, credit_tax=accounting.ACCOUNTS_RECEIVABLE,
                label=f"{label} Canceled", date=date,
            )
            event, amount, used = "Invoice canceled", total, accounting.ACCOUNTS_RECEIVABLE
        else:  # pragma: no cover - guarded by check_transition
            raise InvoiceError(f"Unhandled status {new_status}")
    except InvoiceError as error:
        return {"ok": False, "message": str(error), "transaction_ids": [], "status": current}

    stamp = iceberg_time.storage_timestamp()
    if invoice_repo is not None:
        invoice_repo.update(invoice_id=invoice["Invoice_ID"], status=new_status, edited_time=stamp)
    else:
        db.execute_query(
            connection,
            f"UPDATE tbl_Invoices SET Status = '{new_status}', Edited_Time = '{stamp}' WHERE Invoice_ID = {int(invoice['Invoice_ID'])};",
        )
    record_history(connection, invoice["Invoice_ID"], event, current, new_status, amount=amount, account=used, transaction_ids=ids)
    invoice["Status"] = new_status
    entries = f" Ledger entries: {', '.join(str(i) for i in ids)}." if ids else ""
    return {
        "ok": True,
        "message": f"{label}: {event} ({current} -> {new_status}).{entries}",
        "transaction_ids": ids,
        "status": new_status,
    }


# ----------------------------------------------------------------- history


def history(connection, invoice_id):
    ensure_schema(connection)
    rows = db.execute_read_query_dict(
        connection, f"SELECT * FROM tbl_Invoice_History WHERE Invoice_ID = {int(invoice_id)} ORDER BY History_ID;"
    )
    return rows if isinstance(rows, list) else []


def ledger_entries(connection, ledger_name, invoice):
    """Ledger rows that belong to this invoice (matched by tracking code)."""
    code = accounting.sql_text(invoice.get("Tracking_Code") or "")
    if not code:
        return []
    rows = db.execute_read_query_dict(
        connection, f"SELECT * FROM {ledger_name} WHERE Notes = '{code}' ORDER BY Transaction_ID;"
    )
    return rows if isinstance(rows, list) else []


def timeline(connection, ledger_name, invoice, account_names=None):
    """Merge history rows and ledger entries into one ordered list of events.

    Each item: ``{"when", "event", "from_status", "to_status", "amount",
    "account", "transactions", "source"}`` where ``source`` is "history" or
    "ledger".  Ledger entries already referenced by a history row are folded
    into it; the rest (legacy invoices) appear as their own items.
    """
    names = account_names or {}
    items = []
    referenced = set()
    for row in history(connection, invoice["Invoice_ID"]):
        ids = [int(i) for i in str(row["Transaction_IDs"] or "").split(",") if i.strip()]
        referenced.update(ids)
        items.append({
            "when": row["Created_Time"],
            "event": row["Event"],
            "from_status": row["From_Status"] or "",
            "to_status": row["To_Status"],
            "amount": int(row["Amount"]),
            "account": _label(row["Account"], names),
            "transactions": ids,
            "source": "history",
        })
    if not items:
        items.append({
            "when": invoice.get("Created_Time", ""),
            "event": "Invoice created",
            "from_status": "",
            "to_status": "Due",
            "amount": int(invoice.get("Total") or 0),
            "account": "",
            "transactions": [],
            "source": "invoice",
        })
    for row in ledger_entries(connection, ledger_name, invoice):
        if int(row["Transaction_ID"]) in referenced:
            continue
        items.append({
            "when": row["Created_Time"],
            "event": f"Ledger: {row['Name']}",
            "from_status": "",
            "to_status": "",
            "amount": int(row["Amount"]),
            "account": f"Dr {_label(row['Debit_Acct'], names)} / Cr {_label(row['Credit_Acct'], names)}",
            "transactions": [int(row["Transaction_ID"])],
            "source": "ledger",
        })
    items.sort(key=lambda i: (_sort_key(i["when"]), i["transactions"][:1] or [0]))
    return items


def _label(account_id, names):
    if not account_id:
        return ""
    name = names.get(str(account_id))
    return f"{account_id} {name}" if name else str(account_id)


def _sort_key(value):
    parsed = iceberg_time.parse_timestamp(value)
    return parsed.timestamp() if parsed else 0.0


def timeline_rows(items):
    """Rows for the on-screen history table: When, Event, Status, Amount, Account, Ledger #s."""
    from iceberg_utils import format_currency

    rows = []
    for item in items:
        status = f"{item['from_status']} -> {item['to_status']}" if item["from_status"] else item["to_status"]
        rows.append([
            iceberg_time.display_timestamp(item["when"], seconds=False),
            item["event"],
            status,
            format_currency(item["amount"]) if item["amount"] else "",
            item["account"],
            ", ".join(str(t) for t in item["transactions"]),
        ])
    return rows
