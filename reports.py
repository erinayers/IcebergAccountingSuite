"""Standard financial reports (ST-007): income statement, balance sheet,
cash flow, and a month-by-month income statement.

Every report is a plain dict with ``title``, ``period``, ``sections`` (a list
of ``{"title", "lines": [(label, cents)], "total": cents}``) and ``summary``
(list of (label, cents)).  ``render_text`` turns a report into aligned text
for the screen and ``report_rows`` flattens it for CSV export.
"""

import calendar
import datetime

import accounting
from iceberg_utils import format_currency


# ----------------------------------------------------------------- periods


def period_bounds(preset, today=None):
    """Return (start, end) ISO dates for a preset name."""
    today = today or datetime.date.today()
    year, month = today.year, today.month
    if preset == "This Year":
        return f"{year}-01-01", f"{year}-12-31"
    if preset == "Last Year":
        return f"{year - 1}-01-01", f"{year - 1}-12-31"
    if preset == "This Month":
        return f"{year}-{month:02d}-01", f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"
    if preset == "Last Month":
        first = today.replace(day=1) - datetime.timedelta(days=1)
        return f"{first.year}-{first.month:02d}-01", f"{first.year}-{first.month:02d}-{first.day:02d}"
    if preset == "This Quarter":
        q_start = 3 * ((month - 1) // 3) + 1
        q_end = q_start + 2
        return f"{year}-{q_start:02d}-01", f"{year}-{q_end:02d}-{calendar.monthrange(year, q_end)[1]:02d}"
    if preset == "Last Quarter":
        q_start = 3 * ((month - 1) // 3) + 1
        first = datetime.date(year, q_start, 1) - datetime.timedelta(days=1)
        lq_start = 3 * ((first.month - 1) // 3) + 1
        lq_end = lq_start + 2
        return f"{first.year}-{lq_start:02d}-01", f"{first.year}-{lq_end:02d}-{calendar.monthrange(first.year, lq_end)[1]:02d}"
    if preset == "Year to Date":
        return f"{year}-01-01", today.isoformat()
    if preset == "All Time":
        return "1900-01-01", "2100-12-31"
    raise ValueError(f"Unknown period preset '{preset}'.")


WORKING_CAPITAL_ACCOUNTS = {"10005", "10006", "13002", "13003"}  # inventory, A/R, A/P, sales tax payable

PERIOD_PRESETS = ["This Year", "Year to Date", "Last Year", "This Quarter", "Last Quarter", "This Month", "Last Month", "All Time", "Custom"]
REPORT_TYPES = ["Income Statement", "Income Statement by Month", "Balance Sheet", "Cash Flow"]


def _rows_between(rows, start, end):
    return [r for r in rows if start <= str(r["Transaction_Date"])[:10] <= end]


def _accounts_of_type(accounts, digit):
    return sorted((a for a in accounts if accounting.type_digit(a["Account_ID"]) == digit), key=lambda a: str(a["Account_ID"]))


def _lines(accounts, totals, include_zero=False):
    lines = []
    for account in accounts:
        key = str(account["Account_ID"])
        value = totals.get(key, 0)
        if value or include_zero:
            lines.append((f"{key} {account['Name']}", value))
    return lines


# ------------------------------------------------------------------ reports


def income_statement(rows, accounts, start, end):
    period_rows = _rows_between(rows, start, end)
    ids = [str(a["Account_ID"]) for a in accounts]
    totals = accounting.balances(period_rows, ids)
    revenue = _accounts_of_type(accounts, "5")
    expenses = _accounts_of_type(accounts, "1")
    revenue_lines = _lines(revenue, totals)
    expense_lines = _lines(expenses, totals)
    total_revenue = sum(v for _, v in revenue_lines)
    total_expenses = sum(v for _, v in expense_lines)
    net = total_revenue - total_expenses
    return {
        "type": "Income Statement",
        "title": "Income Statement (Profit and Loss)",
        "period": f"{start} to {end}",
        "sections": [
            {"title": "Revenue", "lines": revenue_lines, "total": total_revenue, "total_label": "Total Revenue"},
            {"title": "Expenses", "lines": expense_lines, "total": total_expenses, "total_label": "Total Expenses"},
        ],
        "summary": [("Net Income" if net >= 0 else "Net Loss", net)],
        "transaction_count": len(period_rows),
    }


def income_statement_by_month(rows, accounts, start, end):
    """Columns per month; returns a table report with ``columns`` and ``table`` rows."""
    start_date = datetime.date.fromisoformat(start)
    end_date = datetime.date.fromisoformat(end)
    months = []
    cursor = start_date.replace(day=1)
    while cursor <= end_date:
        months.append((cursor.year, cursor.month))
        cursor = (cursor.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    revenue = _accounts_of_type(accounts, "5")
    expenses = _accounts_of_type(accounts, "1")
    ids = [str(a["Account_ID"]) for a in revenue + expenses]
    per_month = []
    for year, month in months:
        m_start = max(start, f"{year}-{month:02d}-01")
        m_end = min(end, f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}")
        per_month.append(accounting.balances(_rows_between(rows, m_start, m_end), ids))
    columns = ["Account"] + [f"{calendar.month_abbr[m]} {y}" for y, m in months] + ["Total"]

    def build(accounts_subset):
        table = []
        for account in accounts_subset:
            key = str(account["Account_ID"])
            values = [totals.get(key, 0) for totals in per_month]
            if any(values):
                table.append([f"{key} {account['Name']}"] + values + [sum(values)])
        return table

    revenue_table = build(revenue)
    expense_table = build(expenses)
    revenue_totals = [sum(r[i] for r in revenue_table) for i in range(1, len(columns))]
    expense_totals = [sum(r[i] for r in expense_table) for i in range(1, len(columns))]
    net = [r - e for r, e in zip(revenue_totals, expense_totals)]
    table = (
        [["REVENUE"] + [None] * (len(columns) - 1)]
        + revenue_table
        + [["Total Revenue"] + revenue_totals]
        + [["EXPENSES"] + [None] * (len(columns) - 1)]
        + expense_table
        + [["Total Expenses"] + expense_totals]
        + [["Net Income"] + net]
    )
    return {
        "type": "Income Statement by Month",
        "title": "Income Statement by Month",
        "period": f"{start} to {end}",
        "columns": columns,
        "table": table,
        "sections": [],
        "summary": [("Net Income for period", net[-1] if net else 0)],
    }


def balance_sheet(rows, accounts, as_of):
    through = _rows_between(rows, "0000-00-00", as_of)
    ids = [str(a["Account_ID"]) for a in accounts]
    totals = accounting.balances(through, ids)
    assets = _lines(_accounts_of_type(accounts, "0"), totals)
    liabilities = _lines(_accounts_of_type(accounts, "3"), totals)
    equity = _lines(_accounts_of_type(accounts, "4"), totals)
    withdrawals = sum(totals.get(str(a["Account_ID"]), 0) for a in _accounts_of_type(accounts, "2"))
    revenue = sum(totals.get(str(a["Account_ID"]), 0) for a in _accounts_of_type(accounts, "5"))
    expenses = sum(totals.get(str(a["Account_ID"]), 0) for a in _accounts_of_type(accounts, "1"))
    retained = revenue - expenses - withdrawals
    total_assets = sum(v for _, v in assets)
    total_liabilities = sum(v for _, v in liabilities)
    owner_equity = sum(v for _, v in equity)
    total_equity = owner_equity + retained
    equity_lines = equity + [("Retained Earnings (revenue - expenses - withdrawals)", retained)]
    return {
        "type": "Balance Sheet",
        "title": "Balance Sheet",
        "period": f"as of {as_of}",
        "sections": [
            {"title": "Assets", "lines": assets, "total": total_assets, "total_label": "Total Assets"},
            {"title": "Liabilities", "lines": liabilities, "total": total_liabilities, "total_label": "Total Liabilities"},
            {"title": "Equity", "lines": equity_lines, "total": total_equity, "total_label": "Total Equity"},
        ],
        "summary": [
            ("Total Liabilities and Equity", total_liabilities + total_equity),
            ("Assets - (Liabilities + Equity)", total_assets - total_liabilities - total_equity),
        ],
        "balanced": total_assets == total_liabilities + total_equity,
    }


def is_cash_account(account):
    """Cash and bank accounts: the default checking/cash accounts plus any
    asset account with a bank named in its Institution field."""
    key = str(account["Account_ID"])
    if accounting.type_digit(key) != "0":
        return False
    if key in ("10002", "10004"):
        return True
    return bool(str(account.get("Institution") or "").strip())


def cash_flow(rows, accounts, start, end, cash_account_ids=None):
    """Direct-method cash flow: movements of cash accounts grouped by the
    type of the other account in each transaction."""
    if cash_account_ids is None:
        cash_ids = {str(a["Account_ID"]) for a in accounts if is_cash_account(a)}
    else:
        cash_ids = {str(a) for a in cash_account_ids}
    names = accounting.account_name_map(accounts)
    buckets = {"Operating": {}, "Investing": {}, "Financing": {}}
    bucket_for = {"1": "Operating", "5": "Operating", "3": "Financing", "4": "Financing", "2": "Financing", "0": "Investing"}
    transfers = 0

    def bucket_name(counter):
        # Receivables, payables, inventory, and sales tax are working capital:
        # collecting an invoice or paying a supplier is an operating cash flow.
        if counter in WORKING_CAPITAL_ACCOUNTS:
            return "Operating"
        return bucket_for[accounting.type_digit(counter)]
    for row in _rows_between(rows, start, end):
        debit, credit, amount = str(row["Debit_Acct"]), str(row["Credit_Acct"]), int(row["Amount"])
        if debit in cash_ids and credit in cash_ids:
            transfers += amount
            continue
        if debit in cash_ids:
            counter, change = credit, amount
        elif credit in cash_ids:
            counter, change = debit, -amount
        else:
            continue
        bucket = bucket_name(counter)
        label = f"{counter} {names.get(counter, '')}".strip()
        buckets[bucket][label] = buckets[bucket].get(label, 0) + change
    before = accounting.balances(_rows_between(rows, "0000-00-00", (datetime.date.fromisoformat(start) - datetime.timedelta(days=1)).isoformat()), cash_ids)
    beginning = sum(before.values())
    sections = []
    net = 0
    for title in ("Operating", "Investing", "Financing"):
        lines = sorted((label, value) for label, value in buckets[title].items() if value)
        total = sum(v for _, v in lines)
        net += total
        sections.append({"title": f"{title} Activities", "lines": lines, "total": total, "total_label": f"Net Cash from {title} Activities"})
    return {
        "type": "Cash Flow",
        "title": "Statement of Cash Flows",
        "period": f"{start} to {end}",
        "cash_accounts": sorted(cash_ids),
        "sections": sections,
        "summary": [
            ("Net Change in Cash", net),
            ("Cash at Beginning of Period", beginning),
            ("Cash at End of Period", beginning + net),
        ],
        "transfers_between_cash_accounts": transfers,
    }


def run(report_type, rows, accounts, start, end):
    if report_type == "Income Statement":
        return income_statement(rows, accounts, start, end)
    if report_type == "Income Statement by Month":
        return income_statement_by_month(rows, accounts, start, end)
    if report_type == "Balance Sheet":
        return balance_sheet(rows, accounts, end)
    if report_type == "Cash Flow":
        return cash_flow(rows, accounts, start, end)
    raise ValueError(f"Unknown report type '{report_type}'.")


# ---------------------------------------------------------------- rendering


def _money(cents):
    return format_currency(cents)


def render_text(report, width=78):
    lines = [report["title"].center(width).rstrip(), f"Period: {report['period']}".center(width).rstrip(), ""]
    if report.get("cash_accounts") is not None:
        lines.append(f"Cash accounts: {', '.join(report['cash_accounts']) or 'none'}")
        lines.append("")
    if "table" in report:
        columns = report["columns"]
        col_w = max(12, (width - 34) // max(1, len(columns) - 1))
        header = f"{columns[0]:<34}" + "".join(f"{c:>{col_w}}" for c in columns[1:])
        lines.append(header)
        lines.append("-" * len(header))
        for row in report["table"]:
            label = str(row[0])[:33]
            cells = "".join(f"{'' if v is None else _money(v):>{col_w}}" for v in row[1:])
            lines.append(f"{label:<34}{cells}")
        lines.append("")
    for section in report["sections"]:
        lines.append(section["title"].upper())
        if not section["lines"]:
            lines.append("    (no activity)")
        for label, value in section["lines"]:
            lines.append(f"    {label[:width - 22]:<{width - 20}}{_money(value):>16}")
        lines.append(f"  {section.get('total_label', 'Total'):<{width - 18}}{_money(section['total']):>16}")
        lines.append("")
    for label, value in report["summary"]:
        lines.append(f"{label:<{width - 16}}{_money(value):>16}")
    if report.get("balanced") is False:
        lines.append("")
        lines.append("WARNING: assets do not equal liabilities plus equity. Check for one-sided or edited transactions.")
    return "\n".join(lines)


def report_rows(report):
    """Flatten a report to CSV rows: (section, label, amount in dollars)."""
    rows = [["Report", report["title"], ""], ["Period", report["period"], ""]]
    if "table" in report:
        rows.append([""] + report["columns"])
        for row in report["table"]:
            rows.append([""] + [row[0]] + ["" if v is None else f"{v / 100:.2f}" for v in row[1:]])
        return rows
    for section in report["sections"]:
        for label, value in section["lines"]:
            rows.append([section["title"], label, f"{value / 100:.2f}"])
        rows.append([section["title"], section.get("total_label", "Total"), f"{section['total'] / 100:.2f}"])
    for label, value in report["summary"]:
        rows.append(["Summary", label, f"{value / 100:.2f}"])
    return rows
