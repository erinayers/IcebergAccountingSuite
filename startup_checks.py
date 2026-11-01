"""Pre-flight checks that turn setup problems into actionable messages (ST-002).

``run_startup_checks()`` is called by ``webapp.py`` before the window is
created.  It verifies the interpreter version, the webview host (pywebview
and its platform runtime), the other required packages, optional external
tools, and the data files the application needs.  Each problem is returned as a ``Problem``
with a plain-language explanation and a fix, so a user never has to interpret
a traceback to get the application running.

The module deliberately imports nothing heavy at module level so it can run
even when the rest of the environment is broken.
"""

import importlib
import importlib.util
import os
import platform
import sys

SUPPORTED_PYTHON = ((3, 11), (3, 14))  # inclusive range of (major, minor)
DOCS_SETUP = "docs/SETUP.md"

REQUIRED_MODULES = [
    # (module name, pip package, what it is used for)
    ("cryptography", "cryptography", "encrypting and decrypting your database files"),
    ("dateutil", "python-dateutil", "parsing dates"),
    ("PIL", "pillow", "building invoice images"),
    ("img2pdf", "img2pdf", "converting invoices to PDF"),
]

REQUIRED_FILES = [
    ("web/index.html", "the application window"),
    ("web/app.css", "the application styling"),
    ("web/routes.js", "the API route table"),
    ("web/client.js", "the API client"),
    ("web/render.js", "the application screens"),
    ("web/app.js", "the application behaviour"),
    ("fonts/LiberationSerif-Regular.ttf", "the font used to print invoices"),
]


class Problem:
    """One startup issue.  ``fatal`` problems stop the launch."""

    def __init__(self, title, detail, fix, fatal=True):
        self.title = title
        self.detail = detail
        self.fix = fix
        self.fatal = fatal

    def __str__(self):
        level = "ERROR" if self.fatal else "WARNING"
        return f"[{level}] {self.title}\n    {self.detail}\n    How to fix: {self.fix}"


# ------------------------------------------------------------------ locations


