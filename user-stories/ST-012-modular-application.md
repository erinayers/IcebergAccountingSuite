# ST-012 — Modular application

- **Status:** Implemented
- **Priority:** P2
- **Area:** Architecture

## User story

As a maintainer, I want UI, accounting rules, persistence, and startup code separated
into focused modules so changes are easier to review and safer to test.

## Acceptance criteria

- [x] Accounting and persistence modules (`accounting.py`, `validation.py`,
      `invoice_lifecycle.py`, `reconciliation.py`, `reports.py`, `data_exchange.py`,
      `db_calls.py`, `backups.py`) never import a GUI toolkit or pywebview.
- [x] Session/state management lives in `session.py`; presentation logic lives in its
      own layer (originally `ui/`, now `web/` + `api.py`).
- [x] The module map and the rules that keep it that way are documented in
      `docs/ARCHITECTURE.md`.
- [x] The accounting/persistence test suite runs headless, with no display required.

## Implementation evidence

`docs/ARCHITECTURE.md`, module layout described there.
