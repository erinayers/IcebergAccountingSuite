# ST-039 — Vendor 1099-NEC summary export

- **Status:** Proposed, not started
- **Priority:** P3
- **Area:** Tax Forms

## User story

As a business owner, I want a year-end summary of payments to each vendor, so I can
prepare 1099-NEC filings without re-tallying the ledger by hand.

## Acceptance criteria

- [ ] A new report (or export) sums ledger payments per vendor for a selected calendar
      year.
- [ ] Only payment-type postings (not all transactions referencing a vendor, e.g. not
      refunds or unrelated notes) are included in the sum.
- [ ] The output includes the vendor's identifying details already on file (business
      name, address) alongside the total, so it's usable as a starting point for an
      actual 1099-NEC without manual lookup.
- [ ] The report/export can be filtered to vendors above a configurable reporting
      threshold (the current IRS 1099-NEC threshold is user-configurable, not
      hard-coded, since thresholds change).
- [ ] The output can be exported to CSV, consistent with the other reports/exports in
      `data_exchange.py`.
- [ ] Covered by tests verifying the sum excludes non-payment postings and handles a
      vendor with zero qualifying payments (omitted or shown as zero, not erroring).

## Scope notes

Built on the existing `reports.py`/`data_exchange.py` patterns; no new infrastructure
needed.
