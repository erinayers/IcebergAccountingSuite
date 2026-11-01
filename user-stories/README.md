# User stories and product roadmap

This folder tracks proposed product work for Iceberg Accounting Suite. Priorities are product-owner recommendations based on the current README, source layout, tests, and the Windows startup issues reported during setup. They are not commitments or release dates.

## Roadmap

### P0 — Make startup and data handling dependable

- **ST-001 — Supported installation:** As a new user, I want a documented, reproducible setup on supported Windows and Linux versions so I can install and launch the desktop app without guessing which Python version or system libraries are required.
- **ST-002 — Clear startup errors:** As a user, I want actionable messages when GUI dependencies, Tcl/Tk, or data files are unavailable so I can fix setup problems without interpreting a traceback.
- **ST-003 — Safe database saves:** As a business owner, I want saves to be atomic and report success or failure so an interrupted save does not silently leave my books incomplete.
- **ST-004 — Recoverable backups:** As a business owner, I want timestamped backups and a documented restore flow so I can recover accounting data after accidental edits or file damage.
- **ST-005 — Consistent time handling:** As a user in any timezone, I want timestamps and scheduled saves to work independently of localized timezone names and daylight-saving changes.

### P1 — Improve accounting confidence and daily workflows

- **ST-006 — Reconciliation:** As a bookkeeper, I want to reconcile an account against a statement and see unmatched transactions so I can confirm balances.
- **ST-007 — Financial reports:** As a small-business owner, I want standard income statement, balance sheet, and cash flow reports for a selected period so I can review business performance.
- **ST-008 — Invoice lifecycle clarity:** As a business owner, I want invoice status changes, payment recording, refunds, and their ledger entries shown as a clear history so I can audit what happened.
- **ST-009 — Data validation:** As a user, I want invalid dates, amounts, missing required fields, and duplicate records flagged before saving so errors are prevented at entry time.
- **ST-010 — Import and export:** As a bookkeeper, I want to export reports and back up or migrate records using documented formats so I can work with my accountant and move between machines.

### P2 — Maintainability and accessibility

- **ST-011 — Accessible interface:** As a keyboard or screen-reader user, I want predictable focus order, readable contrast, and keyboard access to common actions so I can use the app efficiently.
- **ST-012 — Modular application:** As a maintainer, I want UI, accounting rules, persistence, and startup code separated into focused modules so changes are easier to review and safer to test.
- **ST-013 — Automated release checks:** As a maintainer, I want supported Python/platform combinations checked in continuous integration so incompatible dependency changes are caught before release.

### P2 — Modernize the desktop interface

- **ST-014 — Consistent visual system:** As a user, I want consistent typography, spacing, colors, and controls across every screen so the app feels coherent and easier to learn.
- **ST-015 — Clear application navigation:** As a user, I want a persistent, clearly labeled way to move between Dashboard, Ledger, Invoices, Customers, Vendors, and Services so I can find common tasks without searching nested menus.
- **ST-016 — Responsive workspace:** As a user on a smaller screen or resized window, I want panels and tables to adapt to the available space so important information and actions remain visible.
- **ST-017 — Readable data tables:** As a bookkeeper, I want sortable, resizable tables with clearer column headings, row selection, and legible financial values so I can review records quickly.
- **ST-018 — Contextual action feedback:** As a user, I want clear success, error, loading, and unsaved-change feedback near the action I just performed so I know whether a transaction or edit was saved.
- **ST-019 — Focused data-entry forms:** As a user entering transactions or invoices, I want forms grouped into logical sections with visible required fields and inline validation so I can complete them with fewer mistakes.
- **ST-020 — Theme and display preferences:** As a user, I want to choose comfortable text scaling and light or dark appearance so the interface suits my display and working environment.

### P1 — Simplify building, packaging, and releasing

