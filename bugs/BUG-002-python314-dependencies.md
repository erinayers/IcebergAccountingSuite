# BUG-002 — Python 3.14 cannot install pinned CFFI dependency without a compiler

- **Status:** Resolved in 1.2 (ST-001/ST-002). Supported interpreters (3.11-3.13) are declared in `docs/SETUP.md`, `README.md`, and `requirements.txt`; `startup_checks.py` warns on 3.14 with the fix. Verified by `tests/test_startup_checks.py`.
- **Priority:** P0
- **Area:** Installation and dependency support
- **Affected environment:** Windows, Python 3.14.2

## Description

Installing `requirements.txt` attempts to build pinned `cffi==1.17.0` from source and fails because Microsoft C++ Build Tools are not installed. The traceback ends with `Microsoft Visual C++ 14.0 or greater is required`. The project README only says Python 3, so users are not told which interpreter version is supported or that a compiler may be needed.

## Reproduction

1. Create a virtual environment with Python 3.14.
2. Run `python -m pip install -r requirements.txt`.

## Expected

The documented Python version installs the pinned dependencies using available wheels, or setup instructions explain any required compiler/toolchain.

## Suggested resolution

Declare and document supported Python versions and operating systems, then update or constrain dependencies accordingly. Verify the full install from a clean environment on each supported platform.

## Resolution (version 1.2)

- Supported interpreters are now declared: Python 3.11, 3.12, and 3.13 (`docs/SETUP.md`, `README.md`, header of `requirements.txt`). 3.14 is documented as unsupported until the pinned packages publish wheels for it.
- `startup_checks.py` warns when Iceberg is launched on an unsupported interpreter and explains that the fix is to create the virtual environment with `py -3.13`.
- The Windows setup walkthrough shows how to install 3.13 side by side and select it with the `py` launcher.

**Verification needed:** on a clean Windows machine with Python 3.13 only, `py -3.13 -m venv .venv`, install `requirements.txt`, and confirm no package is built from source.

## Recurrence and final resolution (version 2.0)

The error came back when `pip install -r requirements.txt` was run from a PowerShell
whose `pip` belonged to Python 3.14 (both 3.13 and 3.14 were installed; the app itself had
been started with 3.13). Rather than keep 3.14 unsupported, every pinned package was moved
to a release that publishes prebuilt wheels for Python 3.11, 3.12, 3.13 **and** 3.14 on
Windows (`win_amd64`) and Linux (`manylinux_2_28`/`manylinux2014`):

| Package | Old pin | New pin |
|---------|---------|---------|
| cffi | 1.17.0 (no 3.14 wheel) | 2.1.1 |
| cryptography | 43.0.0 | 46.0.3 |
| pillow | 10.4.0 | 12.1.1 |
| lxml | 5.3.1 | 6.1.3 |
| pikepdf | 9.5.2 | 10.17.0 |
| img2pdf | 0.6.0 (source only) | 0.6.3 |
| pyinstaller / hooks | 6.17.0 / 2025.11 | 6.22.3 / 2026.9 |

`scripts/check_release.py --wheels` downloads every pin for each interpreter/OS with
`--only-binary=:all:` and fails if any would need a compiler; CI now runs the full matrix
including 3.14. The test suite and the invoice image-to-PDF path were run against the new
libraries. `docs/SETUP.md` now tells Windows users to create environments through the
`py` launcher so the intended interpreter is used.
