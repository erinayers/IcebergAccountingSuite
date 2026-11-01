# ST-021 — Repeatable build

- **Status:** Implemented
- **Priority:** P1
- **Area:** Build

## User story

As a maintainer, I want a documented, one-command build process using pinned,
supported dependencies so I can produce the same runnable application from a clean
checkout.

## Acceptance criteria

- [x] A single entry-point script (`compile.s` on Linux, `build.ps1` on Windows)
      drives the full build.
- [x] `scripts/build_release.py` creates a virtual environment, installs pinned
      wheels, builds with PyInstaller using `packaging/iceberg.spec`, and self-verifies
      the built program (`--version`, `--check`).
- [x] The process has been verified by building on Linux and exercising the frozen
      binary's server.

## Implementation evidence

`compile.s`, `build.ps1`, `scripts/build_release.py`, `packaging/iceberg.spec`.
