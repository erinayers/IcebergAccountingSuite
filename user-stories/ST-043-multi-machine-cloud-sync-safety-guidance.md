# ST-043 — Multi-machine / cloud-sync safety guidance

- **Status:** Proposed, not started
- **Priority:** P4
- **Area:** Multi-Machine Sync

## User story

As a user who keeps a database folder in a cloud-synced location (Dropbox, OneDrive,
Google Drive) and might open Iceberg from more than one machine, I want documented
guidance (and ideally a lock file or open-elsewhere warning) so two machines can't
silently save conflicting versions of the same encrypted `.icb`, since the current
design assumes one machine with no cross-machine coordination.

## Acceptance criteria

- [ ] `docs/BACKUP_AND_RESTORE.md` (or a new doc) explicitly states the risk of
      opening the same database from two machines/processes at once via a sync
      folder, and recommends a safe workflow (e.g. close on one machine, wait for
      sync, then open on the other).
- [ ] Opening a database creates a lightweight lock marker (e.g. a sidecar file)
      recording which machine/process has it open.
- [ ] Opening a database that already has a live lock marker warns the user clearly
      before proceeding, rather than silently allowing two concurrent writers.
- [ ] The lock marker is cleaned up reliably on normal exit, and a stale lock marker
      (e.g. left over from a crash) does not permanently block the user from
      reopening on the same machine — the warning is informative, not a hard lock a
      user can get stuck behind.
- [ ] Covered by tests for lock creation/cleanup/staleness detection.

## Scope notes

Docs-only is the minimum viable version of this story; the lock file is a stretch
goal on top of it.
