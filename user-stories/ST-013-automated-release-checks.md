# ST-013 — Automated release checks

- **Status:** Implemented
- **Priority:** P2
- **Area:** CI/CD

## User story

As a maintainer, I want supported Python/platform combinations checked in continuous
integration so incompatible dependency changes are caught before release.

## Acceptance criteria

- [x] `scripts/check_release.py` runs a compile check, pyflakes, data-file/doc
      presence checks, the full test suite, `pip check`, and (optionally)
      wheel-availability verification across Python 3.11–3.14 on Windows and Linux.
- [x] `.github/workflows/ci.yml` runs this on Ubuntu and Windows for each supported
      interpreter using wheels-only installs.
- [x] A failure in any supported combination fails CI before a release can be tagged.
- [x] Covered by `tests/test_check_release.py`.

## Implementation evidence

`scripts/check_release.py`, `.github/workflows/ci.yml`, `tests/test_check_release.py`.
