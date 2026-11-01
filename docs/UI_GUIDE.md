# Using the Interface

## Layout

- **Title bar** - product name and the local clock with its UTC offset.
- **Header** - the business name, the save state badge, **Tools**, **Save**, and
  **+ New Transaction**. The arrow at the left returns to *Your Databases*.
- **Navigation tabs** - Dashboard · Ledger · Invoices · Customers · Vendors · Services ·
  Reports · Reconcile. The active tab is underlined.
- **Workspace** - a list panel on the left and a details panel on the right; forms open
  in a dialog over the workspace.
- **Status line** - which database is open, the outcome of the last action (green for
  success, red for an error, amber for a warning), and the save state with the autosave
  countdown.

## Icons

The interface uses the project's icon set (`web/icons/`): a green check for success, a
red cross for errors and removals, an amber exclamation for warnings, circled arrows for
back/forward, play for *Run report*, a terminal for the console log, a screen for
databases, and a pencil-and-wrench for tools and properties. Every icon carries a text
label for screen readers.

## Keyboard

| Keys | Action |
|------|--------|
| Ctrl+1 … Ctrl+8 | Dashboard, Ledger, Invoices, Customers, Vendors, Services, Reports, Reconcile |
| Ctrl+N | New transaction |
| Ctrl+I | New invoice |
| Ctrl+S | Save |
| Ctrl+O | Open database |
| Ctrl+F | Search on the current screen |
| Ctrl+M | Tools menu |
| Ctrl+, | Preferences |
| Esc | Close a dialog |
| Enter | Submit the open form |
| Tab / Shift+Tab | Move between fields |

Every form opens with the first field focused. *Tools → Keyboard shortcuts* shows this
list inside the application.

## Tables

Click a column heading to sort (click again to reverse). Money is right-aligned;
negative amounts are shown in parentheses and red. Selecting a row loads it into the
details panel. Search boxes filter as you type.

## Forms and validation

Required fields are marked with a red asterisk. When you submit, each problem is shown
beneath the field it concerns and the field is outlined; the dialog stays open so you can
fix it. Some checks ask for confirmation rather than refusing (for example a transaction
that looks like a duplicate).

## Screens

| Screen | What it does |
|--------|--------------|
| Welcome / Your Databases | Create a database or open one with its filekey; cards list the databases in the Iceberg folder with their backup counts. |
| Dashboard | Stat tiles, balance check, chart of accounts with type/year filters; click an account for its register; *+ New account*. |
| Account register | Running balance per transaction; *Edit account*, *Reconcile*. |
| Ledger | Search and year filter, details panel, *Edit*, *+ New Transaction*. |
| Invoices | List with status pills; details with line items and history; change status (deposit/refund account when needed); *View PDF*; *+ New Invoice*. |
| Customers | List with balance due; details with the customer's invoices; *New*/*Edit*. |
| Vendors | List and details; *New*/*Edit*. |
| Services | List with price and taxability; *New*/*Edit*. |
| Reports | Report type, period preset or custom dates, *Run report*, *Export CSV*. |
| Reconcile | Statement date and balance, tick cleared transactions, live difference, *Finish*, *History*, *Undo last*. |
| Database properties (Tools) | Business details, receipts folder, sales tax. |

## Tools menu

Your databases · Database properties · Save now · Restore from backup · Export ledger to
CSV · Export all data to CSV · Import transactions from CSV · Save an import template ·
Preferences · Keyboard shortcuts · Console log · Documentation.

## Preferences

Appearance (Light, Dark, High contrast), text size (Smaller … Extra large), and compact
rows. Changes apply immediately and are stored in `preferences.json` next to the
application.

## Window size

The window opens at up to 1280×860, fitted to the screen, and can be resized or maximised;
panels and tables stretch with it. On a small screen choose *Compact rows* and *Smaller*
text.
