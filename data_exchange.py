"""CSV export and import (ST-010).

Exports are UTF-8 CSV files with a header row; money is written in dollars
with two decimals so accountants can open them directly in a spreadsheet.
Stored timestamps are converted to the local display format.

The transaction importer accepts the documented column layout (see
``docs/IMPORT_EXPORT.md``), validates every row with ``validation`` and
writes nothing unless the whole file is valid, so a half-imported file
never ends up in the books.
"""

import csv
import os

import accounting
import db_calls as db
import iceberg_time
import reports
import validation

IMPORT_COLUMNS = ["Date", "Name", "Amount", "Debit_Account", "Credit_Account", "Notes", "Vendor"]
IMPORT_REQUIRED = ["Date", "Name", "Amount", "Debit_Account", "Credit_Account"]
IMPORT_ALIASES = {
    "date": "Date",
    "transaction_date": "Date",
    "name": "Name",
    "description": "Name",
    "payee": "Name",
    "amount": "Amount",
    "debit": "Debit_Account",
    "debit_account": "Debit_Account",
    "debit_acct": "Debit_Account",
    "credit": "Credit_Account",
    "credit_account": "Credit_Account",
    "credit_acct": "Credit_Account",
    "notes": "Notes",
    "memo": "Notes",
    "vendor": "Vendor",
}

EXPORT_TABLES = {
    "accounts": "tbl_Accounts",
    "vendors": "tbl_Vendors",
    "customers": "tbl_Customers",
    "services": "tbl_Skus",
    "invoices": "tbl_Invoices",
    "invoice_history": "tbl_Invoice_History",
    "reconciliations": "tbl_Reconciliations",
}
MONEY_COLUMNS = {"Amount", "Subtotal", "Sales_Tax", "Total", "Price", "Statement_Balance", "Cleared_Balance"}
TIME_COLUMNS = {"Created_Time", "Edited_Time"}


class ImportError_(Exception):
    """Raised when an import file cannot be used.  ``errors`` lists row problems."""

    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or []


def _write_csv(path, header, rows):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def _cell(column, value):
    if value is None:
        return ""
    if column in MONEY_COLUMNS:
        try:
            return f"{int(value) / 100:.2f}"
        except (TypeError, ValueError):
            return value
    if column in TIME_COLUMNS:
        return iceberg_time.display_timestamp(value)
    return value


# ----------------------------------------------------------------- exports


def export_table(connection, table, path):
    """Export any table to CSV.  Returns (path, row_count)."""
    rows = db.execute_read_query_dict(connection, f"SELECT * FROM {table};")
    if not isinstance(rows, list):
        raise ImportError_(f"Table {table} could not be read: {rows}")
    if rows:
        header = list(rows[0].keys())
    else:
        header = accounting_columns(connection, table)
    _write_csv(path, header, [[_cell(c, row.get(c)) for c in header] for row in rows])
    return path, len(rows)


def accounting_columns(connection, table):
    rows = db.execute_read_query_dict(connection, f"PRAGMA table_info({table});")
    return [row["name"] for row in rows] if isinstance(rows, list) else []


def export_ledger(connection, ledger_name, accounts, path, start=None, end=None):
    """Export the ledger with account names and local timestamps."""
    names = accounting.account_name_map(accounts)
    rows = accounting.read_ledger(connection, ledger_name, start, end)
    header = [
        "Transaction_ID", "Transaction_Date", "Name", "Amount", "Debit_Account", "Debit_Account_Name",
        "Credit_Account", "Credit_Account_Name", "Notes", "Vendor", "Customer", "Record_Image",
        "Reconciled_Date", "Created_Time", "Edited_Time",
    ]
    out = []
    for row in rows:
        out.append([
            row["Transaction_ID"], str(row["Transaction_Date"])[:10], row["Name"], f"{int(row['Amount']) / 100:.2f}",
            row["Debit_Acct"], names.get(str(row["Debit_Acct"]), ""), row["Credit_Acct"], names.get(str(row["Credit_Acct"]), ""),
            row.get("Notes") or "", row.get("Vendor") or "", row.get("Customer") or "", row.get("Record_Image") or "",
            row.get("Reconciled_Date") or "", iceberg_time.display_timestamp(row.get("Created_Time")),
            iceberg_time.display_timestamp(row.get("Edited_Time")),
        ])
    _write_csv(path, header, out)
    return path, len(out)


def export_report(report, path):
    rows = reports.report_rows(report)
    header = ["Section", "Line", "Amount"] if "table" not in report else ["Section", "Line", "Amounts..."]
    _write_csv(path, header, rows)
    return path


