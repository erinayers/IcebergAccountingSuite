"""Contextual action feedback and unsaved-change state (ST-018).

A status bar sits between the workspace and the console.  ``notify`` writes
the outcome of the action the user just performed (success, error, warning,
info, working) with a matching colour and also appends it to the console
log, which is the permanent record.  ``save_state_text`` produces the
"Unsaved changes - autosave in 4:12" / "All changes saved 14:52" label.
"""

LEVELS = ("success", "error", "warning", "info", "working")
ICONS = {"success": "\u2713", "error": "\u2716", "warning": "\u26a0", "info": "\u2139", "working": "\u23f3"}


def build_status_bar(sg, theme):
    return [
        sg.Text("", key="-Status_Message-", font=theme.font("medium"), text_color=theme.color("info"),
                background_color=theme.color("feedback_bg"), expand_x=True, pad=(theme.pad["md"], theme.pad["xs"])),
        sg.Text("", key="-Save_State-", font=theme.font("medium"), text_color=theme.color("info"),
                background_color=theme.color("feedback_bg"), justification="right", pad=(theme.pad["md"], theme.pad["xs"])),
    ]


def notify(window, theme, message, level="info"):
    """Show ``message`` in the status bar coloured by ``level``."""
    if level not in LEVELS:
        level = "info"
    color_key = "info" if level == "working" else level
    text = f"{ICONS[level]} {message}"
    try:
        window["-Status_Message-"].update(text, text_color=theme.color(color_key))
        if level == "working":
            window.refresh()
    except Exception:
        pass
    return text


def format_countdown(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def save_state_text(database_loaded, unsaved, last_saved_display, seconds_to_autosave):
    if not database_loaded:
        return "No database open"
    if unsaved:
        return f"Unsaved changes \u00b7 autosave in {format_countdown(seconds_to_autosave)} \u00b7 Ctrl+S to save now"
    if last_saved_display:
        return f"All changes saved {last_saved_display}"
    return "No unsaved changes"


def update_save_state(window, theme, text, unsaved):
    try:
        window["-Save_State-"].update(text, text_color=theme.color("warning" if unsaved else "success"))
    except Exception:
        pass