def app_directory():
    """Folder containing the application (source checkout or frozen binary)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def change_to_app_directory():
    """Make relative paths (``./sessions.icbs``, ``./fonts``) resolve correctly.

    Iceberg keeps its data files next to the program.  Launching it from
    another folder (a shortcut, a terminal opened elsewhere) used to fail with
    ``FileNotFoundError``; running from the application folder avoids that.
    """
    directory = app_directory()
    os.chdir(directory)
    return directory


# --------------------------------------------------------------------- checks


def python_version_problem(version_info=None):
    version_info = version_info or sys.version_info
    low, high = SUPPORTED_PYTHON
    current = (version_info[0], version_info[1])
    label = f"{current[0]}.{current[1]}"
    supported = f"{low[0]}.{low[1]} through {high[0]}.{high[1]}"
    if current < low:
        return Problem(
            f"Python {label} is too old",
            f"Iceberg supports Python {supported}.",
            f"Install a supported Python from https://www.python.org/downloads/ and recreate the virtual environment (see {DOCS_SETUP}).",
        )
    if current > high:
        return Problem(
            f"Python {label} is not supported yet",
            f"Iceberg supports Python {supported}. Newer releases may lack prebuilt wheels for some pinned dependencies, so 'pip install -r requirements.txt' could try to compile them and fail without a C compiler.",
            f"Install Python {high[0]}.{high[1]} alongside your current version and create the virtual environment with it (see {DOCS_SETUP}).",
            fatal=False,
        )
    return None


def _webview_runtime_hint():
    system = platform.system()
    if system == "Windows":
        return "Install the Microsoft Edge WebView2 Runtime (it ships with Windows 10/11; download it from Microsoft if the window is blank)."
    if system == "Darwin":
        return "No extra runtime is needed on macOS; reinstall pywebview with 'pip install pywebview'."
    return ("Install WebKitGTK for Python: 'sudo apt install gir1.2-webkit2-4.1 python3-gi' (Debian/Ubuntu) or "
            "'sudo dnf install webkit2gtk4.1 python3-gobject' (Fedora), or use 'pip install pywebview[qt]'.")


def webview_problem():
    """pywebview must import; on Linux a GUI backend must also be present."""
    try:
        importlib.import_module("webview")
    except ImportError as error:
        return Problem(
            "pywebview is not installed",
            f"The application window is hosted by pywebview, which could not be imported ({error}).",
            f"Activate the virtual environment and run 'pip install -r requirements.txt'. {_webview_runtime_hint()} See {DOCS_SETUP}.",
        )
    if platform.system() == "Linux":
        have_gtk = importlib.util.find_spec("gi") is not None
        have_qt = any(importlib.util.find_spec(name) is not None for name in ("PyQt6", "PyQt5", "PySide6", "PySide2"))
        if not (have_gtk or have_qt):
            return Problem(
                "No webview backend is installed",
                "pywebview needs WebKitGTK (python3-gi) or Qt WebEngine to show a window on Linux.",
                _webview_runtime_hint(),
            )
    return None


def required_module_problems(modules=None):
    problems = []
    for module, package, purpose in modules or REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except ImportError as error:
            problems.append(
                Problem(
                    f"Missing package: {package}",
                    f"'{module}' is needed for {purpose} ({error}).",
                    "Activate the virtual environment and run 'pip install -r requirements.txt'.",
                )
            )
    return problems


def data_file_problems(base_dir=None, files=None):
    if base_dir is None:
        import paths

        base_dir = paths.resource_directory()
    problems = []
    for relative, purpose in files or REQUIRED_FILES:
        path = os.path.join(base_dir, relative)
        if not os.path.isfile(path):
            problems.append(
                Problem(
                    f"Missing file: {relative}",
                    f"Expected {path}; it provides {purpose}.",
                    "Restore the file from the Iceberg download or repository. The application folder must keep its original layout.",
                )
            )
    return problems


def session_log_problem(base_dir=None):
    """The session log (sessions.icbs) is recreated if missing, but a database
    without its key is a sign of a damaged folder."""
    base_dir = base_dir or app_directory()
    db_path = os.path.join(base_dir, "sessions.icbs")
    key_path = os.path.join(base_dir, "sessions.icbskey")
    has_db, has_key = os.path.isfile(db_path), os.path.isfile(key_path)
    if has_db and not has_key:
        return Problem(
            "sessions.icbskey is missing",
            f"{db_path} exists but its key file does not, so the session log cannot be decrypted.",
            "Delete or move sessions.icbs and Iceberg will create a fresh session log on the next launch (the file only contains console messages).",
        )
    return None


def run_startup_checks(skip_gui=False):
    """Run every check and return the list of ``Problem`` objects found."""
    problems = []
    version = python_version_problem()
    if version:
        problems.append(version)
    if not skip_gui:
        gui = webview_problem()
        if gui:
            problems.append(gui)
    problems.extend(required_module_problems())
    problems.extend(data_file_problems())
    session = session_log_problem()
    if session:
        problems.append(session)
    return problems


# ------------------------------------------------------------------ reporting


def format_report(problems):
    lines = [
        "Iceberg Accounting Suite could not start cleanly.",
        f"Python {platform.python_version()} on {platform.system()} {platform.release()}",
        "",
    ]
    for problem in problems:
        lines.append(str(problem))
        lines.append("")
    lines.append(f"Setup guide: {DOCS_SETUP}")
    return "\n".join(lines)


def show_message_box(title, text):
    """Best-effort native dialog so double-click launches still show errors."""
    try:
        if platform.system() == "Windows":
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, text, title, 0x10)
            return True
        import tkinter
        from tkinter import messagebox

        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror(title, text)
        root.destroy()
        return True
    except Exception:
        return False


def report_problems(problems, stream=None, dialog=None):
    """Print problems (and show a dialog when possible).  Returns True if fatal."""
    stream = stream or sys.stderr
    if not problems:
        return False
    fatal = [problem for problem in problems if problem.fatal]
    text = format_report(problems)
    print(text, file=stream)
    if fatal and (dialog if dialog is not None else stream is sys.stderr):
        show_message_box("Iceberg Accounting Suite - setup problem", text)
    return bool(fatal)


def ensure_ready_or_exit():
    """Run checks and exit on fatal errors (used by ``webapp.py``)."""
    change_to_app_directory()
    problems = run_startup_checks()
    if report_problems(problems):
        sys.exit(2)
    return problems


if __name__ == "__main__":
    change_to_app_directory()
    found = run_startup_checks()
    if found:
        report_problems(found, stream=sys.stdout)
        sys.exit(2 if any(p.fatal for p in found) else 0)
    print("All startup checks passed.")
