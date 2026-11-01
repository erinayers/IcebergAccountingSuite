# ST-026 — Deployment and upgrade guide

- **Status:** Implemented
- **Priority:** P1
- **Area:** Deployment

## User story

As a user or IT administrator, I want platform-specific install, first-run, upgrade,
rollback, and uninstall instructions so I can manage the application over time.

## Acceptance criteria

- [x] `docs/DEPLOYMENT.md` documents data locations, download verification, and
      per-platform install/first-run/upgrade/rollback/uninstall steps.
- [x] Managed/silent install guidance is included for IT deployment scenarios.
- [x] A self-check mechanism (`--check`) is documented for confirming a deployed build
      is healthy.

## Implementation evidence

`docs/DEPLOYMENT.md`.