- **ST-021 — Repeatable build:** As a maintainer, I want a documented, one-command build process using pinned, supported dependencies so I can produce the same runnable application from a clean checkout.
- **ST-022 — Platform packages:** As a user, I want an installable package for each supported operating system so I can install and launch Iceberg without setting up Python or pip dependencies myself.
- **ST-023 — User data locations:** As a user installing a packaged build, I want databases, encryption keys, logs, and receipts stored in clearly documented user-selected or application data locations so upgrades do not overwrite or scatter my files.
- **ST-024 — Release artifacts:** As a maintainer, I want each release to include versioned installers or archives, checksums, and concise upgrade notes so users can identify and verify the right download.
- **ST-025 — Automated release pipeline:** As a maintainer, I want builds and packaging checks to run automatically for supported platforms when a version is released so release artifacts are complete and consistent.
- **ST-026 — Deployment and upgrade guide:** As a user or IT administrator, I want platform-specific install, first-run, upgrade, rollback, and uninstall instructions so I can manage the application over time.

### P1 — Build a marketing and distribution website

- **ST-027 — Product website:** As a prospective user, I want a clear website explaining Iceberg's purpose, features, intended audience, and limitations so I can decide whether it fits my needs.
- **ST-028 — Trusted downloads:** As a user, I want the website to offer versioned downloads with supported operating systems, release notes, and integrity checks so I can find and verify the right package.
- **ST-029 — Getting started and support:** As a new or existing user, I want setup guides, troubleshooting steps, and a clear way to report issues so I can get started and resolve common problems.
- **ST-030 — Project transparency:** As a prospective user, I want to review the license, privacy and data-storage practices, security guidance, and project status so I can understand how the software and my accounting data are handled.
- **ST-031 — Accessible, maintainable site:** As a visitor, I want the site to work on mobile and desktop with accessible navigation and readable content so I can use it on my preferred device.

### P3 — Advanced accounting workflows (proposed)

