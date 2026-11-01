# BUG-003 — Tcl/Tk runtime lookup fails on one Windows Python 3.13 installation

- **Status:** Resolved in 1.2 (ST-002). `startup_checks.repair_tcl_tk_environment()` reproduces the manual workaround automatically and `tkinter_problem()` reports a plain-language fix. Verified by `tests/test_startup_checks.py::TestTclTkRepair`; confirmation on the original `.venv313` machine is still welcome.
- **Priority:** P1
- **Area:** Windows GUI startup
- **Affected environment:** Windows, Python 3.13, virtual environment `.venv313`

## Description

Importing PySimpleGUI raised `_tkinter.TclError: Can't find a usable init.tcl`. Tcl/Tk files were present under the base Python installation's `tcl` directory. Setting `TCL_LIBRARY` and `TK_LIBRARY` to those directories allowed startup to proceed to the separate timer crash tracked in BUG-001.

## Reproduction

1. Create a Python 3.13 virtual environment and install the project requirements.
2. Run `python iceberg.py` without Tcl/Tk environment variables.

## Expected

The documented Windows Python installation provides a working Tkinter runtime, or setup instructions explain the required Python installer components and configuration.

## Suggested resolution

Confirm the required Tcl/Tk installer options on a clean Windows machine. Document the supported installation path and add a startup diagnostic that identifies missing Tcl/Tk files.

## Resolution (version 1.2)

- `startup_checks.repair_tcl_tk_environment()` runs before PySimpleGUI is imported. When `TCL_LIBRARY`/`TK_LIBRARY` are unset it looks for `tcl8.6/init.tcl` and `tk8.6/tk.tcl` under the base Python installation (`sys.base_prefix`) and sets the variables for the process, reproducing the manual workaround automatically.
- `startup_checks.tkinter_problem()` creates a hidden Tk root to prove the toolkit works. If it fails, the user sees "The Tk GUI toolkit cannot start" with the installer option to tick and the environment variables to set, instead of a `_tkinter.TclError` traceback.
- `docs/SETUP.md` documents the required installer option (*tcl/tk and IDLE*).

**Verification needed:** rerun `python iceberg.py` in the original `.venv313` without the environment variables set.
