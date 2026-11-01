"""Parameterised CRUD for the supporting records: accounts, vendors,
customers, services (SKUs).  Returns plain dicts; no GUI imports.

The ``repository`` package built SQL with f-strings, which breaks on names
containing quotes.  Everything here uses ``?`` placeholders instead.
"""

import accounting
import iceberg_time

PHONE_TYPES = ["Mobile", "Home", "Office", "Work", "Other"]
ACCOUNT_TYPE_OPTIONS = [("10", "Assets"), ("11", "Expenses"), ("12", "Equity Withdrawals"),
                        ("13", "Liabilities"), ("14", "Owner Equity"), ("15", "Revenue")]


def _rows(connection, query, params=()):
    cursor = connection.execute(query, params)
    columns = [c[0] for c in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _one(connection, query, params=()):
    rows = _rows(connection, query, params)
    return rows[0] if rows else None


def _like(term):
    return f"%{(term or '').strip()}%"


# ------------------------------------------------------------------ accounts


def account_view(row):
    key = str(row["Account_ID"])
    return {
        "id": key, "name": row["Name"], "type": accounting.type_name(key), "type_prefix": key[:2],
        "notes": row.get("Notes") or "", "institution": row.get("Institution") or "",
        "bank_account_type": row.get("Ins_Account_Type") or "", "routing_number": row.get("Ins_Routing_Number") or "",
        "account_number": row.get("Ins_Account_Number") or "",
        "created": iceberg_time.display_timestamp(row.get("Created_Time"), seconds=False),
        "edited": iceberg_time.display_timestamp(row.get("Edited_Time"), seconds=False),
    }


def list_accounts(connection):
    return [account_view(r) for r in _rows(connection, "SELECT * FROM tbl_Accounts ORDER BY Account_ID;")]


def get_account(connection, account_id):
    row = _one(connection, "SELECT * FROM tbl_Accounts WHERE Account_ID = ?;", (int(account_id),))
    return account_view(row) if row else None


def next_account_id(connection, type_prefix):
    """Next free number in the type's block, e.g. 11019 for expenses."""
    prefix = str(type_prefix)[:2]
    row = _one(connection, "SELECT MAX(Account_ID) AS last FROM tbl_Accounts WHERE Account_ID >= ? AND Account_ID < ?;",
               (int(prefix + "000"), int(prefix + "999") + 1))
    if row and row["last"]:
        return int(row["last"]) + 1
    return int(prefix + "001")


def add_account(connection, type_prefix, name, notes="", institution="", bank_account_type="", routing_number="", account_number=""):
    stamp = iceberg_time.storage_timestamp()
    account_id = next_account_id(connection, type_prefix)
    connection.execute(
        "INSERT INTO tbl_Accounts (Account_ID, Name, Notes, Created_Time, Edited_Time, Institution, Ins_Account_Type, Ins_Routing_Number, Ins_Account_Number) VALUES (?,?,?,?,?,?,?,?,?);",
        (account_id, name, notes, stamp, stamp, institution, bank_account_type, routing_number, account_number))
    connection.commit()
    return account_id


def update_account(connection, account_id, name, notes="", institution="", bank_account_type="", routing_number="", account_number=""):
    connection.execute(
        "UPDATE tbl_Accounts SET Name = ?, Notes = ?, Edited_Time = ?, Institution = ?, Ins_Account_Type = ?, Ins_Routing_Number = ?, Ins_Account_Number = ? WHERE Account_ID = ?;",
        (name, notes, iceberg_time.storage_timestamp(), institution, bank_account_type, routing_number, account_number, int(account_id)))
    connection.commit()


# ------------------------------------------------------------------- vendors


def vendor_view(row):
    return {
        "id": str(row["Vendor_ID"]), "name": row["Business_Name"], "category": row.get("Merchant_Category") or "",
        "first_name": row.get("Contact_First_Name") or "", "last_name": row.get("Contact_Last_Name") or "",
        "preferred_name": row.get("Preferred_Name") or "", "phone": row.get("Phone_Number") or "",
        "phone_type": row.get("Phone_Number_Type") or "", "address": row.get("Business_Address") or "",
        "email": row.get("Business_Email") or "", "website": row.get("Business_Website") or "", "notes": row.get("Notes") or "",
        "created": iceberg_time.display_timestamp(row.get("Created_Time"), seconds=False),
        "edited": iceberg_time.display_timestamp(row.get("Edited_Time"), seconds=False),
    }


def list_vendors(connection, search=""):
    like = _like(search)
    return [vendor_view(r) for r in _rows(
        connection,
        "SELECT * FROM tbl_Vendors WHERE Business_Name LIKE ? OR Merchant_Category LIKE ? OR Contact_First_Name LIKE ? OR Contact_Last_Name LIKE ? "
        "OR Phone_Number LIKE ? OR Business_Email LIKE ? OR Business_Address LIKE ? OR Notes LIKE ? OR Vendor_ID LIKE ? ORDER BY Business_Name COLLATE NOCASE;",
        (like,) * 9)]


def get_vendor(connection, vendor_id):
    row = _one(connection, "SELECT * FROM tbl_Vendors WHERE Vendor_ID = ?;", (int(vendor_id),))
    return vendor_view(row) if row else None


def add_vendor(connection, fields):
    stamp = iceberg_time.storage_timestamp()
    row = _one(connection, "SELECT MAX(Vendor_ID) AS last FROM tbl_Vendors;")
    vendor_id = (int(row["last"]) + 1) if row and row["last"] is not None else 1
    connection.execute(
        "INSERT INTO tbl_Vendors (Vendor_ID, Business_Name, Merchant_Category, Contact_First_Name, Contact_Last_Name, Preferred_Name, Phone_Number, Phone_Number_Type, "
        "Created_Time, Edited_Time, Business_Address, Business_Email, Business_Website, Notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);",
        (vendor_id, fields.get("name", ""), fields.get("category", ""), fields.get("first_name", ""), fields.get("last_name", ""),
         fields.get("preferred_name", ""), fields.get("phone", ""), fields.get("phone_type", "Mobile"), stamp, stamp,
         fields.get("address", ""), fields.get("email", ""), fields.get("website", ""), fields.get("notes", "")))
    connection.commit()
    return vendor_id


def update_vendor(connection, vendor_id, fields):
    connection.execute(
        "UPDATE tbl_Vendors SET Business_Name = ?, Merchant_Category = ?, Contact_First_Name = ?, Contact_Last_Name = ?, Preferred_Name = ?, Phone_Number = ?, "
        "Phone_Number_Type = ?, Business_Address = ?, Business_Email = ?, Business_Website = ?, Notes = ?, Edited_Time = ? WHERE Vendor_ID = ?;",
        (fields.get("name", ""), fields.get("category", ""), fields.get("first_name", ""), fields.get("last_name", ""), fields.get("preferred_name", ""),
         fields.get("phone", ""), fields.get("phone_type", "Mobile"), fields.get("address", ""), fields.get("email", ""), fields.get("website", ""),
         fields.get("notes", ""), iceberg_time.storage_timestamp(), int(vendor_id)))
    connection.commit()


# ----------------------------------------------------------------- customers


def customer_view(row, balance=None):
    view = {
        "id": str(row["Customer_ID"]), "company": row.get("Customer_Company_Name") or "",
        "first_name": row.get("Customer_First_Name") or "", "last_name": row.get("Customer_Last_Name") or "",
        "preferred_name": row.get("Preferred_Name") or "", "phone": row.get("Customer_Phone_Number") or "",
        "phone_type": row.get("Customer_Phone_Number_Type") or "", "address": row.get("Customer_Address") or "",
        "email": row.get("Customer_Email") or "", "notes": row.get("Notes") or "",
        "retail_certificate": row.get("Customer_Retail_Certificate") or "",
        "created": iceberg_time.display_timestamp(row.get("Created_Time"), seconds=False),
        "edited": iceberg_time.display_timestamp(row.get("Edited_Time"), seconds=False),
    }
    view["display_name"] = view["company"] or f"{view['first_name']} {view['last_name']}".strip()
    view["contact"] = f"{view['first_name']} {view['last_name']}".strip()
    if balance is not None:
        view["balance"] = balance
    return view


def outstanding_balances(connection):
    """{customer_id: cents of Due/Overdue invoices}."""
    out = {}
    for row in _rows(connection, "SELECT Customer_ID, SUM(Total) AS due FROM tbl_Invoices WHERE Status IN ('Due','Overdue') GROUP BY Customer_ID;"):
        out[str(row["Customer_ID"])] = int(row["due"] or 0)
    return out


def list_customers(connection, search=""):
    like = _like(search)
    balances = outstanding_balances(connection)
    rows = _rows(
        connection,
        "SELECT * FROM tbl_Customers WHERE Customer_First_Name LIKE ? OR Customer_Last_Name LIKE ? OR Customer_Company_Name LIKE ? OR Preferred_Name LIKE ? "
        "OR Customer_Phone_Number LIKE ? OR Customer_Email LIKE ? OR Customer_Address LIKE ? OR Notes LIKE ? OR Customer_ID LIKE ? "
        "ORDER BY Customer_Company_Name COLLATE NOCASE, Customer_Last_Name COLLATE NOCASE;",
        (like,) * 9)
    return [customer_view(r, balances.get(str(r["Customer_ID"]), 0)) for r in rows]


def get_customer(connection, customer_id):
    if customer_id in (None, ""):
        return None
    row = _one(connection, "SELECT * FROM tbl_Customers WHERE Customer_ID = ?;", (int(customer_id),))
    return customer_view(row, outstanding_balances(connection).get(str(customer_id), 0)) if row else None


def add_customer(connection, fields):
    stamp = iceberg_time.storage_timestamp()
    row = _one(connection, "SELECT MAX(Customer_ID) AS last FROM tbl_Customers;")
    customer_id = (int(row["last"]) + 1) if row and row["last"] is not None else 1
    connection.execute(
        "INSERT INTO tbl_Customers (Customer_ID, Customer_First_Name, Customer_Last_Name, Customer_Company_Name, Customer_Retail_Certificate, Preferred_Name, "
        "Customer_Phone_Number, Customer_Phone_Number_Type, Created_Time, Edited_Time, Customer_Address, Customer_Email, Notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);",
        (customer_id, fields.get("first_name", ""), fields.get("last_name", ""), fields.get("company", ""), fields.get("retail_certificate", ""),
         fields.get("preferred_name", ""), fields.get("phone", ""), fields.get("phone_type", "Mobile"), stamp, stamp,
         fields.get("address", ""), fields.get("email", ""), fields.get("notes", "")))
    connection.commit()
    return customer_id


def update_customer(connection, customer_id, fields):
    connection.execute(
        "UPDATE tbl_Customers SET Customer_First_Name = ?, Customer_Last_Name = ?, Customer_Company_Name = ?, Customer_Retail_Certificate = ?, Preferred_Name = ?, "
        "Customer_Phone_Number = ?, Customer_Phone_Number_Type = ?, Customer_Address = ?, Customer_Email = ?, Notes = ?, Edited_Time = ? WHERE Customer_ID = ?;",
        (fields.get("first_name", ""), fields.get("last_name", ""), fields.get("company", ""), fields.get("retail_certificate", ""), fields.get("preferred_name", ""),
         fields.get("phone", ""), fields.get("phone_type", "Mobile"), fields.get("address", ""), fields.get("email", ""), fields.get("notes", ""),
         iceberg_time.storage_timestamp(), int(customer_id)))
    connection.commit()


# ------------------------------------------------------------------ services


def service_view(row):
    return {
        "sku": str(row["Sku"]), "description": row.get("Description") or "", "long_description": row.get("Long_Description") or "",
        "price": int(row.get("Price") or 0), "taxable": str(row.get("Taxable")) == "True",
        "created": iceberg_time.display_timestamp(row.get("Created_Time"), seconds=False),
        "edited": iceberg_time.display_timestamp(row.get("Edited_Time"), seconds=False),
    }


def list_services(connection, search=""):
    like = _like(search)
    return [service_view(r) for r in _rows(
        connection,
        "SELECT * FROM tbl_Skus WHERE (Sku LIKE ? OR Description LIKE ? OR Long_Description LIKE ?) AND Type = 'Service' ORDER BY Sku;",
        (like, like, like))]


def get_service(connection, sku):
    row = _one(connection, "SELECT * FROM tbl_Skus WHERE Sku = ?;", (str(sku),))
    return service_view(row) if row else None


def next_sku(connection):
    row = _one(connection, "SELECT MAX(CAST(Sku AS INTEGER)) AS last FROM tbl_Skus;")
    return str(int(row["last"]) + 1) if row and row["last"] else "10001"


def add_service(connection, description, price_cents, taxable, long_description=""):
    stamp = iceberg_time.storage_timestamp()
    sku = next_sku(connection)
    connection.execute(
        "INSERT INTO tbl_Skus (Sku, Created_Time, Edited_Time, Description, Long_Description, Price, Taxable, Inventory, Type) VALUES (?,?,?,?,?,?,?,?,?);",
        (sku, stamp, stamp, description, long_description, int(price_cents), "True" if taxable else "False", "False", "Service"))
    connection.commit()
    return sku


def update_service(connection, sku, description, price_cents, taxable, long_description=""):
    connection.execute(
        "UPDATE tbl_Skus SET Description = ?, Long_Description = ?, Price = ?, Taxable = ?, Edited_Time = ? WHERE Sku = ?;",
        (description, long_description, int(price_cents), "True" if taxable else "False", iceberg_time.storage_timestamp(), str(sku)))
    connection.commit()
