"""Entry-time validation for records (ST-009).

Each ``validate_*`` function returns a ``ValidationResult``.  ``errors`` block
the save; ``warnings`` (for example a probable duplicate transaction) are
shown to the user who may choose to continue.  The functions are pure so
they can be unit tested and reused by the CSV importer.
"""

import datetime
import os
import re
from decimal import Decimal, InvalidOperation

ACCOUNT_TYPES = {
    "0": "Assets",
    "1": "Expenses",
    "2": "Equity Withdrawals",
    "3": "Liabilities",
    "4": "Owner Equity",
    "5": "Revenue",
}
INVOICE_STATUSES = ("Due", "Overdue", "Paid", "Refunded", "Canceled")
MAX_LINE_ITEMS = 10
ACCOUNTS_RECEIVABLE = "10006"
MAX_AMOUNT_CENTS = 10**13  # $100 billion; anything larger is a typo

_ACCOUNT_ID = re.compile(r"^1[0-5]\d{3}$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationResult:
    def __init__(self, errors=None, warnings=None, cleaned=None):
        self.errors = list(errors or [])
        self.warnings = list(warnings or [])
        self.cleaned = dict(cleaned or {})
        self.fields = []  # field name for each error (None when not field specific)

    @property
    def ok(self):
        return not self.errors

    def add_error(self, text, field=None):
        self.errors.append(text)
        self.fields.append(field)

    def add_warning(self, text):
        self.warnings.append(text)

    def error_fields(self):
        """Names of the fields that have errors, in order, without duplicates."""
        seen = []
        for field in self.fields:
            if field and field not in seen:
                seen.append(field)
        return seen

    def message(self):
        lines = [f"- {e}" for e in self.errors]
        if self.warnings:
            lines += [f"- Warning: {w}" for w in self.warnings]
        return "\n".join(lines)

    def __repr__(self):
        return f"ValidationResult(ok={self.ok}, errors={self.errors!r}, warnings={self.warnings!r})"


# ---------------------------------------------------------------- primitives


def parse_amount(text, allow_zero=False):
    """Return cents for a money string, or raise ValueError with a user message.

    Accepts ``1234.5``, ``$1,234.50``, ``(12.00)`` / ``-12.00`` (negative).
    """
    raw = "" if text is None else str(text).strip()
    if not raw:
        raise ValueError("Amount is required.")
    negative = False
    if raw.startswith("(") and raw.endswith(")"):
        negative = True
        raw = raw[1:-1]
    raw = raw.replace("$", "").replace(",", "").strip()
    if raw.startswith("-"):
        negative = not negative
        raw = raw[1:]
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise ValueError(f"Amount '{text}' is not a number. Use digits with an optional decimal point, e.g. 125.00.")
    if value != value.quantize(Decimal("0.01")):
        raise ValueError(f"Amount '{text}' has more than two decimal places.")
    cents = int((value * 100).to_integral_value())
    if negative:
        cents = -cents
    if cents == 0 and not allow_zero:
        raise ValueError("Amount must be greater than zero.")
    if abs(cents) > MAX_AMOUNT_CENTS:
        raise ValueError(f"Amount '{text}' is unrealistically large; check for a typo.")
    return cents


def parse_date(text, field="Date"):
    """Return ``YYYY-MM-DD`` for a date string or raise ValueError.

    Accepts ISO ``2025-12-21``, US ``12/21/2025`` (or ``12/21/25``),
    ``2025/12/21`` and ``20251221``.  Anything else - including day-first
    dates - is rejected rather than guessed.  Years outside 1900-2100 are
    rejected as typos.
    """
    raw = "" if text is None else str(text).strip()
    if not raw:
        raise ValueError(f"{field} is required.")
    parsed = None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%m/%d/%y", "%Y%m%d"):
        try:
            parsed = datetime.datetime.strptime(raw, fmt).date()
            break
        except ValueError:
            continue
    if parsed is None:
        raise ValueError(f"{field} '{text}' is not a valid date. Use YYYY-MM-DD, e.g. 2025-12-21.")
    if not (1900 <= parsed.year <= 2100):
        raise ValueError(f"{field} '{text}' has an unlikely year ({parsed.year}).")
    return parsed.isoformat()


def parse_account_id(text, field="Account"):
    """Return the 5-digit account number from ``10002`` or ``10002 - Checking``."""
    raw = "" if text is None else str(text).strip()
    if not raw:
        raise ValueError(f"{field} is required.")
    candidate = raw.split()[0].split("-")[0].strip()
    if not _ACCOUNT_ID.match(candidate):
        raise ValueError(f"{field} '{text}' is not a valid account number (five digits, 10000-15999).")
    return candidate


def account_type_name(account_id):
    return ACCOUNT_TYPES.get(str(account_id)[1], "Unknown")


def _blank(value):
    return value is None or str(value).strip() == ""


def _normalize(value):
    return " ".join(str(value or "").split()).casefold()


# ---------------------------------------------------------------- records


def validate_transaction(fields, account_ids, existing=None):
    """Validate a journal transaction before it is written.

    ``fields`` keys: name, date, amount, debit_account, credit_account,
    notes (optional), vendor (optional).  ``account_ids`` is the set of valid
    account numbers (strings or ints).  ``existing`` is an optional iterable
    of ledger rows (dicts with Name, Transaction_Date, Amount, Debit_Acct,
    Credit_Acct) used to flag probable duplicates.

    On success ``result.cleaned`` holds name, date (ISO), amount (cents),
    debit_account, credit_account.
    """
    result = ValidationResult()
    valid_accounts = {str(a) for a in account_ids}

    name = str(fields.get("name") or "").strip()
    if not name:
        result.add_error("Transaction name is required.", "name")
    elif len(name) > 200:
        result.add_error("Transaction name is longer than 200 characters.", "name")

    date_iso = None
    try:
        date_iso = parse_date(fields.get("date"), "Transaction date")
    except ValueError as error:
        result.add_error(str(error), "date")

    cents = None
    try:
        cents = parse_amount(fields.get("amount"))
        if cents < 0:
            result.add_error("Amount must be positive; swap the debit and credit accounts instead of entering a negative number.", "amount")
    except ValueError as error:
        result.add_error(str(error), "amount")

    debit = credit = None
    try:
        debit = parse_account_id(fields.get("debit_account"), "Debit account")
        if debit not in valid_accounts:
            result.add_error(f"Debit account {debit} does not exist in the chart of accounts.", "debit_account")
    except ValueError as error:
        result.add_error(str(error), "debit_account")
    try:
        credit = parse_account_id(fields.get("credit_account"), "Credit account")
        if credit not in valid_accounts:
            result.add_error(f"Credit account {credit} does not exist in the chart of accounts.", "credit_account")
    except ValueError as error:
        result.add_error(str(error), "credit_account")
    if debit and credit and debit == credit:
        result.add_error("Debit and credit accounts must be different.", "credit_account")

    if date_iso and date_iso > (datetime.date.today() + datetime.timedelta(days=366)).isoformat():
        result.add_warning(f"Transaction date {date_iso} is more than a year in the future.")

    if result.ok and existing:
        for row in existing:
            if (
                _normalize(row.get("Name")) == _normalize(name)
                and str(row.get("Transaction_Date"))[:10] == date_iso
                and int(row.get("Amount") or 0) == cents
                and str(row.get("Debit_Acct")) == debit
                and str(row.get("Credit_Acct")) == credit
            ):
                result.add_warning(
                    f"A transaction with the same name, date, amount, and accounts already exists (Transaction {row.get('Transaction_ID')})."
                )
                break

    if result.ok:
        result.cleaned = {
            "name": name,
            "date": date_iso,
            "amount": cents,
            "debit_account": debit,
            "credit_account": credit,
            "notes": str(fields.get("notes") or ""),
            "vendor": str(fields.get("vendor") or ""),
        }
    return result


def validate_account(name, existing_names, account_type=None):
    result = ValidationResult()
    clean = str(name or "").strip()
    if not clean:
        result.add_error("Account name is required.", "name")
    elif _normalize(clean) in {_normalize(n) for n in existing_names}:
        result.add_error(f"An account named '{clean}' already exists.", "name")
    if account_type is not None and str(account_type)[:2] not in {"10", "11", "12", "13", "14", "15"}:
        result.add_error("Select an account type.", "type")
    if result.ok:
        result.cleaned = {"name": clean}
    return result


def validate_vendor(fields, existing_names):
    result = ValidationResult()
    name = str(fields.get("name") or "").strip()
    if not name:
        result.add_error("Vendor name is required.", "name")
    elif _normalize(name) in {_normalize(n) for n in existing_names}:
        result.add_error(f"A vendor named '{name}' already exists.", "name")
    email = str(fields.get("email") or "").strip()
    if email and not _EMAIL.match(email):
        result.add_error(f"Email '{email}' does not look like an email address.", "email")
    if result.ok:
        result.cleaned = {"name": name, "email": email}
    return result


def validate_customer(fields, existing_customers):
    """``existing_customers`` is an iterable of dicts with company/first/last names."""
    result = ValidationResult()
    company = str(fields.get("company") or "").strip()
    first = str(fields.get("first_name") or "").strip()
    last = str(fields.get("last_name") or "").strip()
    address = str(fields.get("address") or "").strip()
    email = str(fields.get("email") or "").strip()
    if not (company or first or last):
        result.add_error("Enter a company name or a contact first/last name.", "company")
    if not address:
        result.add_error("Customer address is required (it is printed on invoices).", "address")
    if email and not _EMAIL.match(email):
        result.add_error(f"Email '{email}' does not look like an email address.", "email")
    key = (_normalize(company), _normalize(first), _normalize(last))
    for customer in existing_customers or []:
        other = (
            _normalize(customer.get("Customer_Company_Name")),
            _normalize(customer.get("Customer_First_Name")),
            _normalize(customer.get("Customer_Last_Name")),
        )
        if other == key:
            result.add_error("A customer with the same company and contact name already exists.", "company")
            break
    if result.ok:
        result.cleaned = {"company": company, "first_name": first, "last_name": last, "address": address, "email": email}
    return result


def validate_service(fields, existing_descriptions):
    result = ValidationResult()
    description = str(fields.get("description") or "").strip()
    if not description:
        result.add_error("Service description is required.", "description")
    elif _normalize(description) in {_normalize(d) for d in existing_descriptions}:
        result.add_error(f"A service described as '{description}' already exists.", "description")
    price = None
    try:
        price = parse_amount(fields.get("price"), allow_zero=True)
        if price < 0:
            result.add_error("Price cannot be negative.", "price")
    except ValueError as error:
        result.add_error(str(error).replace("Amount", "Price"), "price")
    taxable = str(fields.get("taxable") or "").strip()
    if taxable not in ("True", "False", "Yes", "No"):
        result.add_error("Select whether the service is taxable.", "taxable")
    if result.ok:
        result.cleaned = {"description": description, "price": price, "taxable": taxable}
    return result


def validate_line_item(quantity, sku_selected=True):
    result = ValidationResult()
    if not sku_selected:
        result.add_error("Select a service from the search results before adding a line item.", "sku")
    raw = str(quantity or "").strip()
    if not raw:
        result.add_error("Quantity is required.", "quantity")
    else:
        try:
            value = Decimal(raw)
            if value <= 0:
                result.add_error("Quantity must be greater than zero.", "quantity")
            elif value > 100000:
                result.add_error("Quantity is unrealistically large; check for a typo.", "quantity")
            else:
                result.cleaned = {"quantity": value}
        except InvalidOperation:
            result.add_error(f"Quantity '{quantity}' is not a number.", "quantity")
    return result


def validate_invoice(fields, line_items, asset_account_ids=None):
    """``fields``: customer_id, status, due_date, deposit_account (required when Paid)."""
    result = ValidationResult()
    if _blank(fields.get("customer_id")):
        result.add_error("Select a customer from the search results.", "customer")
    status = str(fields.get("status") or "").strip()
    if status not in INVOICE_STATUSES:
        result.add_error("Select an invoice status.", "status")
    try:
        result.cleaned["due_date"] = parse_date(fields.get("due_date"), "Due date")
    except ValueError as error:
        result.add_error(str(error), "due_date")
    if not line_items:
        result.add_error("Add at least one line item.", "line_items")
    elif len(line_items) > MAX_LINE_ITEMS:
        result.add_error(f"An invoice can have at most {MAX_LINE_ITEMS} line items.", "line_items")
    deposit = fields.get("deposit_account")
    if status == "Paid":
        try:
            account = parse_account_id(deposit, "Deposit account")
            if asset_account_ids is not None and account not in {str(a) for a in asset_account_ids}:
                result.add_error("The deposit account must be an asset account.", "deposit_account")
            elif account == ACCOUNTS_RECEIVABLE:
                result.add_error("Select the account where the payment was deposited; Accounts Receivable is not a deposit account.", "deposit_account")
            result.cleaned["deposit_account"] = account
        except ValueError as error:
            result.add_error(str(error), "deposit_account")
    if not result.ok:
        result.cleaned = {}
    return result


def parse_percent(text, field="Sales tax"):
    """Return a Decimal *fraction* (6.25 -> Decimal('0.0625')) for a percentage string.

    Accepts ``6.25``, ``6.25%``, ``6,25`` is rejected.  Blank means zero.
    """
    raw = "" if text is None else str(text).strip().rstrip("%").strip()
    if not raw:
        return Decimal("0")
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise ValueError(f"{field} '{text}' is not a number. Enter the percentage, e.g. 6.25 (or 0 if you do not collect it).")
    if value < 0 or value > 100:
        raise ValueError(f"{field} must be between 0 and 100 percent.")
    return value / 100


def database_file_stem(business_name):
    """The .icb file name Iceberg derives from a business name.

    Only letters, digits, and underscores survive: the stem is also used as
    part of the ledger *table* name, so it must be a valid SQL identifier.
    """
    stem = re.sub(r"[^A-Za-z0-9_]", "_", str(business_name or "").strip())
    stem = re.sub(r"_+", "_", stem).strip("_")
    if stem and stem[0].isdigit():
        stem = "B_" + stem
    return stem


def validate_database_properties(fields, new_database=True, existing_file=None):
    """Validate the New Database / Database Properties form.

    ``fields``: business_name, address, sales_tax, receipts_location, and
    (for a new database) save_location.  ``cleaned`` holds ``sales_tax`` as a
    Decimal fraction and ``db_name`` (``<stem>.icb``).
    """
    result = ValidationResult()
    name = str(fields.get("business_name") or "").strip()
    if not name:
        result.add_error("Business name is required.", "business_name")
    else:
        stem = database_file_stem(name)
        if not stem:
            result.add_error("Business name must contain at least one letter or digit.", "business_name")
        elif new_database and existing_file and os.path.exists(existing_file):
            result.add_error(f"A database named {stem}.icb already exists in the Iceberg folder. Open it instead, or choose a different business name.", "business_name")
        result.cleaned["db_name"] = f"{stem}.icb"
    if _blank(fields.get("address")):
        result.add_error("Business address is required (it is printed on invoices).", "address")
    try:
        result.cleaned["sales_tax"] = parse_percent(fields.get("sales_tax"))
    except ValueError as error:
        result.add_error(str(error), "sales_tax")
    if new_database:
        save_location = str(fields.get("save_location") or "").strip()
        if not save_location:
            result.add_error("Choose a folder for the filekey (.icbkey).", "save_location")
        elif not os.path.isdir(save_location):
            result.add_error(f"The filekey folder does not exist: {save_location}", "save_location")
    receipts = str(fields.get("receipts_location") or "").strip()
    if not receipts:
        result.add_error("Choose a receipts repository folder.", "receipts_location")
    elif not os.path.isdir(receipts):
        result.add_error(f"The receipts folder does not exist: {receipts}", "receipts_location")
    if not result.ok:
        result.cleaned = {}
    return result


def validate_reconciliation_inputs(statement_date, statement_balance):
    result = ValidationResult()
    try:
        result.cleaned["statement_date"] = parse_date(statement_date, "Statement date")
    except ValueError as error:
        result.add_error(str(error), "statement_date")
    try:
        result.cleaned["statement_balance"] = parse_amount(statement_balance, allow_zero=True)
    except ValueError as error:
        result.add_error(str(error).replace("Amount", "Statement balance"), "statement_balance")
    if not result.ok:
        result.cleaned = {}
    return result
