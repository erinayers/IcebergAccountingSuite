# ST-015 — Clear application navigation

- **Status:** Implemented
- **Priority:** P2
- **Area:** Navigation

## User story

As a user, I want a persistent, clearly labeled way to move between Dashboard,
Ledger, Invoices, Customers, Vendors, and Services so I can find common tasks without
searching nested menus.

## Acceptance criteria

- [x] A persistent navigation element is visible on every screen, with the current
      location highlighted.
- [x] One navigation registry drives both the visible tabs and their keyboard
      shortcuts (Ctrl+1…Ctrl+8) — not duplicated per-screen logic.
- [x] Navigation covers Dashboard, Ledger, Invoices, Customers, Vendors, Services,
      Reports, Reconcile.

## Implementation evidence

`web/render.js` (`NAV`), `docs/UI_GUIDE.md`.
