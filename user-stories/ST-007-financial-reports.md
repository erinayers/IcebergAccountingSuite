# ST-007 — Financial reports

- **Status:** Implemented
- **Priority:** P1
- **Area:** Reports

## User story

As a small-business owner, I want standard income statement, balance sheet, and cash
flow reports for a selected period so I can review business performance.

## Acceptance criteria

- [x] Income Statement, Income Statement by Month, Balance Sheet, and Cash Flow (direct
      method) report types are available.
- [x] The Balance Sheet includes a balance check (assets = liabilities + equity).
- [x] Cash Flow treats working-capital accounts (inventory, A/R, A/P, sales tax
      payable) as operating activity.
- [x] Reports can be run for named presets (This Year, Last Year, This Quarter, etc.)
      or a custom date range.
- [x] Reports can be exported to CSV.
- [x] Documented in `docs/REPORTS.md`; covered by `tests/test_reports.py`.

## Implementation evidence

`reports.py`, `docs/REPORTS.md`, `tests/test_reports.py`.