def export_all(connection, ledger_name, accounts, folder):
    """Write every table plus the ledger into ``folder``.  Returns {name: (path, count)}."""
    stamp = iceberg_time.file_timestamp()
    os.makedirs(folder, exist_ok=True)
    written = {}
    written["ledger"] = export_ledger(connection, ledger_name, accounts, os.path.join(folder, f"ledger_{stamp}.csv"))
    for name, table in EXPORT_TABLES.items():
        if not accounting_columns(connection, table):
            continue  # optional table not present in this database
        written[name] = export_table(connection, table, os.path.join(folder, f"{name}_{stamp}.csv"))
    return written


# ----------------------------------------------------------------- imports


def _normalize_header(fieldnames):
    mapping = {}
    for raw in fieldnames or []:
        key = str(raw or "").strip().lstrip("\ufeff").lower().replace(" ", "_")
        if key in IMPORT_ALIASES:
            mapping[raw] = IMPORT_ALIASES[key]
    return mapping


def read_transactions_csv(path):
    """Parse the CSV into a list of field dicts (no validation yet)."""
    if not os.path.isfile(path):
        raise ImportError_(f"File not found: {path}")
    with open(path, "r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        mapping = _normalize_header(reader.fieldnames)
        missing = [c for c in IMPORT_REQUIRED if c not in mapping.values()]
        if missing:
            raise ImportError_(
                f"The file is missing required column(s): {', '.join(missing)}. "
                f"Expected header: {', '.join(IMPORT_COLUMNS)}."
            )
        records = []
        for line_number, row in enumerate(reader, start=2):
            fields = {mapping[k]: (v or "").strip() for k, v in row.items() if k in mapping}
            if not any(fields.values()):
                continue  # blank line
            fields["_line"] = line_number
            records.append(fields)
    return records


def validate_transactions(records, account_ids, existing_rows=None):
    """Validate parsed records.  Returns (cleaned_rows, errors, warnings)."""
    cleaned, errors, warnings = [], [], []
    seen = set()
    for fields in records:
        result = validation.validate_transaction(
            {
                "name": fields.get("Name"),
                "date": fields.get("Date"),
                "amount": fields.get("Amount"),
                "debit_account": fields.get("Debit_Account"),
                "credit_account": fields.get("Credit_Account"),
                "notes": fields.get("Notes", ""),
                "vendor": fields.get("Vendor", ""),
            },
            account_ids,
            existing=existing_rows,
        )
        line = fields.get("_line", "?")
        for error in result.errors:
            errors.append(f"Line {line}: {error}")
        for warning in result.warnings:
            warnings.append(f"Line {line}: {warning}")
        if result.ok:
            key = (result.cleaned["date"], result.cleaned["name"].casefold(), result.cleaned["amount"], result.cleaned["debit_account"], result.cleaned["credit_account"])
            if key in seen:
                warnings.append(f"Line {line}: duplicate of an earlier line in this file.")
            seen.add(key)
            cleaned.append(result.cleaned)
    return cleaned, errors, warnings


def import_transactions(connection, ledger_name, path, account_ids, existing_rows=None, dry_run=False):
    """Import transactions from ``path``.  All-or-nothing.

    Returns ``{"imported": n, "warnings": [...], "transaction_ids": [...]}``.
    Raises ``ImportError_`` (with ``.errors``) when any row is invalid.
    """
    records = read_transactions_csv(path)
    if not records:
        raise ImportError_("The file contains no transactions.")
    cleaned, errors, warnings = validate_transactions(records, account_ids, existing_rows)
    if errors:
        raise ImportError_(f"{len(errors)} problem(s) found; nothing was imported.", errors)
    if dry_run:
        return {"imported": 0, "warnings": warnings, "transaction_ids": [], "rows": cleaned}
    ids = []
    stamp = iceberg_time.storage_timestamp()
    connection.execute("BEGIN")
    try:
        for row in cleaned:
            transaction_id = accounting.next_transaction_id(connection, ledger_name)
            connection.execute(
                f"""INSERT INTO {ledger_name} (Transaction_ID, Credit_Acct, Debit_Acct, Amount, Name, Notes, Created_Time, Edited_Time, Transaction_Date, Record_Image, Vendor, Customer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (transaction_id, row["credit_account"], row["debit_account"], row["amount"], row["name"],
                 row["notes"], stamp, stamp, row["date"], "", row["vendor"], ""),
            )
            ids.append(transaction_id)
        connection.commit()
    except Exception as error:
        connection.rollback()
        raise ImportError_(f"Import failed and was rolled back: {error}")
    return {"imported": len(ids), "warnings": warnings, "transaction_ids": ids, "rows": cleaned}


def write_import_template(path):
    """Write a sample CSV showing the expected layout."""
    today = iceberg_time.local_date_string()
    rows = [
        [today, "Office supplies", "42.18", "11001", "10002", "Printer paper", ""],
        [today, "Client payment", "1500.00", "10002", "15001", "", ""],
    ]
    return _write_csv(path, IMPORT_COLUMNS, rows)
