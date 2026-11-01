# User stories and product roadmap

This folder tracks proposed and delivered product work for Iceberg Accounting Suite.
Each story has its own file (`ST-XXX-slug.md`) with its full user story, elaborated
acceptance criteria, and implementation evidence or scope notes — this file is the
index and the roadmap-level summary, mirroring how `bugs/README.md` indexes
`bugs/BUG-XXX-*.md`.

Priorities are product-owner recommendations based on the current README, source
layout, tests, and real issues reported during setup. They are not commitments or
release dates.

## Roadmap

### P0 — Make startup and data handling dependable: implemented in version 1.2

| Story | Status |
|-------|--------|
| [ST-001 — Supported installation](ST-001-supported-installation.md) | Implemented; Windows walkthrough awaiting verification |
| [ST-002 — Clear startup errors](ST-002-clear-startup-errors.md) | Implemented |
| [ST-003 — Safe database saves](ST-003-safe-database-saves.md) | Implemented |
| [ST-004 — Recoverable backups](ST-004-recoverable-backups.md) | Implemented |
| [ST-005 — Consistent time handling](ST-005-consistent-time-handling.md) | Implemented; BUG-001 awaiting Windows verification |

### P1 — Improve accounting confidence and daily workflows: implemented in version 1.3

| Story | Status |
|-------|--------|
| [ST-006 — Reconciliation](ST-006-reconciliation.md) | Implemented |
| [ST-007 — Financial reports](ST-007-financial-reports.md) | Implemented |
| [ST-008 — Invoice lifecycle clarity](ST-008-invoice-lifecycle-clarity.md) | Implemented |
| [ST-009 — Data validation](ST-009-data-validation.md) | Implemented |
| [ST-010 — Import and export](ST-010-import-and-export.md) | Implemented |

### P2 — Maintainability and accessibility / Modernize the desktop interface: implemented in version 1.4; UI rebuilt on web technology in 2.0

| Story | Status |
|-------|--------|
| [ST-011 — Accessible interface](ST-011-accessible-interface.md) | Implemented; screen-reader pass pending |
| [ST-012 — Modular application](ST-012-modular-application.md) | Implemented |
| [ST-013 — Automated release checks](ST-013-automated-release-checks.md) | Implemented |
| [ST-014 — Consistent visual system](ST-014-consistent-visual-system.md) | Implemented |
| [ST-015 — Clear application navigation](ST-015-clear-application-navigation.md) | Implemented |
| [ST-016 — Responsive workspace](ST-016-responsive-workspace.md) | Implemented (structural); visual check pending |
| [ST-017 — Readable data tables](ST-017-readable-data-tables.md) | Implemented |
| [ST-018 — Contextual action feedback](ST-018-contextual-action-feedback.md) | Implemented |
| [ST-019 — Focused data-entry forms](ST-019-focused-data-entry-forms.md) | Implemented |
| [ST-020 — Theme and display preferences](ST-020-theme-and-display-preferences.md) | Implemented |

The wireframe supplied for the modernization could not be reproduced in Tk, so the Tk
interface was retired in version 2.0 and replaced by a native webview window
(pywebview) hosting an HTML/CSS/JS front-end over a JSON API (`api.py`) on the
unchanged accounting core. ST-011 and ST-014–ST-020 are delivered on that stack
(`docs/UI_GUIDE.md`, `docs/WEB_INTERFACE.md`, `docs/screens/`) — see each story file
for what's carried forward versus what's web-native.

### P1 — Simplify building, packaging, and releasing: implemented in version 2.0

| Story | Status |
|-------|--------|
| [ST-021 — Repeatable build](ST-021-repeatable-build.md) | Implemented |
| [ST-022 — Platform packages](ST-022-platform-packages.md) | Implemented; Windows installer build needs a Windows run |
| [ST-023 — User data locations](ST-023-user-data-locations.md) | Implemented |
| [ST-024 — Release artifacts](ST-024-release-artifacts.md) | Implemented |
| [ST-025 — Automated release pipeline](ST-025-automated-release-pipeline.md) | Implemented; first run happens on the first tag |
| [ST-026 — Deployment and upgrade guide](ST-026-deployment-and-upgrade-guide.md) | Implemented |

### P1 — Build a marketing and distribution website: implemented in version 2.0

