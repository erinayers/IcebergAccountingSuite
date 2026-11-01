"""Invoices: totals, storage, and the printable PDF.

Line items are stored in ``tbl_Invoices.Line_Items`` as a JSON list of
``[sku, description, price_display, quantity, total_display]`` - the same
shape earlier versions wrote with ``str(list)``, so old invoices still load.
"""

import ast
import json
import os
from decimal import Decimal

import iceberg_time
import invoice_lifecycle
import records
from iceberg_utils import format_currency

MAX_LINE_ITEMS = 10
PAGE_SIZE = (2550, 3300)  # US letter at 300 dpi


class InvoiceError(Exception):
    pass


# ------------------------------------------------------------------ totals


def parse_line_items(text):
    if not text:
        return []
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        try:
            return ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return []


def build_line_item(service, quantity):
    """``service`` is a records.service_view dict; quantity a Decimal."""
    quantity = Decimal(str(quantity))
    total = int((quantity * service["price"]).to_integral_value())
    return [service["sku"], service["description"], format_currency(service["price"]), f"{quantity.normalize():f}", format_currency(total)]


def line_total_cents(item):
    return int((Decimal(str(item[4]).replace("$", "").replace(",", "").strip("()")) * 100).to_integral_value())


def totals(line_items, tax_rate, taxable_by_sku):
    """Return (subtotal, tax, total) in cents.  ``tax_rate`` is a fraction."""
    subtotal = tax = 0
    rate = Decimal(str(tax_rate or 0))
    for item in line_items:
        cents = line_total_cents(item)
        subtotal += cents
        if taxable_by_sku.get(str(item[0])):
            tax += int((Decimal(cents) * rate).to_integral_value())
    return subtotal, tax, subtotal + tax


# ----------------------------------------------------------------- storage


def invoice_view(row, customer=None, names=None):
    items = parse_line_items(row.get("Line_Items"))
    view = {
        "id": int(row["Invoice_ID"]), "customer_id": str(row["Customer_ID"]), "tracking_code": row.get("Tracking_Code") or "",
        "line_items": items, "due_date": str(row.get("Due_Date") or "")[:10], "subtotal": int(row.get("Subtotal") or 0),
        "sales_tax": int(row.get("Sales_Tax") or 0), "total": int(row.get("Total") or 0), "status": row.get("Status") or "",
        "location": row.get("Location") or "", "created": iceberg_time.display_timestamp(row.get("Created_Time"), seconds=False),
        "created_date": iceberg_time.local_date_from_timestamp(row.get("Created_Time")),
        "edited": iceberg_time.display_timestamp(row.get("Edited_Time"), seconds=False),
        "allowed_transitions": sorted(invoice_lifecycle.allowed_transitions(row.get("Status") or "")),
    }
    if customer:
        view["customer_name"] = customer["display_name"]
        view["customer_contact"] = customer["contact"]
        view["customer_phone"] = customer["phone"]
        view["customer_email"] = customer["email"]
    else:
        view["customer_name"] = view["customer_contact"] = view["customer_phone"] = view["customer_email"] = ""
    return view


def list_invoices(connection, search=""):
    like = f"%{(search or '').strip()}%"
    rows = records._rows(
        connection,
        "SELECT i.* FROM tbl_Invoices i LEFT JOIN tbl_Customers c ON c.Customer_ID = i.Customer_ID WHERE i.Invoice_ID LIKE ? OR i.Status LIKE ? "
        "OR i.Tracking_Code LIKE ? OR c.Customer_Company_Name LIKE ? OR c.Customer_First_Name LIKE ? OR c.Customer_Last_Name LIKE ? OR c.Customer_Email LIKE ? "
        "ORDER BY i.Invoice_ID DESC;", (like,) * 7)
    customers = {c["id"]: c for c in records.list_customers(connection)}
    return [invoice_view(r, customers.get(str(r["Customer_ID"]))) for r in rows]


def get_invoice(connection, invoice_id):
    row = records._one(connection, "SELECT * FROM tbl_Invoices WHERE Invoice_ID = ?;", (int(invoice_id),))
    if not row:
        return None
    return invoice_view(row, records.get_customer(connection, row["Customer_ID"]))


def raw_invoice(connection, invoice_id):
    return records._one(connection, "SELECT * FROM tbl_Invoices WHERE Invoice_ID = ?;", (int(invoice_id),))


def next_invoice_id(connection):
    row = records._one(connection, "SELECT MAX(Invoice_ID) AS last FROM tbl_Invoices;")
    return (int(row["last"]) + 1) if row and row["last"] else 10001


