"""Readable, sortable data tables (ST-017).

PySimpleGUI tables are ttk Treeviews.  With ``enable_click_events=True`` a
click produces the event ``(key, '+CLICKED+', (row, col))``; a header click
has ``row == -1``.  ``TableSorter`` keeps the rows shown in each table and
sorts them (and any parallel backing list) by the clicked column, toggling
direction on repeated clicks.  Values are compared as dates, money, numbers,
or text depending on what the column contains.
"""

import re

_MONEY = re.compile(r"^\(?-?\$?[\d,]*\.?\d+\)?$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")

SORT_INDICATOR = {False: " \u25b2", True: " \u25bc"}  # ascending / descending


def parse_click_event(event):
    """Return (key, row, col) for a table click event, else None."""
    if isinstance(event, tuple) and len(event) == 3 and event[1] == "+CLICKED+":
        position = event[2]
        if isinstance(position, tuple) and len(position) == 2:
            row, col = position
            if row is None or col is None:
                return None
            return event[0], row, col
    return None


def sort_key(value):
    """A key that orders dates, money, and numbers sensibly, text otherwise."""
    if value is None:
        return (0, 0.0, "")
    text = str(value).strip()
    if not text:
        return (0, 0.0, "")
    if _DATE.match(text):
        return (1, 0.0, text[:10])
    compact = text.replace(",", "").replace("$", "").replace(" ", "")
    if _MONEY.match(text) or _MONEY.match(compact):
        negative = compact.startswith("(") and compact.endswith(")")
        compact = compact.strip("()")
        try:
            number = float(compact)
            return (2, -number if negative else number, "")
        except ValueError:
            pass
    return (3, 0.0, text.casefold())


def sort_rows(rows, col, descending=False, backing=None):
    """Return (sorted_rows, sorted_backing) keeping both lists aligned."""
    order = sorted(range(len(rows)), key=lambda i: sort_key(rows[i][col] if col < len(rows[i]) else None), reverse=descending)
    sorted_rows = [rows[i] for i in order]
    sorted_backing = [backing[i] for i in order] if backing is not None else None
    return sorted_rows, sorted_backing


class TableSorter:
    """Tracks rows/backing/sort state per table key."""

    def __init__(self):
        self._state = {}

    def register(self, key, rows, backing=None, headings=None):
        """Record the rows currently displayed in ``key`` (resets sort state)."""
        self._state[key] = {"rows": rows, "backing": backing, "col": None, "descending": False, "headings": headings}

    def rows(self, key):
        state = self._state.get(key)
        return state["rows"] if state else []

    def backing(self, key):
        state = self._state.get(key)
        if not state:
            return []
        return state["backing"] if state["backing"] is not None else state["rows"]

    def sort(self, key, col):
        """Sort the table ``key`` by column ``col``; returns (rows, backing, descending)."""
        state = self._state.get(key)
        if not state or not state["rows"] or col >= len(state["rows"][0]):
            return None
        descending = not state["descending"] if state["col"] == col else False
        same_list = state["backing"] is None or state["backing"] is state["rows"]
        rows, backing = sort_rows(state["rows"], col, descending, None if same_list else state["backing"])
        # Sort in place so any list the application already holds stays aligned.
        state["rows"][:] = rows
        if not same_list:
            state["backing"][:] = backing
        state["col"], state["descending"] = col, descending
        return state["rows"], self.backing(key), descending

    def headings_with_indicator(self, key):
        state = self._state.get(key)
        if not state or not state["headings"]:
            return None
        headings = list(state["headings"])
        if state["col"] is not None and state["col"] < len(headings):
            headings[state["col"]] = headings[state["col"]] + SORT_INDICATOR[state["descending"]]
        return headings


def money_column_justification(headings, money_headings=("Amount", "Credits", "Debits", "Balance", "Total", "Price", "Subtotal", "Sales Tax")):
    """Right-align money columns, centre short codes, left-align text."""
    justification = []
    for heading in headings:
        clean = heading.strip()
        if clean in money_headings or clean.endswith("Balance"):
            justification.append("r")
        elif clean in ("Transaction", "Invoice", "Vendor", "Customer", "SKU", "Sku", "Date", "Status", "Taxable", "Ledger #", "ID", "Account", "Debit Account", "Credit Account", "Qty"):
            justification.append("c")
        else:
            justification.append("l")
    return justification


def table_kwargs(theme, headings):
    """Keyword arguments shared by every data table for a consistent look."""
    return {
        "headings": headings,
        "cols_justification": money_column_justification(headings),
        "row_height": theme.row_height,
        "font": theme.font("medium"),
        "header_font": theme.font("medium", bold=True),
        "alternating_row_color": theme.color("table_alt"),
        "background_color": theme.color("table_bg"),
        "text_color": theme.color("table_text"),
        "enable_events": True,
        "enable_click_events": True,
        "expand_x": True,
        "expand_y": True,
        "auto_size_columns": False,
        "justification": "left",
    }
