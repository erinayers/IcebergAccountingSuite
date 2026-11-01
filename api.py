"""Application API for the web interface.

Every public method takes and returns plain JSON-compatible values, never
raises, and reports problems as ``{"ok": False, "message": ..., "errors":
[{"field", "message"}]}`` so the front-end can show them next to the right
control.  Money is returned in cents; the front-end formats it.  The same
object can be driven from tests, from pywebview (``webapp.py``), or from any
other host.
"""

import datetime
import functools
import os
import traceback

import accounting
import backups
import books
import data_exchange
import db_calls as db
import iceberg_time
import invoice_lifecycle
import invoices
import preferences
import reconciliation
import records
import reports
import validation
from paths import Layout
from iceberg_utils import id_generator
from repository import AccountRepository, VendorRepository
from session import IcebergSession, open_session_log, save_session_log

from version import VERSION  # noqa: E402


def _errors(result):
    return [{"field": field, "message": message} for message, field in zip(result.errors, result.fields)]


def _failure(message, errors=None, **extra):
    out = {"ok": False, "message": message, "errors": errors or []}
    out.update(extra)
    return out


def _success(message="", **extra):
    out = {"ok": True, "message": message, "errors": []}
    out.update(extra)
    return out


def operation(requires_database=True):
    """Wrap an API method: refuse when no database is open, and turn any
    unexpected exception into an error response (the interface must never
    see a traceback).  Keeps the signature so the route table can check it."""
    def decorate(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if requires_database and not (self.session.database_loaded and self.session.connection):
                return _failure("Open or create a database first.")
            try:
                return func(self, *args, **kwargs)
            except Exception as error:
                self._log(f"Unexpected error in {func.__name__}: {error}")
                return _failure(f"Something went wrong: {error}", detail=traceback.format_exc())
        return wrapper
    return decorate


def _row(transaction, names):
    debit, credit = str(transaction["Debit_Acct"]), str(transaction["Credit_Acct"])
    return {
        "id": int(transaction["Transaction_ID"]),
        "date": str(transaction["Transaction_Date"])[:10],
        "name": transaction["Name"],
        "amount": int(transaction["Amount"]),
        "debit": debit,
        "debit_name": names.get(debit, ""),
        "credit": credit,
        "credit_name": names.get(credit, ""),
        "notes": transaction.get("Notes") or "",
        "vendor": transaction.get("Vendor") or "",
        "customer": transaction.get("Customer") or "",
        "record_image": transaction.get("Record_Image") or "",
        "reconciled": transaction.get("Reconciled_Date") or "",
        "created": iceberg_time.display_timestamp(transaction.get("Created_Time"), seconds=False),
        "edited": iceberg_time.display_timestamp(transaction.get("Edited_Time"), seconds=False),
    }


class CoreApi:
    """Databases, dashboard, ledger, reports."""

    def __init__(self, folder=".", session=None, layout=None):
        # ``layout`` describes where files live (paths.Layout).  Without one, the
        # folder is used portable-style: books next to it, resources (fonts, docs) inside it.
        self.layout = layout or Layout(folder, mode="portable", app_dir=os.path.abspath(folder), resources=os.path.abspath(folder))
        self.layout.ensure()
        self.folder = self.layout.databases
        self.session = session or IcebergSession(session_log_connection=open_session_log(self.layout.session_log_dir))
        self.session.window = False
        self.session.log_file = self.layout.log_file
        self.properties = {}

    # ------------------------------------------------------------ helpers

    def _log(self, message):
        self.session.current_console_messages = self.session.console_log(message, self.session.current_console_messages)

    def _accounts(self):
        return AccountRepository(self.session.connection).get_all()

    def _names(self, accounts=None):
        return accounting.account_name_map(accounts or self._accounts())

    def _rows(self):
        return accounting.read_ledger(self.session.connection, self.session.ledger_name)

    # ------------------------------------------------------------ app state

    def status(self):
        s = self.session
        return {
            "version": VERSION,
            "database_loaded": bool(s.database_loaded),
            "db_name": s.db_name,
            "business_name": self.properties.get("business_name", ""),
            "unsaved": s.has_unsaved_changes(),
            "last_saved": s.last_saved_display,
            "autosave_in": int(s.seconds_until_autosave()) if s.database_loaded else None,
            "clock": iceberg_time.format_display(),
            "console": s.current_console_messages[:50],
            "paths": self.layout.describe(),
        }

    def paths(self):
        """Where the files are (ST-023), for the Tools > Where are my files dialog."""
        return _success(paths=self.layout.describe(), portable=self.layout.mode == "portable")

    def recent_databases(self):
        """The .icb files in the Iceberg folder, newest first."""
        found = []
        for name in os.listdir(self.folder):
            if name.lower().endswith(".icb") and name != "sessions.icbs":
                path = os.path.join(self.folder, name)
                stat = os.stat(path)
                found.append({
                    "db_name": name,
                    "label": name[:-4].replace("_", " "),
                    "modified": iceberg_time.display_timestamp(datetime.datetime.fromtimestamp(stat.st_mtime, iceberg_time.UTC).isoformat(), seconds=False),
                    "size": stat.st_size,
                    "backups": len(backups.list_backups(path, backup_root=self.layout.backups)),
                })
        found.sort(key=lambda f: f["db_name"].casefold())
        return found

    def shutdown(self):
        """Save everything before the window closes.  Returns the save outcome."""
        outcome = self.save() if self.session.database_loaded else _success("No database open.")
        save_session_log(self.session, self.layout.session_log_dir)
        return outcome

    # ------------------------------------------------------------ databases

    @operation(requires_database=False)
    def create_database(self, fields):
        fields = fields or {}
        stem = validation.database_file_stem(fields.get("business_name"))
        checked = validation.validate_database_properties(
            fields, new_database=True, existing_file=os.path.join(self.folder, f"{stem}.icb") if stem else None
        )
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked))
        properties = {k: fields.get(k, "") for k in books.PROPERTY_NAMES if k not in ("ledger_name",)}
        properties["sales_tax"] = checked.cleaned["sales_tax"]
        try:
            opened = books.create_database(checked.cleaned["db_name"], properties, fields["save_location"], self.folder)
        except books.BooksError as error:
            return _failure(str(error))
        self._adopt(opened)
        self._log(f"Database created: {opened['db_name']}; filekey saved to {opened['key_path']}")
        return _success(f"Created {opened['db_name']}. Keep the filekey safe: {opened['key_path']}", db_name=opened["db_name"], key_path=opened["key_path"])

    @operation(requires_database=False)
    def open_database(self, key_path):
        if not key_path:
            return _failure("Select a filekey (.icbkey) to open a database.")
        try:
            opened = books.open_database(key_path, self.folder)
        except books.BooksError as error:
            return _failure(str(error))
        self._adopt(opened)
        self._log(f"Database opened: {opened['db_name']}")
        return _success(f"Opened {opened['db_name']}.", db_name=opened["db_name"], business_name=self.properties.get("business_name", ""))

    def _adopt(self, opened):
        s = self.session
        if s.connection:
            try:
                s.connection.close()
            except Exception:
                pass
        s.connection = opened["connection"]
        s.db_name = opened["db_name"]
        s.ledger_name = opened["ledger_name"]
        s.filename = os.path.basename(opened["key_path"])
        s.save_location = os.path.dirname(opened["key_path"]) + os.sep
        s.database_loaded = True
        s.last_autosave = iceberg_time.monotonic()
        s.reset_change_tracking()
        s.mark_saved()
        self.properties = books.read_properties(s.connection)

    @operation()
    @operation()
    def save(self, reason="Manual save"):
        s = self.session
        key_path = os.path.join(s.save_location, s.filename)
        result = db.save_encrypted_database(s.connection, os.path.join(self.folder, s.db_name), key_path, backup_root=self.layout.backups)
        self._log(f"{reason}: {result.message}")
        if not result.ok:
            return _failure(result.message)
        s.mark_saved()
        s.last_autosave = iceberg_time.monotonic()
        return _success(f"{reason}: saved {s.db_name}.", backup=result.backup_path, last_saved=s.last_saved_display)

    def autosave_if_due(self):
        s = self.session
        if s.database_loaded and s.seconds_until_autosave() <= 0:
            if s.has_unsaved_changes():
                return self.save("Autosave")
            s.last_autosave = iceberg_time.monotonic()
        return _success("")

    def properties_summary(self):
        return dict(self.properties)

    # ------------------------------------------------------------ dashboard

    @operation()
    @operation()
    def dashboard(self, type_prefix="", year=""):
        rows = self._rows()
        accounts = self._accounts()
        years = books.ledger_years(rows)
        return _success(
            summary=books.dashboard_summary(rows, accounts),
            accounts=books.chart_of_accounts(rows, accounts, type_prefix or None, year or None),
            years=years,
            business=self.properties,
            filters={"type_prefix": type_prefix or "", "year": year or ""},
        )

    @operation()
    def accounts(self):
        return _success(accounts=[{"id": str(a["Account_ID"]), "name": a["Name"], "type": accounting.type_name(a["Account_ID"])}
                                  for a in sorted(self._accounts(), key=lambda a: str(a["Account_ID"]))])

    @operation()
    @operation()
    def account_register(self, account_id):
        account_id = str(account_id)
        accounts = self._accounts()
        names = self._names(accounts)
        account = next((a for a in accounts if str(a["Account_ID"]) == account_id), None)
        if not account:
            return _failure(f"Account {account_id} does not exist.")
        balance = 0
        register = []
        for row in sorted(self._rows(), key=lambda r: (str(r["Transaction_Date"]), int(r["Transaction_ID"]))):
            if account_id not in (str(row["Debit_Acct"]), str(row["Credit_Acct"])):
                continue
            effect = accounting.signed_effect(account_id, row)
            balance += effect
            item = _row(row, names)
            item["effect"] = effect
            item["running_balance"] = balance
            register.append(item)
        register.reverse()
        return _success(account={"id": account_id, "name": account["Name"], "type": accounting.type_name(account_id),
                                 "institution": account.get("Institution") or "", "notes": account.get("Notes") or "",
                                 "balance": balance}, rows=register)

    # ------------------------------------------------------------ ledger

    @operation()
    @operation()
    def ledger(self, search="", year=""):
        rows = self._rows()
        names = self._names()
        found = books.search_ledger(rows, search, year or None, names)
        return _success(rows=[_row(r, names) for r in found], years=books.ledger_years(rows), total=len(rows),
                        filters={"search": search or "", "year": year or ""})

    @operation()
    def transaction(self, transaction_id):
        row = books.get_transaction(self.session.connection, self.session.ledger_name, transaction_id)
        if not row:
            return _failure(f"Transaction {transaction_id} was not found.")
        return _success(transaction=_row(row, self._names()))

    @operation()
    def transaction_form(self):
        """Everything the New Transaction form needs: accounts, vendors, next id, today."""
        vendors = VendorRepository(self.session.connection).get_all()
        return _success(
            next_id=accounting.next_transaction_id(self.session.connection, self.session.ledger_name),
            today=iceberg_time.local_date_string(),
            accounts=self.accounts()["accounts"],
            vendors=[{"id": str(v["Vendor_ID"]), "name": v["Business_Name"]} for v in vendors] if isinstance(vendors, list) else [],
        )

    @operation()
    @operation()
    def add_transaction(self, fields, confirm_warnings=False):
        fields = fields or {}
        checked = validation.validate_transaction(fields, [str(a["Account_ID"]) for a in self._accounts()], existing=self._rows())
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked), warnings=checked.warnings)
        if checked.warnings and not confirm_warnings:
            return _failure("Please confirm before saving.", warnings=checked.warnings, needs_confirmation=True)
        transaction_id = books.add_transaction(self.session.connection, self.session.ledger_name, checked.cleaned,
                                               record_image=fields.get("record_image", ""))
        self._log(f"Transaction {transaction_id} added: {checked.cleaned['name']}")
        return _success(f"Transaction {transaction_id} '{checked.cleaned['name']}' recorded.", id=transaction_id)

    @operation()
    @operation()
    def update_transaction(self, transaction_id, fields):
        fields = fields or {}
        if not books.get_transaction(self.session.connection, self.session.ledger_name, transaction_id):
            return _failure(f"Transaction {transaction_id} was not found.")
        checked = validation.validate_transaction(fields, [str(a["Account_ID"]) for a in self._accounts()])
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked))
        books.update_transaction(self.session.connection, self.session.ledger_name, transaction_id, checked.cleaned)
        self._log(f"Transaction {transaction_id} updated.")
        return _success(f"Transaction {transaction_id} updated.", id=int(transaction_id))

    # ------------------------------------------------------------ reports

    @operation()
    @operation()
    def report(self, report_type, start, end):
        try:
            start = validation.parse_date(start, "From date")
            end = validation.parse_date(end, "To date")
        except ValueError as error:
            return _failure(str(error))
        if start > end:
            return _failure("The From date must not be after the To date.")
        try:
            report = reports.run(report_type, self._rows(), self._accounts(), start, end)
        except ValueError as error:
            return _failure(str(error))
        self.session.last_report = report
        return _success(report=report, text=reports.render_text(report))

    def report_periods(self):
        return _success(presets=[{"name": name, "start": reports.period_bounds(name)[0], "end": reports.period_bounds(name)[1]}
                                 for name in reports.PERIOD_PRESETS if name != "Custom"],
                        types=reports.REPORT_TYPES)


