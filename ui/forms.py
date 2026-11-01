"""Focused data-entry forms (ST-019).

* ``section`` groups related fields under a titled frame.
* ``label`` renders a field label, marking required fields with an asterisk.
* ``legend`` explains the asterisk once per form.
* ``message_row`` / ``show_errors`` display validation problems *inside* the
  form, next to the Submit button, and ``mark_invalid`` colours the offending
  fields so the user sees where to look.  ``FIELD_MAP`` connects validation
  field names to element keys.
"""

REQUIRED_MARK = "*"


def label(sg, theme, text, required=False, width=20):
    suffix = f" {REQUIRED_MARK}" if required else ""
    return sg.Text(f"{text}{suffix}", size=(width, 1), font=theme.font("medium", bold=required))


def legend(sg, theme):
    return sg.Text(f"{REQUIRED_MARK} required", font=theme.font("small"), text_color=theme.color("info"))


def section(sg, theme, title, rows, key=None):
    return sg.Frame(title, rows, font=theme.font("medium", bold=True), pad=(theme.pad["sm"], theme.pad["md"]),
                    expand_x=True, key=key, relief="groove")


def message_row(sg, theme, key):
    """A multi-line text area for inline validation feedback."""
    return [sg.Text("", key=key, size=(90, 3), font=theme.font("small"), text_color=theme.color("error"))]


def field_keys(field_map, fields):
    return [field_map[f] for f in fields if f in field_map]


def show_errors(window, theme, message_key, result, field_map=None):
    """Write validation errors/warnings into the form and highlight fields.

    Returns True when there are no blocking errors.
    """
    lines = [f"\u2716 {e}" for e in result.errors] + [f"\u26a0 {w}" for w in result.warnings]
    try:
        window[message_key].update("\n".join(lines[:3]) if lines else "",
                                   text_color=theme.color("error" if result.errors else "warning"))
    except Exception:
        pass
    if field_map:
        clear_marks(window, theme, field_map.values())
        mark_invalid(window, theme, field_keys(field_map, result.error_fields()))
    return result.ok


def mark_invalid(window, theme, keys):
    for key in keys:
        try:
            window[key].update(background_color=theme.color("field_error_bg"))
        except Exception:
            pass


def clear_marks(window, theme, keys):
    for key in keys:
        try:
            window[key].update(background_color=theme.color("field_bg"))
        except Exception:
            pass


def clear_message(window, message_key):
    try:
        window[message_key].update("")
    except Exception:
        pass
