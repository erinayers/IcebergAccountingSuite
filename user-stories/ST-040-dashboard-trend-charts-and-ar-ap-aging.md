# ST-040 — Dashboard trend charts and AR/AP aging

- **Status:** Proposed, not started
- **Priority:** P3
- **Area:** Dashboard

## User story

As a business owner, I want simple trend charts (revenue/expense over time) and an
accounts-receivable (and, once ST-033 exists, accounts-payable) aging view on the
dashboard, so I can spot trends and overdue balances at a glance instead of reading
report tables.

## Acceptance criteria

- [ ] The Dashboard shows a simple revenue-vs-expense trend chart (e.g. by month) for
      a selectable recent period.
- [ ] The Dashboard shows an accounts-receivable aging breakdown (e.g. current /
      1-30 / 31-60 / 61-90 / 90+ days overdue) computed from open invoices.
- [ ] Once [ST-033](ST-033-accounts-payable-bills.md) (bills) exists, the same aging
      breakdown is available for accounts payable.
- [ ] Charts render without a new heavyweight JS charting dependency, consistent with
      `web/`'s current vanilla-JS approach (hand-rolled SVG/canvas, or a very small,
      vetted library if one is chosen deliberately).
- [ ] The chart/aging data degrades gracefully (shows an empty-state message, not an
      error) for a business with little or no history yet.
- [ ] Covered by tests for the aging-bucket computation logic independent of
      rendering (a pure function given a list of open invoices and "today").

## Scope notes

Depends on [ST-033](ST-033-accounts-payable-bills.md) for the accounts-payable side of
aging; the AR side and trend chart can ship independently.
