# Known bugs

This folder tracks confirmed defects and reproducible setup failures. Environment-specific reports should include the operating system, Python version, exact command, and complete error output.

## Open

None.

## Resolved

| Bug | Summary | Fixed in |
|-----|---------|----------|
| [BUG-001](BUG-001-startup-timezone.md) | Startup timer crashed with localized timezone names | 1.2 |
| [BUG-002](BUG-002-python314-dependencies.md) | Python 3.14 could not install pinned dependencies (recurred on the reporter's machine; pins updated) | 2.0 |
| [BUG-003](BUG-003-windows-tcl-tk.md) | Tcl/Tk runtime lookup failed in a Windows virtual environment | 1.2 |
| [BUG-004](BUG-004-ledger-tab-crash-without-customer.md) | Ledger tab crashed for transactions without a customer | 1.3 |
| [BUG-005](BUG-005-exit-without-saving.md) | Closing the window skipped saving the database | 1.2 |
| [BUG-006](BUG-006-wrong-timezone-name-in-records.md) | Timestamps stored with the wrong zone name and inconsistent formats | 1.2 |
| [BUG-007](BUG-007-stale-startup-time-on-invoices.md) | Invoice dates used the application start time | 1.2 |
| [BUG-008](BUG-008-open-database-cancel-crash.md) | Cancelling Open Database (or a wrong key) crashed the application | 1.2 |
| [BUG-009](BUG-009-invoice-zero-tax-ledger-entry.md) | Zero-tax invoices posted a failing ledger entry; paid check matched wrong invoices | 1.3 |
| [BUG-010](BUG-010-new-database-sales-tax-crash.md) | New Database crashed on a non-numeric sales tax and left a partial file | 1.3 |
| [BUG-011](BUG-011-business-name-special-characters.md) | Business names with punctuation produced an invalid ledger table name | 2.0 |

BUG-001 and BUG-003 concerned the retired Tk interface (timer and Tcl/Tk lookup); the new interface has neither component. BUG-002 was reproduced on the reporter's machine and fixed by updating the dependency pins.
