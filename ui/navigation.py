"""Persistent navigation (ST-015) and the tab registry (ST-012).

``TABS`` is the single list of workspace tabs in display order; the index in
this list is the tab index used throughout the application.  ``NAV_ITEMS``
are the buttons on the navigation bar; each maps to the existing menu event
so the bar and the menu always do the same thing.
"""

TABS = [
    ("-Dashboard_Tab-", "Dashboard"),
    ("-Ledger_Tab-", "View Ledger"),
    ("-Reports_Tab-", "Reports"),
    ("-Vendors_Tab-", "Vendors"),
    ("-Customers_Tab-", "Customers"),
    ("-Invoicing_Tab-", "Point of Sale"),
    ("-Inventory_Tab-", "Inventory"),
    ("-Owner_Equity_Tab-", "Owner Equity"),
    ("-View_Account_Tab-", "View Account"),
    ("-View_Properties_Tab-", "Database Properties"),
    ("-View_Services_Tab-", "Services"),
    ("-About_Tab-", "About"),
    ("-Reconcile_Tab-", "Reconcile"),
]
TAB_KEYS = [key for key, _ in TABS]
TAB_INDEX = {key: i for i, (key, _) in enumerate(TABS)}

# (label, event it triggers, tab index it shows, keyboard shortcut)
NAV_ITEMS = [
    ("Dashboard", "Go to Dashboard", 0, "Ctrl+1"),
    ("Ledger", "View Ledger", 1, "Ctrl+2"),
    ("Invoices", "Point of Sale", 5, "Ctrl+3"),
    ("Customers", "View Customers", 4, "Ctrl+4"),
    ("Vendors", "View Vendors", 3, "Ctrl+5"),
    ("Services", "View Services", 10, "Ctrl+6"),
    ("Reports", "Reports", 2, "Ctrl+7"),
    ("Reconcile", "Reconcile Account", 12, "Ctrl+8"),
]
NAV_KEY_PREFIX = "-Nav_"


def nav_key(label):
    return f"{NAV_KEY_PREFIX}{label}-"


def event_for_nav_key(key):
    """Translate a navigation button key into the menu event it stands for."""
    for label, event, _, _ in NAV_ITEMS:
        if key == nav_key(label):
            return event
    return key


def index_for_event(event):
    for _, item_event, index, _ in NAV_ITEMS:
        if event == item_event:
            return index
    return None


def active_item_for_tab(index):
    for label, _, tab_index, _ in NAV_ITEMS:
        if tab_index == index:
            return label
    return None


def build_nav_bar(sg, theme):
    """A row of navigation buttons plus a title area showing where you are."""
    buttons = []
    for label, _, _, shortcut in NAV_ITEMS:
        buttons.append(
            sg.Button(
                label,
                key=nav_key(label),
                font=theme.font("medium", bold=True),
                button_color=(theme.color("nav_inactive_text"), theme.color("nav_inactive")),
                disabled=True,
                pad=(theme.pad["xs"], theme.pad["sm"]),
                tooltip=f"{label} ({shortcut})",
                metadata=label,
            )
        )
    buttons.append(sg.Push())
    buttons.append(sg.Text("", key="-Nav_Location-", font=theme.font("medium", bold=True), justification="right"))
    return buttons


def set_enabled(window, enabled):
    for label, _, _, _ in NAV_ITEMS:
        window[nav_key(label)].update(disabled=not enabled)


def set_active(window, theme, index, location_text=None):
    """Highlight the nav button for ``index`` and show the location label."""
    active = active_item_for_tab(index)
    for label, _, _, _ in NAV_ITEMS:
        if label == active:
            colors = (theme.color("nav_active_text"), theme.color("nav_active"))
        else:
            colors = (theme.color("nav_inactive_text"), theme.color("nav_inactive"))
        window[nav_key(label)].update(button_color=colors)
    if location_text is None:
        location_text = TABS[index][1] if 0 <= index < len(TABS) else ""
    window["-Nav_Location-"].update(location_text)


def show_tab(window, theme, index):
    """Make one tab visible and selected, hide the rest, and sync the nav bar."""
    for i, key in enumerate(TAB_KEYS):
        if i == index:
            window[key].update(visible=True)
            window[key].select()
        else:
            window[key].update(visible=False)
    set_active(window, theme, index)