# =====================================================================
# Records, invoices, reconciliation, properties, backups, exchange
# =====================================================================


class IcebergApi(CoreApi):
    """The complete application API used by the web interface."""

    # ------------------------------------------------------------ accounts

    @operation()
    def account(self, account_id):
        account = records.get_account(self.session.connection, account_id)
        return _success(account=account) if account else _failure(f"Account {account_id} does not exist.")

    def account_form(self):
        return _success(types=[{"prefix": p, "label": l} for p, l in records.ACCOUNT_TYPE_OPTIONS],
                        bank_account_types=["", "Checking", "Savings", "Passbook", "Certificate of Deposit"])

    @operation()
    @operation()
    def add_account(self, fields):
        fields = fields or {}
        existing = [a["name"] for a in records.list_accounts(self.session.connection)]
        checked = validation.validate_account(fields.get("name"), existing, fields.get("type_prefix"))
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked))
        account_id = records.add_account(self.session.connection, fields.get("type_prefix"), checked.cleaned["name"], fields.get("notes", ""),
                                         fields.get("institution", ""), fields.get("bank_account_type", ""), fields.get("routing_number", ""), fields.get("account_number", ""))
        self._log(f"Account {account_id} '{checked.cleaned['name']}' added.")
        return _success(f"Account {account_id} '{checked.cleaned['name']}' added.", id=str(account_id))

    @operation()
    @operation()
    def update_account(self, account_id, fields):
        fields = fields or {}
        current = records.get_account(self.session.connection, account_id)
        if not current:
            return _failure(f"Account {account_id} does not exist.")
        others = [a["name"] for a in records.list_accounts(self.session.connection) if a["id"] != str(account_id)]
        checked = validation.validate_account(fields.get("name"), others)
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked))
        records.update_account(self.session.connection, account_id, checked.cleaned["name"], fields.get("notes", ""), fields.get("institution", ""),
                               fields.get("bank_account_type", ""), fields.get("routing_number", ""), fields.get("account_number", ""))
        self._log(f"Account {account_id} updated.")
        return _success(f"Account {account_id} updated.", id=str(account_id))

    # ------------------------------------------------------------- vendors

    @operation()
    def vendors(self, search=""):
        return _success(vendors=records.list_vendors(self.session.connection, search), phone_types=records.PHONE_TYPES, filters={"search": search or ""})

    @operation()
    def vendor(self, vendor_id):
        vendor = records.get_vendor(self.session.connection, vendor_id)
        return _success(vendor=vendor) if vendor else _failure(f"Vendor {vendor_id} does not exist.")

    @operation()
    @operation()
    def save_vendor(self, fields, vendor_id=None):
        fields = fields or {}
        others = [v["name"] for v in records.list_vendors(self.session.connection) if v["id"] != str(vendor_id)]
        checked = validation.validate_vendor(fields, others)
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked))
        fields = dict(fields, name=checked.cleaned["name"])
        if vendor_id:
            if not records.get_vendor(self.session.connection, vendor_id):
                return _failure(f"Vendor {vendor_id} does not exist.")
            records.update_vendor(self.session.connection, vendor_id, fields)
            self._log(f"Vendor {vendor_id} updated.")
            return _success(f"Vendor '{fields['name']}' updated.", id=str(vendor_id))
        new_id = records.add_vendor(self.session.connection, fields)
        self._log(f"Vendor {new_id} '{fields['name']}' added.")
        return _success(f"Vendor '{fields['name']}' added.", id=str(new_id))

    # ----------------------------------------------------------- customers

    @operation()
    def customers(self, search=""):
        return _success(customers=records.list_customers(self.session.connection, search), phone_types=records.PHONE_TYPES, filters={"search": search or ""})

    @operation()
    def customer(self, customer_id):
        customer = records.get_customer(self.session.connection, customer_id)
        if not customer:
            return _failure(f"Customer {customer_id} does not exist.")
        return _success(customer=customer, invoices=[i for i in invoices.list_invoices(self.session.connection) if i["customer_id"] == str(customer_id)])

    @operation()
    @operation()
    def save_customer(self, fields, customer_id=None):
        fields = fields or {}
        others = [{"Customer_Company_Name": c["company"], "Customer_First_Name": c["first_name"], "Customer_Last_Name": c["last_name"]}
                  for c in records.list_customers(self.session.connection) if c["id"] != str(customer_id)]
        checked = validation.validate_customer(fields, others)
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked))
        fields = dict(fields, **checked.cleaned)
        if customer_id:
            if not records.get_customer(self.session.connection, customer_id):
                return _failure(f"Customer {customer_id} does not exist.")
            records.update_customer(self.session.connection, customer_id, fields)
            self._log(f"Customer {customer_id} updated.")
            return _success("Customer updated.", id=str(customer_id))
        new_id = records.add_customer(self.session.connection, fields)
        self._log(f"Customer {new_id} added.")
        return _success("Customer added.", id=str(new_id))

    # ------------------------------------------------------------ services

    @operation()
    def services(self, search=""):
        return _success(services=records.list_services(self.session.connection, search), filters={"search": search or ""})

    @operation()
    @operation()
    def save_service(self, fields, sku=None):
        fields = fields or {}
        others = [s["description"] for s in records.list_services(self.session.connection) if s["sku"] != str(sku)]
        taxable = fields.get("taxable")
        taxable_text = "True" if taxable in (True, "True", "true", "Yes", "yes", "1", 1) else ("False" if taxable in (False, "False", "false", "No", "no", "0", 0) else "")
        checked = validation.validate_service({"description": fields.get("description"), "price": fields.get("price"), "taxable": taxable_text}, others)
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked))
        c = checked.cleaned
        if sku:
            if not records.get_service(self.session.connection, sku):
                return _failure(f"Service {sku} does not exist.")
            records.update_service(self.session.connection, sku, c["description"], c["price"], taxable_text == "True", fields.get("long_description", ""))
            self._log(f"Service {sku} updated.")
            return _success(f"Service '{c['description']}' updated.", id=str(sku))
        new_sku = records.add_service(self.session.connection, c["description"], c["price"], taxable_text == "True", fields.get("long_description", ""))
        self._log(f"Service {new_sku} '{c['description']}' added.")
        return _success(f"Service '{c['description']}' added.", id=new_sku)

    # ------------------------------------------------------------ invoices

    @operation()
    def invoices(self, search=""):
        return _success(invoices=invoices.list_invoices(self.session.connection, search), filters={"search": search or ""})

    @operation()
    @operation()
    def invoice(self, invoice_id):
        view = invoices.get_invoice(self.session.connection, invoice_id)
        if not view:
            return _failure(f"Invoice {invoice_id} was not found.")
        raw = invoices.raw_invoice(self.session.connection, invoice_id)
        timeline = invoice_lifecycle.timeline(self.session.connection, self.session.ledger_name, raw, self._names())
        return _success(invoice=view, history=invoice_lifecycle.timeline_rows(timeline),
                        asset_accounts=[a for a in records.list_accounts(self.session.connection) if a["type_prefix"] == "10" and a["id"] != accounting.ACCOUNTS_RECEIVABLE])

    @operation()
    def invoice_form(self):
        tax_rate = self.properties.get("sales_tax") or "0"
        return _success(next_id=invoices.next_invoice_id(self.session.connection), today=iceberg_time.local_date_string(),
                        sales_tax_rate=str(tax_rate), customers=records.list_customers(self.session.connection),
                        services=records.list_services(self.session.connection),
                        asset_accounts=[a for a in records.list_accounts(self.session.connection) if a["type_prefix"] == "10" and a["id"] != accounting.ACCOUNTS_RECEIVABLE],
                        statuses=["Due", "Overdue", "Paid"], max_line_items=invoices.MAX_LINE_ITEMS)

    @operation()
    def invoice_totals(self, line_items, tax_rate=None):
        """Recompute subtotal/tax/total for the form as line items change."""
        taxable = {s["sku"]: s["taxable"] for s in records.list_services(self.session.connection)}
        rate = tax_rate if tax_rate not in (None, "") else (self.properties.get("sales_tax") or "0")
        try:
            subtotal, tax, total = invoices.totals(line_items or [], rate, taxable)
        except Exception as error:
            return _failure(f"Could not total the line items: {error}")
        return _success(subtotal=subtotal, sales_tax=tax, total=total)

    @operation()
    def invoice_line_item(self, sku, quantity):
        service = records.get_service(self.session.connection, sku)
        checked = validation.validate_line_item(quantity, sku_selected=bool(service))
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked))
        return _success(line_item=invoices.build_line_item(service, checked.cleaned["quantity"]))

    @operation()
    @operation()
    def create_invoice(self, fields, line_items):
        fields = fields or {}
        line_items = line_items or []
        asset_ids = [a["id"] for a in records.list_accounts(self.session.connection) if a["type_prefix"] == "10"]
        checked = validation.validate_invoice(fields, line_items, asset_account_ids=asset_ids)
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked))
        customer = records.get_customer(self.session.connection, fields.get("customer_id"))
        if not customer:
            return _failure("Select a customer.", [{"field": "customer", "message": "Select a customer from the list."}])
        taxable = {s["sku"]: s["taxable"] for s in records.list_services(self.session.connection)}
        rate = fields.get("sales_tax_rate") if fields.get("sales_tax_rate") not in (None, "") else (self.properties.get("sales_tax") or "0")
        subtotal, tax, total = invoices.totals(line_items, rate, taxable)
        if subtotal <= 0:
            return _failure("The invoice total must be greater than zero.", [{"field": "line_items", "message": "Add at least one line item with a price."}])
        status = fields.get("status")
        invoice_id = invoices.insert_invoice(self.session.connection, customer["id"], id_generator(), line_items, checked.cleaned["due_date"], subtotal, tax, total, status)
        raw = invoices.raw_invoice(self.session.connection, invoice_id)
        try:
            entries = invoice_lifecycle.post_invoice(self.session.connection, self.session.ledger_name, raw, deposit_account=checked.cleaned.get("deposit_account"))
        except invoice_lifecycle.InvoiceError as error:
            return _failure(f"The invoice was saved but its ledger entries failed: {error}", id=invoice_id)
        pdf_message, pdf_path = self._render_invoice_pdf(invoice_id)
        self._log(f"Invoice {invoice_id} created ({status}); ledger entries {', '.join(str(e) for e in entries)}. {pdf_message}")
        return _success(f"Invoice {invoice_id} created. {pdf_message}".strip(), id=invoice_id, pdf=pdf_path, ledger_entries=entries)

    def _render_invoice_pdf(self, invoice_id):
        view = invoices.get_invoice(self.session.connection, invoice_id)
        customer = records.get_customer(self.session.connection, view["customer_id"]) or {}
        try:
            path = invoices.render_pdf(view, customer, self.properties, self.properties.get("receipts_location", ""), self.layout.fonts)
        except invoices.InvoiceError as error:
            return f"PDF not written: {error}", ""
        invoices.set_location(self.session.connection, invoice_id, path)
        return f"PDF saved to {path}.", path

    @operation()
    @operation()
    def change_invoice_status(self, invoice_id, status, account=None):
        raw = invoices.raw_invoice(self.session.connection, invoice_id)
        if not raw:
            return _failure(f"Invoice {invoice_id} was not found.")
        result = invoice_lifecycle.change_status(self.session.connection, self.session.ledger_name, raw, status, account=account or None)
        if not result["ok"]:
            return _failure(result["message"])
        pdf_message, pdf_path = self._render_invoice_pdf(invoice_id)
        self._log(f"{result['message']} {pdf_message}")
        return _success(f"{result['message']} {pdf_message}", id=int(invoice_id), pdf=pdf_path, status=result["status"])

    @operation()
    def invoice_pdf_path(self, invoice_id):
        """The invoice's PDF, regenerated if it is missing from disk."""
        view = invoices.get_invoice(self.session.connection, invoice_id)
        if not view:
            return _failure(f"Invoice {invoice_id} was not found.")
        if view["location"] and os.path.isfile(view["location"]):
            return _success(path=view["location"])
        message, path = self._render_invoice_pdf(invoice_id)
        return _success(path=path) if path else _failure(message)

    # ------------------------------------------------------ reconciliation

    @operation()
    @operation()
    def reconcile_start(self, account_id, statement_date, statement_balance):
        checked = validation.validate_reconciliation_inputs(statement_date, statement_balance)
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked))
        if not records.get_account(self.session.connection, account_id):
            return _failure("Select an account to reconcile.", [{"field": "account", "message": "Select an account."}])
        session = reconciliation.start(self.session.connection, self.session.ledger_name, account_id, checked.cleaned["statement_date"])
        self.session.reconcile_session = session
        self.session.reconcile_statement_balance = checked.cleaned["statement_balance"]
        return self.reconcile_summary([])

    @operation()
    def reconcile_summary(self, cleared_ids):
        cleared_ids = cleared_ids or []
        session = self.session.reconcile_session
        if not session:
            return _failure("Load the statement first.")
        summary = reconciliation.summarize(session, cleared_ids, self.session.reconcile_statement_balance)
        summary = dict(summary, cleared=[dict(v) for v in summary["cleared"]], unmatched=[dict(v) for v in summary["unmatched"]])
        return _success(session={"account_id": session["account_id"], "statement_date": session["statement_date"], "reconciled_count": session["reconciled_count"],
                                 "later_reconciled": len(session["later_reconciled"])},
                        candidates=[dict(v) for v in session["candidates"]], summary=summary, cleared_ids=[int(i) for i in cleared_ids])

    @operation()
    def reconcile_finish(self, cleared_ids):
        cleared_ids = cleared_ids or []
        session = self.session.reconcile_session
        if not session:
            return _failure("Load the statement first.")
        try:
            summary = reconciliation.complete(self.session.connection, self.session.ledger_name, session, cleared_ids, self.session.reconcile_statement_balance)
        except reconciliation.ReconciliationError as error:
            return _failure(str(error))
        self._log(f"Reconciled account {session['account_id']} through {session['statement_date']}: {summary['cleared_count']} transactions cleared.")
        self.session.reconcile_session = None
        saved = self.save("Save after reconciliation")
        return _success(f"Reconciled {session['account_id']} through {session['statement_date']}: {summary['cleared_count']} transactions cleared." + ("" if saved["ok"] else f" {saved['message']}"),
                        cleared_count=summary["cleared_count"])

    @operation()
    def reconcile_history(self, account_id=None):
        rows = reconciliation.history(self.session.connection, account_id or None)
        return _success(history=[{"id": r["Reconciliation_ID"], "account_id": r["Account_ID"], "statement_date": r["Statement_Date"],
                                  "statement_balance": int(r["Statement_Balance"]), "cleared_count": int(r["Cleared_Count"]),
                                  "recorded": iceberg_time.display_timestamp(r["Created_Time"], seconds=False)} for r in rows])

    @operation()
    @operation()
    def reconcile_undo(self, account_id):
        try:
            record = reconciliation.undo_last(self.session.connection, self.session.ledger_name, account_id)
        except reconciliation.ReconciliationError as error:
            return _failure(str(error))
        self._log(f"Undid reconciliation of {account_id} for statement {record['Statement_Date']}.")
        self.session.reconcile_session = None
        return _success(f"Undid the reconciliation for statement {record['Statement_Date']}.")

    # ---------------------------------------------------------- properties

    @operation()
    @operation()
    def update_properties(self, fields):
        fields = fields or {}
        checked = validation.validate_database_properties(fields, new_database=False)
        if not checked.ok:
            return _failure("Please fix the highlighted fields.", _errors(checked))
        stamp = iceberg_time.storage_timestamp()
        values = {k: fields.get(k, "") for k in books.PROPERTY_NAMES if k not in ("ledger_name",)}
        values["sales_tax"] = f"{checked.cleaned['sales_tax']}"
        for key, label in books.PROPERTY_NAMES.items():
            if key == "ledger_name":
                continue
            self.session.connection.execute("UPDATE tbl_Properties SET Property_Value = ?, Edited_Time = ? WHERE Property_Name = ?;", (str(values[key]), stamp, label))
        self.session.connection.commit()
        self.properties = books.read_properties(self.session.connection)
        self._log("Database properties updated.")
        return _success("Database properties saved.", properties=self.properties)

    # ------------------------------------------------------------- backups

    @operation()
    def backups(self):
        db_path = os.path.join(self.folder, self.session.db_name)
        return _success(backups=[{"path": p, "label": backups.describe_backup(p), "name": os.path.basename(p), "size": os.path.getsize(p)} for p in backups.list_backups(db_path, backup_root=self.layout.backups)],
                        folder=backups.backup_directory(db_path, backup_root=self.layout.backups))

    @operation()
    @operation()
    def restore_backup(self, path):
        db_path = os.path.join(self.folder, self.session.db_name)
        key_path = os.path.join(self.session.save_location, self.session.filename)
        try:
            safety = backups.restore_backup(path, db_path, backup_root=self.layout.backups)
        except backups.BackupError as error:
            return _failure(str(error))
        self._log(f"Restored {self.session.db_name} from {path}; previous file kept as {safety}.")
        reopened = self.open_database(key_path)
        if not reopened["ok"]:
            return reopened
        return _success(f"Restored from {os.path.basename(path)}. The previous file was kept as a backup.", safety_copy=safety)

    # ------------------------------------------------------ import / export

    @operation()
    @operation()
    def export_ledger(self, path):
        if not path:
            return _failure("Choose where to save the file.")
        _, count = data_exchange.export_ledger(self.session.connection, self.session.ledger_name, self._accounts(), path)
        self._log(f"Exported {count} transactions to {path}.")
        return _success(f"Exported {count} transactions to {path}.", count=count, path=path)

    @operation()
    @operation()
    def export_all(self, folder):
        if not folder:
            return _failure("Choose a folder.")
        written = data_exchange.export_all(self.session.connection, self.session.ledger_name, self._accounts(), folder)
        summary = ", ".join(f"{name} ({count})" for name, (_, count) in written.items())
        self._log(f"Exported to {folder}: {summary}.")
        return _success(f"Exported {len(written)} files to {folder}.", files={name: {"path": p, "count": c} for name, (p, c) in written.items()})

    @operation()
    def export_report(self, path):
        report = getattr(self.session, "last_report", None)
        if not report:
            return _failure("Run a report first.")
        if not path:
            return _failure("Choose where to save the file.")
        data_exchange.export_report(report, path)
        self._log(f"Report exported to {path}.")
        return _success(f"Report exported to {path}.", path=path)

    @operation()
    @operation()
    def import_transactions(self, path, confirm=False):
        if not path:
            return _failure("Choose a CSV file.")
        ids = [str(a["Account_ID"]) for a in self._accounts()]
        existing = self._rows()
        try:
            result = data_exchange.import_transactions(self.session.connection, self.session.ledger_name, path, ids, existing_rows=existing, dry_run=not confirm)
        except data_exchange.ImportError_ as error:
            return _failure(str(error), problems=error.errors)
        if not confirm:
            return _success(f"{len(result['rows'])} transaction(s) are ready to import.", preview=len(result["rows"]), warnings=result["warnings"], needs_confirmation=True)
        self._log(f"Imported {result['imported']} transactions from {path}.")
        saved = self.save("Save after import")
        return _success(f"Imported {result['imported']} transactions." + ("" if saved["ok"] else f" {saved['message']}"), imported=result["imported"], transaction_ids=result["transaction_ids"])

    @operation(requires_database=False)
    def import_template(self, path):
        if not path:
            return _failure("Choose where to save the template.")
        data_exchange.write_import_template(path)
        return _success(f"Template written to {path}.", path=path)

    # --------------------------------------------------------- preferences

    def preferences(self):
        return _success(preferences=preferences.load(self.layout.preferences_dir), themes=list(preferences.THEMES),
                        text_scales=[{"value": s, "label": preferences.scale_label(s)} for s in preferences.TEXT_SCALES])

    def save_preferences(self, prefs):
        try:
            saved = preferences.save(prefs or {}, self.layout.preferences_dir)
        except OSError as error:
            return _failure(f"Preferences could not be saved: {error}")
        return _success("Preferences saved.", preferences=saved)

    def console(self):
        return _success(lines=self.session.current_console_messages[:200])

