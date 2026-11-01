# ST-034 — Recurring transactions and invoices

- **Status:** Proposed, not started
- **Priority:** P3
- **Area:** Automation

## User story

As a bookkeeper, I want to schedule recurring ledger entries and invoices (rent,
subscriptions, retainers) to post automatically or with one click on their due date,
so I don't have to re-enter the same transaction every period.

## Acceptance criteria

- [ ] A recurrence schedule (frequency, next-due date, and a template referencing an
      existing transaction or invoice shape) can be created and edited.
- [ ] Due-today (and overdue) recurring items are surfaced on the Dashboard, not
      buried in a separate screen the user has to remember to check.
- [ ] Posting a recurring item reuses the existing transaction/invoice creation code
      paths (and their validation) rather than a separate, divergent insert path.
- [ ] A recurring schedule can be paused, resumed, or canceled without affecting
      transactions/invoices it has already posted.
- [ ] Each posted occurrence is linked back to its originating schedule so its origin
      is auditable later.
- [ ] Covered by tests for schedule CRUD, due-date computation across month/leap-year
      boundaries, and posting idempotency (an item due today is not posted twice if
      the due-today check runs more than once).

## Scope notes

Stored alongside existing ledger/invoice records; posting reuses existing creation
paths rather than introducing a parallel one.
