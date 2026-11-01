"""Keyboard access and focus (ST-011).

``SHORTCUTS`` maps Tk key sequences to the menu events they trigger, so the
most common actions never require the mouse.  ``bind_shortcuts`` registers
them on the main window; PySimpleGUI then returns the event name from
``window.read()`` exactly as if the menu item had been chosen.  The list is
also rendered in the Help > Keyboard Shortcuts dialog and in the README, so
there is a single source of truth.
"""

SHORTCUTS = [
    # (tk sequence, event, human label, description)
    ("<Control-n>", "New Transaction", "Ctrl+N", "New transaction"),
    ("<Control-s>", "Save Database", "Ctrl+S", "Save database"),
    ("<Control-o>", "Open Database", "Ctrl+O", "Open database"),
    ("<Control-i>", "New Invoice", "Ctrl+I", "New invoice"),
    ("<Control-f>", "Focus Search", "Ctrl+F", "Jump to the search box on the current tab"),
    ("<Control-1>", "Go to Dashboard", "Ctrl+1", "Dashboard"),
    ("<Control-2>", "View Ledger", "Ctrl+2", "Ledger"),
    ("<Control-3>", "Point of Sale", "Ctrl+3", "Invoices"),
    ("<Control-4>", "View Customers", "Ctrl+4", "Customers"),
    ("<Control-5>", "View Vendors", "Ctrl+5", "Vendors"),
    ("<Control-6>", "View Services", "Ctrl+6", "Services"),
    ("<Control-7>", "Reports", "Ctrl+7", "Reports"),
    ("<Control-8>", "Reconcile Account", "Ctrl+8", "Reconcile"),
    ("<F1>", "Documentation", "F1", "Open the documentation"),
    ("<Control-comma>", "Preferences", "Ctrl+,", "Display preferences"),
]

# Search box to focus for each tab index (Ctrl+F).
SEARCH_FIELDS = {1: "-Ledger_Search_Input-", 3: "-Vendors_Search_Input-", 4: "-Customers_Search_Input-",
                 5: "-POS_Search_Input-", 10: "-Services_Search_Input-"}

# Accelerator-free events that must be ignored when no database is open.
NEEDS_DATABASE = {"New Transaction", "Save Database", "New Invoice", "Go to Dashboard", "View Ledger", "Point of Sale",
                  "View Customers", "View Vendors", "View Services", "Reports", "Reconcile Account", "Focus Search"}


def bind_shortcuts(window):
    """Register every shortcut on ``window``.  Returns the number bound."""
    count = 0
    for sequence, event, _, _ in SHORTCUTS:
        try:
            window.bind(sequence, event)
            count += 1
        except Exception:
            continue
    return count


def shortcut_table():
    """Rows of (keys, description) for display."""
    return [(label, description) for _, _, label, description in SHORTCUTS]


def shortcut_help_text():
    width = max(len(label) for _, _, label, _ in SHORTCUTS) + 2
    lines = ["Keyboard shortcuts", ""]
    for label, description in shortcut_table():
        lines.append(f"{label:<{width}}{description}")
    lines += ["", "Menus: press Alt plus the underlined letter.",
              "Forms: Tab moves between fields in reading order; Enter on the last field submits.",
              "Tables: click a column heading to sort; click again to reverse."]
    return "\n".join(lines)


def focus_first_input(window, key):
    """Put the keyboard focus on the first field of a form."""
    try:
        window[key].set_focus()
        return True
    except Exception:
        return False
