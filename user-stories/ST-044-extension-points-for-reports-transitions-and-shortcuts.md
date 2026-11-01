# ST-044 — Extension points for reports, invoice transitions, and shortcuts (optional)

- **Status:** Proposed, optional — weigh against `docs/ARCHITECTURE.md`'s "one
  registry per concept" simplicity rule before committing
- **Priority:** P4
- **Area:** Extensibility

## User story

As a maintainer, I want a documented, minimal checklist for registering a new report
type, invoice transition, or shortcut without touching dispatch logic in multiple
files.

## Acceptance criteria

- [ ] A short, explicit checklist exists (in `docs/ARCHITECTURE.md` or a new
      CONTRIBUTING-adjacent doc) listing every file that must change to add a new
      report type, a new invoice status/transition, or a new keyboard shortcut.
- [ ] Where reasonably possible, the number of files that must change for each of
      these additions is reduced (e.g. a single registration call rather than edits
      in three separate places), without introducing a generic plugin-loading
      mechanism that the project doesn't otherwise need.
- [ ] This explicitly stops short of a dynamic/pluggable extension system — it should
      not conflict with `docs/ARCHITECTURE.md`'s existing simplicity rule ("one
      registry per concept").
- [ ] Before implementation, an explicit decision is recorded on whether this is worth
      doing at all, since it's optional and may not be worth the churn for a
      single-maintainer or small-contributor-base project.
- [ ] If implemented, covered by a test that adding a new report type/transition/
      shortcut following the checklist actually works end-to-end (not just that the
      checklist reads well).

## Scope notes

Lowest priority of all open stories. Take on only if the closed-registry pattern
(`reports.REPORT_TYPES`, `invoice_lifecycle.TRANSITIONS`, `web/render_tools.js`
`SHORTCUTS`) becomes a real contributor pain point.
