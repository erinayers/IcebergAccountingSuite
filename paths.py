"""Where Iceberg keeps its files (ST-023).

Two modes:

* **user** (packaged builds): everything lives in the per-user data folder -
  ``%LOCALAPPDATA%\\Iceberg`` on Windows, ``~/.local/share/iceberg`` on Linux,
  ``~/Library/Application Support/Iceberg`` on macOS - so upgrades that
  replace the program folder never touch your books.
* **portable** (running from a source checkout, or a ``portable.txt`` marker
  next to the program): files stay next to the program, as in earlier versions.

Either way the layout is::

    <root>/databases/        encrypted books (.icb)          [portable: <root>/]
    <root>/backups/<name>/   timestamped backups
    <root>/logs/iceberg.log  console log
    <root>/preferences.json  display preferences
    <root>/sessions.icbs(+key)  session console log

Filekeys (.icbkey) and the receipts folder are always where the user chose
to put them.  ``--data-dir PATH`` or ``ICEBERG_DATA_DIR`` overrides the root.
"""

import os
import sys

APP_NAME = "Iceberg"
PORTABLE_MARKER = "portable.txt"


def app_directory():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def resource_directory():
    """Where bundled resources (web/, fonts/, docs/) live; PyInstaller puts them in _MEIPASS or _internal."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None)
        if base and os.path.isdir(os.path.join(base, "web")):
            return base
        internal = os.path.join(app_directory(), "_internal")
        if os.path.isdir(os.path.join(internal, "web")):
            return internal
    return app_directory()


def default_user_data_dir(platform=None, environ=None, home=None):
    platform = platform or sys.platform
    environ = os.environ if environ is None else environ
    home = home or os.path.expanduser("~")
    if platform.startswith("win"):
        base = environ.get("LOCALAPPDATA") or environ.get("APPDATA") or os.path.join(home, "AppData", "Local")
        return os.path.join(base, APP_NAME)
    if platform == "darwin":
        return os.path.join(home, "Library", "Application Support", APP_NAME)
    base = environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    return os.path.join(base, APP_NAME.lower())


def is_portable(app_dir=None, frozen=None):
    app_dir = app_dir or app_directory()
    frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    if os.path.isfile(os.path.join(app_dir, PORTABLE_MARKER)):
        return True
    return not frozen  # a source checkout keeps its files next to the code


def data_root(argv=None, environ=None, app_dir=None, frozen=None):
    """Resolve the data root: --data-dir, then ICEBERG_DATA_DIR, then mode default."""
    argv = sys.argv[1:] if argv is None else argv
    environ = os.environ if environ is None else environ
    app_dir = app_dir or app_directory()
    for i, arg in enumerate(argv):
        if arg.startswith("--data-dir="):
            return os.path.abspath(os.path.expanduser(arg.split("=", 1)[1])), "custom"
        if arg == "--data-dir" and i + 1 < len(argv):
            return os.path.abspath(os.path.expanduser(argv[i + 1])), "custom"
    if environ.get("ICEBERG_DATA_DIR"):
        return os.path.abspath(os.path.expanduser(environ["ICEBERG_DATA_DIR"])), "custom"
    if is_portable(app_dir, frozen):
        return app_dir, "portable"
    return default_user_data_dir(environ=environ), "user"


class Layout:
    """Resolved folder layout.  ``ensure()`` creates the folders."""

    def __init__(self, root, mode="user", app_dir=None, resources=None):
        self.root = os.path.abspath(root)
        self.mode = mode
        self.app = app_dir or app_directory()
        self.resources = resources or resource_directory()
        self.databases = self.root if mode == "portable" else os.path.join(self.root, "databases")
        self.backups = os.path.join(self.root, "backups")
        self.logs = os.path.join(self.root, "logs")
        self.log_file = os.path.join(self.logs, "iceberg.log")
        self.preferences_dir = self.root
        self.session_log_dir = self.root
        self.fonts = os.path.join(self.resources, "fonts")
        self.docs = os.path.join(self.resources, "docs")
        self.web = os.path.join(self.resources, "web")

    def ensure(self):
        for folder in (self.root, self.databases, self.backups, self.logs):
            os.makedirs(folder, exist_ok=True)
        return self

    def describe(self):
        return {
            "mode": self.mode,
            "root": self.root,
            "databases": self.databases,
            "backups": self.backups,
            "logs": self.logs,
            "log_file": self.log_file,
            "preferences": os.path.join(self.preferences_dir, "preferences.json"),
            "program": self.app,
        }


def resolve(argv=None, environ=None, app_dir=None, frozen=None):
    root, mode = data_root(argv, environ, app_dir, frozen)
    return Layout(root, mode, app_dir=app_dir)
