# ST-024 — Release artifacts

- **Status:** Implemented
- **Priority:** P1
- **Area:** Release

## User story

As a maintainer, I want each release to include versioned installers or archives,
checksums, and concise upgrade notes so users can identify and verify the right
download.

## Acceptance criteria

- [x] Each release produces versioned archives/installers.
- [x] `SHA256SUMS-<platform>.txt` accompanies every release.
- [x] `RELEASE_NOTES.md` is generated from the relevant `CHANGELOG.md` section.
- [x] `version.py` is the single source of truth for the product version, checked by
      `tests/test_build_release.py`.

## Implementation evidence

`version.py`, `CHANGELOG.md`, `tests/test_build_release.py`.
