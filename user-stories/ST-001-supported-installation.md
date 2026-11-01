# ST-001 — Supported installation

- **Status:** Implemented; Windows walkthrough awaiting verification on a clean machine
- **Priority:** P0
- **Area:** Setup & Installation

## User story

As a new user, I want a documented, reproducible setup on supported Windows and Linux
versions so I can install and launch the desktop app without guessing which Python
version or system libraries are required.

## Acceptance criteria

- [x] The supported Python version range (3.11–3.14) and supported OS versions are
      stated in one place (`README.md`, `docs/SETUP.md`).
- [x] Step-by-step Windows (PowerShell) and Linux (`apt` + venv) instructions exist and
      use copy-pasteable commands.
- [x] `requirements.txt` pins dependency versions that install from prebuilt wheels on
      every supported Python/OS combination (no compiler required).
- [x] A troubleshooting table in `docs/SETUP.md` covers the most common setup failures
      with plain-language fixes.
- [ ] The Windows walkthrough has been verified end-to-end on a clean machine (tracked
      as an open follow-up, not yet confirmed).

## Implementation evidence

`docs/SETUP.md` (platform matrix, walkthrough, troubleshooting table), the
"Installing and starting" section of `README.md`, and `requirements.txt`.