def insert_invoice(connection, customer_id, tracking_code, line_items, due_date, subtotal, tax, total, status, location=""):
    stamp = iceberg_time.storage_timestamp()
    invoice_id = next_invoice_id(connection)
    connection.execute(
        "INSERT INTO tbl_Invoices (Invoice_ID, Customer_ID, Tracking_Code, Line_Items, Due_Date, Created_Time, Edited_Time, Subtotal, Sales_Tax, Total, Status, Payment_Method, Location) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);",
        (invoice_id, int(customer_id), tracking_code, json.dumps(line_items), due_date, stamp, stamp, int(subtotal), int(tax), int(total), status, "", location))
    connection.commit()
    return invoice_id


def set_location(connection, invoice_id, location):
    connection.execute("UPDATE tbl_Invoices SET Location = ? WHERE Invoice_ID = ?;", (location, int(invoice_id)))
    connection.commit()


# --------------------------------------------------------------------- pdf


def render_pdf(invoice, customer, business, receipts_folder, fonts_folder="fonts", date=None):
    """Draw the invoice and write ``<receipts>/Invoices/<id>/<id>.pdf``.

    ``invoice`` is an ``invoice_view`` dict, ``customer`` a customer view,
    ``business`` the properties dict.  Returns the PDF path.  Raises
    ``InvoiceError`` with a readable message when the folder or fonts are
    unavailable; the caller decides whether that is fatal.
    """
    try:
        import img2pdf
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:
        raise InvoiceError(f"PDF support is not installed ({error}).")
    if not receipts_folder or not os.path.isdir(receipts_folder):
        raise InvoiceError(f"The receipts folder does not exist: {receipts_folder!r}. Set it under Database Properties.")
    font_path = os.path.join(fonts_folder, "LiberationSerif-Regular.ttf")
    if not os.path.isfile(font_path):
        raise InvoiceError(f"Invoice font not found: {font_path}")
    folder = os.path.join(receipts_folder, "Invoices", str(invoice["id"]))
    os.makedirs(folder, exist_ok=True)
    date = date or invoice.get("created_date") or iceberg_time.local_date_string()
    status_date = invoice["due_date"] if invoice["status"] in ("Due", "Overdue") else iceberg_time.local_date_string()

    small = ImageFont.truetype(font_path, 50)
    medium = ImageFont.truetype(font_path, 70)
    large = ImageFont.truetype(font_path, 100)
    canvas = Image.new("RGB", PAGE_SIZE, "white")
    draw = ImageDraw.Draw(canvas)
    org = business.get("business_name", "")
    draw.text((225, 225), f"INVOICE {invoice['id']}                                   {date}", "#000000", large)
    draw.text((225, 425), "Bill To:\n" + "\n".join(filter(None, [customer.get("company", ""), customer.get("contact", ""), customer.get("address", ""), customer.get("phone", ""), customer.get("email", "")])), "#000000", small)
    draw.text((1525, 425), "Remit To:\n" + "\n".join(filter(None, [org, business.get("owner_name", ""), business.get("address", ""), business.get("phone", ""), business.get("email", "")])), "#000000", small)
    draw.text((225, 925), "SKU       Description                        Price            Qty           Total", "#000000", medium)
    items = invoice["line_items"]
    for i, item in enumerate(items):
        y = 925 + (i + 1) * 120
        draw.text((225, y), str(item[0]), "#000000", medium)
        draw.text((500, y + 15), str(item[1])[:34], "#000000", small)
        draw.text((1250, y), str(item[2]), "#000000", medium)
        draw.text((1600, y), str(item[3]), "#000000", medium)
        draw.text((1900, y), str(item[4]), "#000000", medium)
    n = len(items)
    draw.text((1630, 925 + (n + 1) * 120), f"Subtotal: {format_currency(invoice['subtotal'])}", "#000000", medium)
    draw.text((1630, 925 + (n + 2) * 120), f"Tax:        {format_currency(invoice['sales_tax'])}", "#000000", medium)
    draw.text((1630, 925 + (n + 3) * 120), f"Total:      {format_currency(invoice['total'])}", "#000000", medium)
    draw.text((895, 2900), f"Status: {invoice['status']} {status_date}", "#000000", medium)
    draw.text((775, 3035), invoice["tracking_code"], "#000000", small)
    draw.text((1275 - len(org) * 25 / 2, 3100), org, "#000000", small)
    draw.text((1100, 3165), "Page 1 of 1", "#000000", small)

    png_path = os.path.join(folder, f"{invoice['id']}_0.png")
    canvas.save(png_path, "PNG")
    pdf_path = os.path.join(folder, f"{invoice['id']}.pdf")
    layout = img2pdf.get_fixed_dpi_layout_fun((300, 300))
    with open(pdf_path, "wb") as handle:
        handle.write(img2pdf.convert([png_path], layout_fun=layout))
    return pdf_path