| Story | Status |
|-------|--------|
| [ST-027 — Product website](ST-027-product-website.md) | Implemented |
| [ST-028 — Trusted downloads](ST-028-trusted-downloads.md) | Implemented |
| [ST-029 — Getting started and support](ST-029-getting-started-and-support.md) | Implemented |
| [ST-030 — Project transparency](ST-030-project-transparency.md) | Implemented |
| [ST-031 — Accessible, maintainable site](ST-031-accessible-maintainable-site.md) | Implemented |

### P3 — Advanced accounting workflows: proposed, not started

| Story | Status |
|-------|--------|
| [ST-032 — Inline custom chart-of-accounts creation](ST-032-inline-custom-chart-of-accounts-creation.md) | Proposed |
| [ST-033 — Accounts payable / bills](ST-033-accounts-payable-bills.md) | Proposed |
| [ST-034 — Recurring transactions and invoices](ST-034-recurring-transactions-and-invoices.md) | Proposed |
| [ST-035 — Bank statement import (OFX/QFX)](ST-035-bank-statement-import.md) | Proposed |
| [ST-036 — Budgets and budget-vs-actual reporting](ST-036-budgets-and-budget-vs-actual-reporting.md) | Proposed |
| [ST-037 — Multi-currency accounts and transactions](ST-037-multi-currency-accounts-and-transactions.md) | Proposed; needs design review first |

### P3 — Auditability and reporting depth: proposed, not started

| Story | Status |
|-------|--------|
| [ST-038 — Ledger and record change history with undo](ST-038-ledger-and-record-change-history-with-undo.md) | Proposed |
| [ST-039 — Vendor 1099-NEC summary export](ST-039-vendor-1099-nec-summary-export.md) | Proposed |
| [ST-040 — Dashboard trend charts and AR/AP aging](ST-040-dashboard-trend-charts-and-ar-ap-aging.md) | Proposed |

### P4 — Platform hardening

| Story | Status |
|-------|--------|
| [ST-041 — Parameterized reconciliation queries](ST-041-parameterized-reconciliation-queries.md) | **Implemented** |
| [ST-042 — Retire legacy `repository/` write methods](ST-042-retire-legacy-repository-write-methods.md) | Proposed |
| [ST-043 — Multi-machine / cloud-sync safety guidance](ST-043-multi-machine-cloud-sync-safety-guidance.md) | Proposed |
| [ST-044 — Extension points for reports/transitions/shortcuts](ST-044-extension-points-for-reports-transitions-and-shortcuts.md) | Proposed; optional |

## Suggested delivery order

1. Resolve BUG-001 and BUG-002; establish a supported Python and OS matrix (ST-001, ST-002, ST-005).
2. Make database saves observable and recoverable (ST-003, ST-004).
3. Add validation and accounting workflow coverage, beginning with reconciliation and invoice lifecycle history (ST-006, ST-008, ST-009).
4. Add reporting and data exchange improvements (ST-007, ST-010).
5. Establish a supported build process and user data layout, then package and document releases (ST-021–ST-024, ST-026).
6. Publish the product, support, transparency, and verified download information on the website (ST-027–ST-031), once release artifacts and support processes are ready.
7. Modernize navigation, layout, tables, and forms as a coherent UI update (ST-014–ST-020), with accessibility requirements included from the start (ST-011).
8. Improve modularity and automate compatibility and release checks (ST-012, ST-013, ST-025).
9. ST-041 (reconciliation SQL cleanup) is done. Continue the next phase with the remaining low-risk, high-value workflow fixes: inline custom-account creation and the repository SQL cleanup (ST-032, ST-042). Then extend core bookkeeping parity with bills/AP and recurring transactions (ST-033, ST-034). Add bank statement import and change history/undo once those are stable (ST-035, ST-038), followed by budgets, dashboard trend charts, and the 1099 summary (ST-036, ST-039, ST-040). Document multi-machine/cloud-sync safety whenever it's convenient (ST-043) — it's independent of the rest. Leave multi-currency (ST-037) for last — it is the largest and riskiest story and should get its own design review before scheduling. Treat extension points (ST-044) as optional; only take it on if the closed-registry pattern becomes a real contributor pain point.

## Adding a new story

Create `ST-XXX-slug.md` following the existing files' template (User story, Acceptance
criteria as a checklist, Implementation evidence or Scope notes), then add it to the
relevant table above and to the delivery order if it changes sequencing.
