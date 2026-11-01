# Changelog

All notable changes to Iceberg Accounting Suite. The section for the current
version is published as the release notes by `scripts/build_release.py`.

## 2.0.0

### Upgrade notes
- First packaged release. Installed builds keep their files in a per-user data
  folder (`%LOCALAPPDATA%\Iceberg` on Windows, `~/.local/share/iceberg` on Linux);
  a source checkout keeps them next to the code as before. To move existing books
  into an installed build, copy the `.icb` into the data folder's `databases`
  folder (Tools > Where are my files) and keep the `.icbkey` where it is.
- Python 3.11–3.14 are supported; every dependency installs from prebuilt wheels.
- The classic Tk interface was retired; `python webapp.py` (or the installed
  program) is the only interface.

### Added
- New interface: native window hosting an HTML/CSS/JS front-end over a local JSON
  API, following the product wireframe (cards, status pills, inline validation).
- Invoices with line items, status history, and PDF output; customers, vendors,
  services; bank reconciliation; income statement, balance sheet, cash flow;
  CSV import/export; preferences (light/dark/high-contrast, text size).
- Atomic, verified saves with timestamped backups and in-app restore.
- Startup checks with plain-language fixes; keyboard shortcuts; icon set.

### Fixed
- BUG-001 to BUG-011 (see `bugs/README.md`), including the startup timer crash,
  the Python 3.14 dependency build failure, silent data loss on exit, wrong
  timezone names in records, and the New Database crash on a non-numeric sales tax.
