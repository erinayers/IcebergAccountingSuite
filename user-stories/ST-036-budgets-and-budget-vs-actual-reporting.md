# ST-036 — Budgets and budget-vs-actual reporting

- **Status:** Proposed, not started
- **Priority:** P3
- **Area:** Budgeting

## User story

As a business owner, I want to set a budget per account and period and see
budget-vs-actual on reports, so I can track spending and revenue against plan.

## Acceptance criteria

- [ ] A budget can be set per account for a given period (e.g. month or year) and
      edited later.
- [ ] A new report type ("Budget vs. Actual") appears alongside the existing entries
      in `reports.REPORT_TYPES`.
- [ ] The report shows, per account, the budgeted amount, the actual amount for the
      selected period, and the variance (absolute and percentage).
- [ ] The report respects the same period presets (This Year, This Quarter, custom
      range, etc.) as the other report types.
- [ ] The report can be exported to CSV like the existing reports.
- [ ] Covered by tests mirroring `tests/test_reports.py`'s structure, including a case
      with no budget set for an account (should show actual-only, not an error).

## Scope notes

New budget table (account, period, amount) plus one new report type; no changes to
existing report types.
