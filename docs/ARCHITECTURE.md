# Architecture

Iceberg is a desktop application: a native webview window (pywebview) hosting an
HTML/CSS/JavaScript interface over a Python core, with an encrypted SQLite database held
in memory while it is open. The code is split into layers so accounting rules,
persistence, startup, and presentation can be changed and tested independently.

```
webapp.py                  Host: starts the API server, opens the window (or --browser), native dialogs
server.py                  Local HTTP JSON API (stdlib) driven by web/routes.js; token + lock
api.py                     IcebergApi: every operation as JSON in / JSON out; @operation guards
web/                       The interface: routes.js, client.js, render*.js, app.js (see docs/WEB_INTERFACE.md)
├── session.py             IcebergSession: open database, console log, unsaved-change tracking, autosave timing
├── books.py               Schema, default chart of accounts, create/open, dashboard and ledger queries
├── records.py             Accounts, vendors, customers, services (parameterised SQL)
├── invoices.py            Invoice totals, storage, PDF rendering
├── accounting rules       No GUI imports; fully unit tested
│   ├── accounting.py      Account types, signed balances, ledger reads
│   ├── validation.py      Entry-time checks with field-level errors
│   ├── invoice_lifecycle.py  Invoice state machine, ledger postings, history
│   ├── reconciliation.py  Statement reconciliation
│   ├── reports.py         Income statement, balance sheet, cash flow
│   └── data_exchange.py   CSV import/export
├── persistence
│   ├── db_calls.py        SQLite helpers, Fernet encryption, atomic verified saves
│   ├── backups.py         Timestamped backups and restore
│   └── repository/        Original per-table classes (still used by books.py for table creation)
├── paths.py               Data-folder layout (per-user / portable / --data-dir)
├── preferences.py         preferences.json (appearance, text size, compact rows)
├── version.py             The product version (one place)
├── startup_checks.py      Pre-flight checks with plain-language fixes
├── iceberg_time.py        UTC storage, local display, monotonic scheduling
└── iceberg_utils.py       Currency formatting helpers
```

## Rules of the road

- **Accounting and persistence modules never import a GUI toolkit or pywebview.** They
  take plain values and connections and return plain results, which `api.py` turns into
  JSON and the front-end turns into screens. This is what makes the test suite runnable
  without a display.
- **`api.py` never raises.** Every method returns `{"ok", "message", "errors": [{"field",
  "message"}], ...}`; unexpected exceptions are caught, logged to the console, and
  reported as a message.
- **One registry per concept:** navigation (`web/render.js` `NAV`), shortcuts
  (`web/render_tools.js` `SHORTCUTS` + `app.js` key map), report types
  (`reports.REPORT_TYPES`), invoice transitions (`invoice_lifecycle.TRANSITIONS`),
  property names (`books.PROPERTY_NAMES`).
- **All stored timestamps are UTC ISO 8601**; display conversion happens at the edge.
- **Writes to disk are atomic** (`db_calls.atomic_write_bytes`) and every save returns a
  result object that the interface shows.
- **SQL takes parameters**, never f-strings, in new code (`records.py`, `invoices.py`,
  `books.py`).

## Lifecycle of a session

`webapp.py` runs the startup checks, creates `DesktopApi` (the API plus native file
dialogs), starts `server.ApiServer` on a random loopback port, and opens the window on
`http://127.0.0.1:<port>/?token=...`. The page builds its `Api` client from `routes.js`
and polls `app.status` / `app.autosave` every five seconds; autosave writes only when
bookkeeping data changed. Closing the window calls `app.shutdown`, which saves the database
and the session log, then the server stops.

## Build, packaging, website

`packaging/iceberg.spec` (PyInstaller one-folder build), `scripts/build_release.py`
(build → verify with `--version`/`--check` → archive + installer + notes + checksums),
`packaging/windows/iceberg.iss` (Inno Setup), `packaging/linux/` (install/uninstall,
desktop entry), `.github/workflows/release.yml` (tag-driven release), `site/`
(static website built by `site/build.py`, deployed by `site.yml`), and
`scripts/publish_release_info.py` (records checksums for the downloads page).

## Release checks

`scripts/check_release.py` runs compile, pyflakes, data-file/doc presence, the Python
tests, the Node view tests, and `pip check`; `--wheels` verifies that every pinned
dependency has a prebuilt wheel for Python 3.11–3.14 on Windows and Linux.
`.github/workflows/ci.yml` runs it on Ubuntu and Windows for each interpreter with
wheels-only installs.
