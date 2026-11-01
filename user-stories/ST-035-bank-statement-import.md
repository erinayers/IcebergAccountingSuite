# ST-035 — Bank statement import (OFX/QFX)

- **Status:** Proposed, not started
- **Priority:** P3
- **Area:** Bank Import

## User story

As a bookkeeper, I want to import a bank or card statement in OFX/QFX format, so
reconciling a month of activity is faster than retyping a CSV and transactions match
against existing ledger entries where possible.

## Acceptance criteria

- [ ] An OFX/QFX file can be selected and parsed into a list of candidate statement
      transactions (date, amount, description).
- [ ] Parsed transactions are run through the same validation path CSV import already
      uses (`data_exchange.py`), with the same line/entry-level error reporting.
- [ ] Parsed transactions that plausibly match an existing, unreconciled ledger entry
      (by date/amount/account) are pre-matched for the user rather than treated as
      brand-new.
- [ ] Unmatched statement transactions feed into the existing `reconciliation.py`
      candidate list/workflow rather than a separate, parallel UI.
- [ ] A malformed or unsupported OFX/QFX file produces a clear error, not a partial
      import or a crash.
- [ ] Covered by tests using at least one real-world-shaped sample OFX file committed
      under `docs/samples/`, plus a malformed-file case.

## Scope notes

Extends `data_exchange.py`'s importer with an OFX/QFX parser feeding the same
validation path as CSV import, then into the existing reconciliation candidate list.