- **ST-032 — Inline custom chart-of-accounts creation:** As a bookkeeper, I want to create a new custom account directly from the New Transaction form and the vendor form (not only from the Dashboard's "+ New account"), so I can record a ledger entry or set up a vendor against an account that doesn't exist yet without losing my place or re-entering data.
- **ST-033 — Accounts payable / bills:** As a business owner, I want to track vendor bills (amount, due date, status, payment) the same way invoices track customer receivables, so my payables and receivables are both visible and I can see what I owe, not just what I'm owed.
- **ST-034 — Recurring transactions and invoices:** As a bookkeeper, I want to schedule recurring ledger entries and invoices (rent, subscriptions, retainers) to post automatically or with one click on their due date, so I don't have to re-enter the same transaction every period.
- **ST-035 — Bank statement import (OFX/QFX):** As a bookkeeper, I want to import a bank or card statement in OFX/QFX format, so reconciling a month of activity is faster than retyping a CSV and transactions match against existing ledger entries where possible.
- **ST-036 — Budgets and budget-vs-actual reporting:** As a business owner, I want to set a budget per account and period and see budget-vs-actual on reports, so I can track spending and revenue against plan.
- **ST-037 — Multi-currency accounts and transactions:** As a business owner who transacts in more than one currency, I want to record transactions in a foreign currency with an exchange rate captured at entry time, so my books reflect true cost and revenue in my home currency. (Largest story here; needs its own design pass before estimation.)

### P3 — Auditability and reporting depth (proposed)

- **ST-038 — Ledger and record change history with undo:** As a user, I want edits to ledger entries, accounts, vendors, and customers tracked with an old/new value history and an "undo last change" action (matching the pattern reconciliation already uses), so mistakes are visible and recoverable.
- **ST-039 — Vendor 1099-NEC summary export:** As a business owner, I want a year-end summary of payments to each vendor, so I can prepare 1099-NEC filings without re-tallying the ledger by hand.
- **ST-040 — Dashboard trend charts and AR/AP aging:** As a business owner, I want simple trend charts (revenue/expense over time) and an accounts-receivable (and, once ST-033 exists, accounts-payable) aging view on the dashboard, so I can spot trends and overdue balances at a glance instead of reading report tables.

### P4 — Platform hardening (proposed)

- **ST-041 — Parameterized reconciliation queries:** As a maintainer, I want `reconciliation.py`'s SQL to use parameters instead of string interpolation, consistent with the "SQL takes parameters, never f-strings" rule already followed in `records.py`/`invoices.py`/`books.py`, so the module can't be misused with unexpected input and the codebase has one consistent pattern.
- **ST-042 — Retire the legacy `repository/` package's unsafe write methods:** As a maintainer, I want the f-string-built `insert`/`update` methods in `repository/account.py`, `vendor.py`, `customer.py`, `invoice.py`, `owner.py`, `property.py`, and `sku.py` removed or rewritten with `?` placeholders. Live account/vendor/property writes already go through `records.py` or direct parameterized `connection.execute(...)` calls (confirmed in `api.py`), so these methods are currently dead code rather than an exploited path, but they remain callable footguns that contradict `docs/ARCHITECTURE.md`'s stated SQL rule and `records.py`'s own docstring, which already flags the `repository` package as unsafe on names containing quotes.
- **ST-043 — Multi-machine / cloud-sync safety guidance:** As a user who keeps a database folder in a cloud-synced location (Dropbox, OneDrive, Google Drive) and might open Iceberg from more than one machine, I want documented guidance (and ideally a lock file or open-elsewhere warning) so two machines can't silently save conflicting versions of the same encrypted `.icb`, since the current design assumes one machine with no cross-machine coordination.
- **ST-044 — Extension points for reports, invoice transitions, and shortcuts (optional):** As a maintainer, I want a documented, minimal checklist for registering a new report type, invoice transition, or shortcut without touching dispatch logic in multiple files. Lower priority and in tension with `docs/ARCHITECTURE.md`'s explicit "one registry per concept" simplicity rule — include only if the closed-registry pattern starts to cause real contributor friction.

## Suggested delivery order

1. Resolve BUG-001 and BUG-002; establish a supported Python and OS matrix (ST-001, ST-002, ST-005).
2. Make database saves observable and recoverable (ST-003, ST-004).
3. Add validation and accounting workflow coverage, beginning with reconciliation and invoice lifecycle history (ST-006, ST-008, ST-009).
4. Add reporting and data exchange improvements (ST-007, ST-010).
5. Establish a supported build process and user data layout, then package and document releases (ST-021–ST-024, ST-026).
6. Publish the product, support, transparency, and verified download information on the website (ST-027–ST-031), once release artifacts and support processes are ready.
7. Modernize navigation, layout, tables, and forms as a coherent UI update (ST-014–ST-020), with accessibility requirements included from the start (ST-011).
8. Improve modularity and automate compatibility and release checks (ST-012, ST-013, ST-025).
9. Start the next phase with low-risk, high-value workflow fixes: inline custom-account creation and the reconciliation/repository SQL cleanup (ST-032, ST-041, ST-042). Then extend core bookkeeping parity with bills/AP and recurring transactions (ST-033, ST-034). Add bank statement import and change history/undo once those are stable (ST-035, ST-038), followed by budgets, dashboard trend charts, and the 1099 summary (ST-036, ST-039, ST-040). Document multi-machine/cloud-sync safety whenever it's convenient (ST-043) — it's independent of the rest. Leave multi-currency (ST-037) for last — it is the largest and riskiest story and should get its own design review before scheduling. Treat extension points (ST-044) as optional; only take it on if the closed-registry pattern becomes a real contributor pain point.

## Story status

### P0 — Make startup and data handling dependable: implemented in version 1.2

| Story | Status | Acceptance criteria and where they are met |
|-------|--------|--------------------------------------------|
| ST-001 Supported installation | Implemented; Windows walkthrough awaiting verification on a clean machine | Supported Python (3.11–3.13) and OS matrix, step-by-step Windows and Linux instructions, file locations, and a troubleshooting table in `docs/SETUP.md`; README links to it; `requirements.txt` states the supported versions. |
| ST-002 Clear startup errors | Implemented | `startup_checks.py` runs before the GUI imports: interpreter version, Tcl/Tk (with automatic `TCL_LIBRARY`/`TK_LIBRARY` repair), PySimpleGUI, required packages, poppler, data files, and session-log consistency. Problems are printed and shown in a dialog with a plain-language fix; `python startup_checks.py` runs them standalone. Open Database failures (missing file, wrong key, damaged file) are reported in a dialog and the console. Tests: `tests/test_startup_checks.py`. |
| ST-003 Safe database saves | Implemented | `db_calls.save_encrypted_database()` writes to a temp file in the same folder, fsyncs, verifies by decrypting, then `os.replace()`s; it returns a `SaveResult` that is logged to the console (and therefore into `tbl_Console_Log`) and shown in a dialog on failure. Opening no longer writes plaintext to disk. Save on exit with a confirm-on-failure prompt. Tests: `tests/test_db_calls.py::TestSafeSaves`, `TestOpenDatabase`. |
| ST-004 Recoverable backups | Implemented | `backups.py` writes `backups/<db>/<db>_<UTC stamp>.icb` after every successful save and keeps the 20 newest. *File → Restore from Backup* lists backups in local time, keeps a safety copy, restores, and reopens. Manual restore flow documented in `docs/BACKUP_AND_RESTORE.md`. Tests: `tests/test_backups.py`. |
| ST-005 Consistent time handling | Implemented; BUG-001 awaiting Windows launch check | `iceberg_time.py`: all stored timestamps are UTC ISO 8601; display is local time with a numeric `UTC±hh:mm` offset (no localized names); legacy formats still parse; autosave and clock refresh use `time.monotonic()`. Tests: `tests/test_iceberg_time.py`, `tests/test_iceberg_utils.py`. |

### P1 — Improve accounting confidence and daily workflows: implemented in version 1.3

| Story | Status | Acceptance criteria and where they are met |
|-------|--------|--------------------------------------------|
| ST-006 Reconciliation | Implemented | `reconciliation.py` + Reconcile tab (Ledger → Reconcile Account, or View Account → Reconcile). Enter statement date and ending balance, click transactions to clear them, see cleared balance / difference / unmatched list live, finish only when balanced; cleared transactions get a `Reconciled_Date`, statements are stored in `tbl_Reconciliations`, with history and undo. Docs: `docs/RECONCILIATION.md`. Tests: `tests/test_reconciliation.py`. |
| ST-007 Financial reports | Implemented | `reports.py` + Reports tab: Income Statement, Income Statement by Month, Balance Sheet (with balance check), Cash Flow (direct method, working-capital accounts as operating) for presets or custom dates; CSV export. Docs: `docs/REPORTS.md`. Tests: `tests/test_reports.py`. |
| ST-008 Invoice lifecycle clarity | Implemented | `invoice_lifecycle.py` state machine owns every transition and its ledger entries; `tbl_Invoice_History` records event, from/to status, amount, account, and ledger IDs; the Point of Sale tab shows the timeline (legacy invoices derived from ledger entries by tracking code); invalid transitions are refused with an explanation. Tests: `tests/test_invoice_lifecycle.py`. |
| ST-009 Data validation | Implemented | `validation.py` checks transactions (incl. edits and imports), accounts, vendors, customers, services, invoice line items and invoices before saving: required fields, dates, amounts, account existence and distinctness, duplicate names/records, probable duplicate transactions (confirmation). Errors are shown in a dialog and the console; the form stays open. Tests: `tests/test_validation.py`. |
| ST-010 Import and export | Implemented | `data_exchange.py`: ledger export with account names, export of all tables, report export; CSV transaction import with header aliases, full validation, line-numbered errors, duplicate warnings, all-or-nothing write, automatic save/backup. Docs and sample file: `docs/IMPORT_EXPORT.md`, `docs/samples/`. Tests: `tests/test_data_exchange.py`. |

### P2 — Maintainability and accessibility / Modernize the desktop interface: implemented in version 1.4

| Story | Status | Acceptance criteria and where they are met |
|-------|--------|--------------------------------------------|
| ST-011 Accessible interface | Implemented; needs a screen-reader pass on a real desktop | `ui/accessibility.py`: 15 keyboard shortcuts bound on the main window (Ctrl+N/S/O/I/F, Ctrl+1-8, F1, Ctrl+,) with a Help > Keyboard Shortcuts dialog generated from the same list; every form focuses its first field and submits on Enter; all three palettes verified ≥ 4.5:1 WCAG AA contrast by `tests/test_ui.py::TestTheme`. |
| ST-012 Modular application | Implemented | Session state in `session.py`; presentation helpers in `ui/` (theme, preferences, navigation, tables, feedback, forms, accessibility); accounting rules, persistence, and startup already in their own modules; no accounting/persistence module imports the GUI toolkit. Map and rules in `docs/ARCHITECTURE.md`. `iceberg.py` keeps only layouts and the event loop. |
| ST-013 Automated release checks | Implemented | `scripts/check_release.py` (compile, pyflakes, data files/docs, tests, `pip check`, optional wheel availability) and `.github/workflows/ci.yml` running it on ubuntu + windows × Python 3.11/3.12/3.13 with wheels-only installs, plus an allowed-to-fail 3.14 probe. Tests: `tests/test_check_release.py`. |
| ST-014 Consistent visual system | Implemented | `ui/theme.py` defines palettes, a type scale (small/medium/large/xlarge), spacing, and row heights; every layout constant (`small_print`, panel colours, …) now derives from the active theme; tables share alternating rows, bold headers, right-aligned money. |
| ST-015 Clear application navigation | Implemented | Persistent navigation bar (`ui/navigation.py`) with active highlighting and a location label; one tab registry (`TABS`) replaces the 13 hand-written tab-switching loops; nav buttons map to the existing menu events. |
| ST-016 Responsive workspace | Implemented (structural); visual check on small screens pending | Window sized from the screen (95%/90%, never below 1024×720), resizable with a minimum size, expanding tab group/tables/status bar; *Compact rows* and text-size preferences for small displays. |
| ST-017 Readable data tables | Implemented | `ui/tables.py`: click-to-sort on every main table with value-aware keys (dates, money incl. parentheses, numbers) and ▲/▼ indicators; sorting keeps the side-panel selection mapping intact (backing lists sorted together); right-aligned money columns; alternating row colour; ttk column resizing. Tests: `TestTables`. |
| ST-018 Contextual action feedback | Implemented | `ui/feedback.py` status bar: ✓/✖/⚠/ℹ outcome of the last action (saves, records added, validation failures, sorts, imports) and a save-state label ("Unsaved changes · autosave in 3:41" / "All changes saved 14:52"). `IcebergSession` tracks unsaved bookkeeping changes via SQLite `total_changes`, excluding console writes; autosave skips when nothing changed. Tests: `TestFeedback`, `tests/test_session.py`. |
| ST-019 Focused data-entry forms | Implemented | `ui/forms.py`: New Transaction grouped into Details / Accounts / Notes / Receipt sections with required markers, legend, tooltips; validation errors shown inline above Submit with the offending fields highlighted (field-level errors from `validation.ValidationResult.error_fields()`); vendor, customer, service, account forms gained legends, inline messages, focus and Enter-to-submit. Tests: `TestForms`, `tests/test_validation.py`. |
| ST-020 Theme and display preferences | Implemented | `ui/preferences.py` + Help > Preferences dialog: Light / Dark / High contrast, five text sizes, compact rows; stored in `preferences.json` with validation and safe fallback; applied at next launch. Tests: `TestPreferences`. |

### Version 2.0 — the interface was rebuilt on web technology

The wireframe supplied for the modernization could not be reproduced in Tk, so the Tk
interface was retired and replaced by a native webview window (pywebview) hosting an
HTML/CSS/JS front-end over a JSON API (`api.py`) on the unchanged accounting core. Every
workspace is covered: Welcome/Databases, Create, Dashboard, Account register, Ledger and
transactions, Invoices (creation with line items, status changes with history, PDF),
Customers, Vendors, Services, Reports, Reconcile, Database properties, Restore from backup,
CSV import/export, Preferences (live), keyboard shortcuts, console log. ST-011 and
ST-014–ST-020 are therefore delivered on that stack (`docs/UI_GUIDE.md`,
`docs/WEB_INTERFACE.md`, `docs/screens/`). Verification on a real Windows/Linux desktop
remains the next step; the view layer and API are covered by automated tests and
headless screenshots.

### P1 — Simplify building, packaging, and releasing: implemented in version 2.0

| Story | Status | Acceptance criteria and where they are met |
|-------|--------|--------------------------------------------|
| ST-021 Repeatable build | Implemented | `./compile.s` / `.\build.ps1` → `scripts/build_release.py`: venv, pinned wheels, PyInstaller spec (`packaging/iceberg.spec`), self-verification of the built program (`--version`, `--check`). Verified by building on Linux and exercising the frozen binary's server. |
| ST-022 Platform packages | Implemented; Windows installer build needs a Windows run | Windows: Inno Setup installer (`packaging/windows/iceberg.iss`) + portable zip; Linux: tar.gz with `install.sh`/`uninstall.sh` and a desktop entry. macOS: from source only (documented). |
| ST-023 User data locations | Implemented | `paths.py`: per-user data folder for installed builds, portable mode for source checkouts or a `portable.txt` marker, `--data-dir`/`ICEBERG_DATA_DIR` override; databases/backups/logs/preferences laid out and documented; *Tools → Where are my files*. Tests: `tests/test_paths.py`. |
| ST-024 Release artifacts | Implemented | Versioned archives/installer, `SHA256SUMS-<platform>.txt`, `RELEASE_NOTES.md` from `CHANGELOG.md`, `version.py` as the single version source (checked by `tests/test_build_release.py`). |
| ST-025 Automated release pipeline | Implemented; first run happens on the first tag | `.github/workflows/release.yml`: on `v*` tags builds on Windows + Linux (wheels-only installs, tag/version agreement check, release checks, build, verify, package), then publishes the GitHub release with artifacts, combined checksums, and notes. |
| ST-026 Deployment and upgrade guide | Implemented | `docs/DEPLOYMENT.md`: data locations, download verification, per-platform install/first run/upgrade/rollback/uninstall, managed deployments, silent install, self-check. |

### P1 — Build a marketing and distribution website: implemented in version 2.0

| Story | Status | Acceptance criteria and where they are met |
|-------|--------|--------------------------------------------|
| ST-027 Product website | Implemented | `site/pages/index.html`: purpose, features, intended audience, explicit limitations, screenshots. |
| ST-028 Trusted downloads | Implemented | `downloads.html` generated from `site/releases.json`: versions, OS/type per file, SHA-256, release-notes links, verification commands, supported-systems table; `scripts/publish_release_info.py` fills checksums from the build output. |
| ST-029 Getting started and support | Implemented | `getting-started.html`: install per platform, first database, file locations, troubleshooting table, how to report an issue (with what to include and what not to attach). |
| ST-030 Project transparency | Implemented | `about.html`: MIT license, privacy & data storage (local only, encryption details, what is not encrypted, loopback interface), security guidance, project status and roadmap. |
| ST-031 Accessible, maintainable site | Implemented | One layout + page fragments built by `site/build.py`; skip link, labelled nav with `aria-current`, single h1, alt text, focus styles, reduced-motion, mobile breakpoint; `--check` validates structure/links; `tests/test_site.py`; deployed by `.github/workflows/site.yml`. |

Every story in the roadmap through ST-031 (version 2.0) has been implemented. ST-032 onward below are newly proposed and not yet started; add acceptance criteria, estimates, and release targets as each is scheduled.

### P3/P4 — Advanced accounting workflows, auditability, and platform hardening: proposed, not started

| Story | Status | Notes |
|-------|--------|-------|
| ST-032 Inline custom chart-of-accounts creation | Proposed | Add an "add new account" option to the account pickers on the New Transaction and vendor forms, reusing `records.add_account`/`validation.validate_account` instead of duplicating them, so the behavior stays identical to the Dashboard's "+ New account". |
| ST-033 Accounts payable / bills | Proposed | Mirrors `invoice_lifecycle.py`/`invoices.py` for vendor bills: a status machine (Due/Overdue/Paid/Canceled), ledger postings against Accounts Payable (13002), and a bills list parallel to the Invoices tab. |
| ST-034 Recurring transactions and invoices | Proposed | A schedule (frequency, next-due date, template) stored alongside existing ledger/invoice records; surfaced on the dashboard as due-today items; posting reuses the existing transaction/invoice creation paths. |
| ST-035 Bank statement import (OFX/QFX) | Proposed | Extends `data_exchange.py`'s importer with an OFX/QFX parser feeding the same validation path as CSV import, then into the existing `reconciliation.py` candidate list. |
| ST-036 Budgets and budget-vs-actual reporting | Proposed | A budget table (account, period, amount) and a new report type alongside the existing `reports.REPORT_TYPES`. |
| ST-037 Multi-currency accounts and transactions | Proposed | Largest and riskiest story: touches `accounting.py`, `iceberg_utils.py` formatting, ledger schema, and every report; needs its own design review before estimation. |
| ST-038 Ledger and record change history with undo | Proposed | Generalizes the existing `reconciliation.undo_last` pattern into a shared change-log table (old/new values, timestamp) covering ledger entries, accounts, vendors, and customers. |
| ST-039 Vendor 1099-NEC summary export | Proposed | A report/export summing ledger payments per vendor for a calendar year, built on the existing `reports.py`/`data_exchange.py` patterns. |
| ST-040 Dashboard trend charts and AR/AP aging | Proposed | Adds simple charts and an aging breakdown to `books.dashboard_summary`; depends on ST-033 for the accounts-payable side of aging. |
| ST-041 Parameterized reconciliation queries | Proposed | `reconciliation.py` currently builds SQL with f-strings (e.g. `WHERE Debit_Acct = '{account_id}'`, `Transaction_ID IN ({id_list})`); convert to parameterized queries to match the rest of the codebase's SQL safety rule (see `docs/ARCHITECTURE.md`). |
| ST-042 Retire legacy `repository/` write methods | Proposed | `repository/account.py`, `vendor.py`, `customer.py`, `invoice.py`, `owner.py`, `property.py`, `sku.py` still build `insert`/`update` SQL with unescaped f-strings. Confirmed these are not reachable from live writes today (`api.py` uses `records.py` or direct `?`-parameterized `connection.execute` calls instead) but they are dead, unsafe code sitting next to the pattern they're supposed to have been replaced by. |
| ST-043 Multi-machine / cloud-sync safety guidance | Proposed | No lock file or multi-machine coordination exists today; document the risk and a safe workflow, and consider a simple lock file as a stretch goal. |
| ST-044 Extension points for reports/transitions/shortcuts | Proposed; optional | Would relax the closed registries (`reports.REPORT_TYPES`, `invoice_lifecycle.TRANSITIONS`, `web/render_tools.js` `SHORTCUTS`) into a documented registration pattern. Weigh against `docs/ARCHITECTURE.md`'s explicit preference for one simple registry per concept before committing to this. |
