"""Iceberg application host.

Run with ``python webapp.py``.  ``server.ApiServer`` serves the interface and
the JSON API on a random loopback port; a native pywebview window loads it.
File and folder pickers are the only platform calls, added here so ``api.py``
stays testable without a display.  ``--browser`` opens the interface in your
default browser instead of a native window (handy on Linux without WebKitGTK).

Requirements: ``pip install pywebview`` plus a webview runtime - Edge WebView2
on Windows (bundled with Windows 10/11), WebKitGTK on Linux
(``sudo apt install gir1.2-webkit2-4.1 python3-gi``) or ``pip install
pywebview[qt]``.  See docs/WEB_INTERFACE.md.
"""

import os
import subprocess
import sys
import webbrowser

import paths
import startup_checks
from api import IcebergApi
from version import VERSION
from server import ApiServer

WINDOW_TITLE = "Iceberg Accounting Suite"


class DesktopApi(IcebergApi):
    """IcebergApi plus native dialogs.  pywebview exposes every public method
    of this object to JavaScript as ``window.pywebview.api.<name>``."""

    def __init__(self, folder=".", layout=None):
        super().__init__(folder=folder, layout=layout)
        self.window = None

    def _dialog(self, kind, **kwargs):
        """Show a native dialog.  ``path`` is None when there is no window or
        the user cancelled - that is a normal outcome, not an error."""
        if self.window is None:
            return {"ok": True, "path": None, "errors": []}
        try:
            import webview

            dialog_kind = getattr(webview, kind)
            result = self.window.create_file_dialog(dialog_kind, **kwargs)
        except Exception as error:
            return {"ok": False, "message": f"The file dialog could not be shown: {error}", "errors": []}
        if isinstance(result, (list, tuple)):
            result = result[0] if result else None
        return {"ok": True, "path": result or None, "errors": []}

    def pick_key_file(self):
        return self._dialog("OPEN_DIALOG", allow_multiple=False, file_types=("Iceberg filekey (*.icbkey)", "All files (*.*)"))

    def pick_file(self):
        return self._dialog("OPEN_DIALOG", allow_multiple=False)

    def pick_folder(self):
        return self._dialog("FOLDER_DIALOG")

    def pick_save_file(self, filename="export.csv"):
        return self._dialog("SAVE_DIALOG", save_filename=filename, file_types=("CSV (*.csv)", "All files (*.*)"))

    def open_docs(self):
        return self.open_path(self.layout.docs)

    def open_data_folder(self):
        return self.open_path(self.layout.root)

    def open_path(self, path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
            return {"ok": True, "message": "", "errors": []}
        except Exception as error:
            return {"ok": False, "message": f"Could not open {path}: {error}", "errors": []}


def main():
    if "--version" in sys.argv:
        print(f"Iceberg Accounting Suite {VERSION}")
        return
    startup_checks.change_to_app_directory()
    if "--check" in sys.argv:
        # Headless self-check used by the build script and by support: no window is opened.
        layout = paths.resolve().ensure()
        problems = startup_checks.run_startup_checks(skip_gui=True)
        startup_checks.report_problems(problems, stream=sys.stdout)
        print(f"Data folder ({layout.mode}): {layout.root}")
        print("Self-check " + ("failed" if any(p.fatal for p in problems) else "passed") + f" for Iceberg {VERSION}.")
        sys.exit(2 if any(p.fatal for p in problems) else 0)
    browser_mode = "--browser" in sys.argv
    problems = startup_checks.run_startup_checks(skip_gui=browser_mode)
    if not browser_mode:
        try:
            import importlib

            importlib.import_module("webview")
        except ImportError:
            problems.append(startup_checks.Problem(
                "pywebview is not installed",
                "The application window needs the pywebview package and a webview runtime.",
                "Run 'pip install pywebview' (Linux: also install WebKitGTK or use 'pip install pywebview[qt]'), or start with 'python webapp.py --browser'. See docs/SETUP.md.",
            ))
    if startup_checks.report_problems(problems):
        sys.exit(2)

    layout = paths.resolve().ensure()
    api = DesktopApi(layout=layout)
    api_server = ApiServer(api, layout.resources).start()
    print(f"Iceberg {VERSION} is serving on {api_server.url}", flush=True)
    print(f"Data folder ({layout.mode}): {layout.root}", flush=True)
    try:
        if browser_mode:
            webbrowser.open(api_server.url)
            print("Press Ctrl+C to stop.", flush=True)
            try:
                api_server._thread.join()
            except KeyboardInterrupt:
                pass
        else:
            import webview

            width, height = _window_size(_screen_size(webview))
            window = webview.create_window(WINDOW_TITLE, api_server.url, width=width, height=height, min_size=(1024, 700), text_select=False)
            api.window = window
            webview.start(debug="--debug" in sys.argv)
    finally:
        api.shutdown()
        api_server.stop()


def _window_size(screen, preferred=(1280, 860), minimum=(1024, 700)):
    """Fit the preferred window into the screen, never below the minimum."""
    try:
        width, height = int(screen[0]), int(screen[1])
        if width <= 0 or height <= 0:
            raise ValueError
    except (TypeError, ValueError, IndexError):
        return preferred
    return (max(minimum[0], min(preferred[0], int(width * 0.95))), max(minimum[1], min(preferred[1], int(height * 0.9))))


def _screen_size(webview):
    try:
        screen = webview.screens[0]
        return (screen.width, screen.height)
    except Exception:
        return None


if __name__ == "__main__":
    main()
