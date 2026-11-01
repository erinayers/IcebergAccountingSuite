# ST-010 — Import and export

- **Status:** Implemented
- **Priority:** P1
- **Area:** Import/Export

## User story

As a bookkeeper, I want to export reports and back up or migrate records using
documented formats so I can work with my accountant and move between machines.

## Acceptance criteria

- [x] The ledger can be exported to CSV with account names resolved (not just IDs).
- [x] All core tables (accounts, vendors, customers, services, invoices, invoice
      history, reconciliations) can be exported.
- [x] Reports can be exported to CSV.
- [x] CSV transaction import accepts the documented column layout plus common header
      aliases (e.g. "Payee" for Name).
- [x] Import runs every row through the same validation as manual entry, reports
      line-numbered errors, and writes nothing if any row fails (all-or-nothing).
- [x] A successful import triggers an automatic save and backup.
- [x] Documented in `docs/IMPORT_EXPORT.md` with a sample file in `docs/samples/`;
      covered by `tests/test_data_exchange.py`.

## Implementation evidence

`data_exchange.py`, `docs/IMPORT_EXPORT.md`, `docs/samples/`,
`tests/test_data_exchange.py`.
