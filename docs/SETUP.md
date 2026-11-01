# Iceberg Accounting Suite — Setup Guide

This guide gives a reproducible way to install and launch Iceberg from source on
Windows and Linux. If anything goes wrong, jump to [Troubleshooting](#troubleshooting);
every startup problem Iceberg can detect is listed there with its fix.

## Supported versions

| Component | Supported | Notes |
|-----------|-----------|-------|
| Python | **3.11, 3.12, 3.13, 3.14** | 3.10 and older are not supported. Every pinned dependency ships prebuilt wheels for all four versions on Windows and Linux, so installing never needs a C compiler (verified by `scripts/check_release.py --wheels`). |
| Windows | Windows 10 and 11 (64-bit) | Install Python from python.org with the **tcl/tk and IDLE** option ticked. |
| Linux | Ubuntu 22.04 / 24.04, Debian 12, Fedora 39+ | Needs WebKitGTK for Python (or the Qt extra). |
| Webview runtime | Edge WebView2 (Windows), WebKitGTK 2.x (Linux) | Windows 10/11 include WebView2. Linux: `gir1.2-webkit2-4.1 python3-gi`, or `pip install pywebview[qt]` instead. |

Iceberg is a desktop application: it needs a graphical session. The window is a native
webview (Edge WebView2 on Windows, WebKitGTK on Linux) hosting the interface.

## Windows

1. **Install Python 3.13 or 3.14** from <https://www.python.org/downloads/windows/>.
   In the installer tick **Add python.exe to PATH** (the defaults are otherwise fine).

2. **Open PowerShell** in the Iceberg folder (Shift + right-click → *Open PowerShell window here*).

3. **Create and activate a virtual environment** with the interpreter you want to use.
   **Always go through the `py` launcher** - when more than one Python is installed, the
   plain `pip` and `python` commands on your PATH may belong to a different version than
   you expect (that is how BUG-002 was reported):

   ```powershell
   py -0                      # lists the installed versions
   py -3.13 -m venv .venv     # or py -3.14
   .\.venv\Scripts\Activate.ps1
   ```

   Inside the activated environment `python` and `pip` refer to the venv, so the
   remaining commands are unambiguous.

   If PowerShell refuses to run the activation script, run
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use
   `.\.venv\Scripts\activate.bat` from a Command Prompt instead.

4. **Install the dependencies:**

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

   All packages install from prebuilt wheels on Python 3.11-3.14; no compiler is needed.
   If you ever see "Microsoft Visual C++ 14.0 or greater is required", pip is building a
   package from source - check `python --version` inside the environment and that you are
   installing from an up-to-date `requirements.txt`.


5. **Check the setup and launch:**

   ```powershell
   python startup_checks.py
   python webapp.py
   ```

   `startup_checks.py` prints `All startup checks passed.` or a list of problems with fixes.
   The same checks run automatically every time `webapp.py` starts.

   If the window opens but stays blank, install the **Microsoft Edge WebView2 Runtime**
   (free, from Microsoft); it is normally already present on Windows 10/11.

Subsequent launches: open PowerShell in the Iceberg folder, run `.\.venv\Scripts\Activate.ps1`,
then `python webapp.py`.

## Linux

1. **Install system packages.**

   Debian / Ubuntu:

   ```bash
   sudo apt install python3 python3-venv gir1.2-webkit2-4.1 python3-gi
   ```

   Fedora:

   ```bash
   sudo dnf install python3 webkit2gtk4.1 python3-gobject
   ```

   (If you prefer not to install system packages, `pip install pywebview[qt]` inside the
   virtual environment provides a Qt-based window instead - or run
   `python webapp.py --browser`, which opens the interface in your default browser.)

   Confirm the interpreter version is 3.11–3.13 with `python3 --version`. If your
   distribution ships a different version, install a supported one (for example
   `sudo apt install python3.12 python3.12-venv python3.12-tk`) and use that
   executable in the next step.

2. **Open a terminal in the Iceberg folder** and create the virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the dependencies:**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Check the setup and launch:**

   ```bash
   python startup_checks.py
   python webapp.py
   ```

Subsequent launches: `source .venv/bin/activate` then `python webapp.py`.

### Building a distributable folder

```bash
chmod u+x compile.s
./compile.s
```

This runs PyInstaller and produces `dist/iceberg/` containing the `iceberg` executable with
the `web`, `fonts`, and `docs` folders bundled. Copy the whole folder; databases and
backups are created next to the executable.

## Where Iceberg keeps its files

Iceberg always runs from its own folder (it changes the working directory on startup),
so it behaves the same whether launched from a terminal, a shortcut, or a file manager.
Display preferences are kept in `preferences.json` in the same folder.

| File / folder | Purpose |
|---------------|---------|
| `<Business>.icb` | Your encrypted accounting database, in the Iceberg folder. |
| `<Business>.icbkey` | The encryption key for that database, saved wherever you chose when creating it. **Without it the database cannot be opened — back it up somewhere safe.** |
| `backups/<Business>/` | Timestamped copies of the `.icb` written on every save. See [BACKUP_AND_RESTORE.md](BACKUP_AND_RESTORE.md). |
| `sessions.icbs`, `sessions.icbskey` | The console log for the application. Recreated automatically if missing. |
| `Invoices/` inside your receipts folder | Generated invoice PDFs and images. |

## Troubleshooting

Run `python startup_checks.py` to get the exact message for your machine.

| Message | Cause | Fix |
|---------|-------|-----|
| **Python 3.x is too old** | Interpreter older than 3.11. | Install a supported Python and recreate `.venv` with it. |
| **Microsoft Visual C++ 14.0 or greater is required** during `pip install` | pip is compiling a package from source: either an unsupported Python version or an old `requirements.txt` (BUG-002). | Run `py -0` to see your versions, create the venv with a supported one (`py -3.13 -m venv .venv`), activate it, and install from the current `requirements.txt`. |
| **pywebview is not installed** | The window host is missing from the environment. | Activate `.venv` and run `pip install -r requirements.txt`. |
| **No webview backend is installed** (Linux) | Neither WebKitGTK nor Qt WebEngine is available. | `sudo apt install gir1.2-webkit2-4.1 python3-gi`, or `pip install pywebview[qt]`. |
| **The window opens but is blank** (Windows) | The Edge WebView2 Runtime is missing. | Install the WebView2 Runtime from Microsoft, then start Iceberg again. |
| **PySimpleGUI is not installed** / **Missing package: …** | Dependencies were not installed into the active environment. | Activate `.venv` and run `pip install -r requirements.txt`. |
| **Missing file: …** | The Iceberg folder is incomplete (fonts, logo, artwork). | Restore the file from the download; keep the folder layout intact. |
| **sessions.icbskey is missing** | `sessions.icbs` exists without its key. | Delete or move `sessions.icbs`; a fresh log is created on launch. |
| **The database could not be opened — Filekey not found / does not match** | Wrong `.icbkey` selected, or the `.icb` is not in the Iceberg folder. | Select the key saved when the database was created; the matching `.icb` must sit in the Iceberg folder. |
| **Save failed** in the status line | Disk full, folder read-only, or the key file moved. | The previous file on disk is untouched. Fix the cause and select **Save** again; your data is still open in memory. |

## Running the tests

```bash
pytest
```

The suite runs without a display and covers database persistence, backups,
time handling, validation, reports, reconciliation, invoice lifecycle, CSV
exchange, the UI helpers, and the startup checks.  `python scripts/check_release.py`
runs the tests together with the compile, lint, and dependency checks used in CI.
