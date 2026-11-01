"""Display preferences stored next to the application (ST-020).

``preferences.json``::

    {"theme": "light", "text_scale": 1.0, "compact": false}

The web interface applies them live (a class on <body> and a CSS font-size
scale), so no restart is needed.

Values are validated on load so a hand-edited or damaged file can never stop
Iceberg from starting; anything invalid falls back to the default.
"""

import json
import os

FILE_NAME = "preferences.json"
THEMES = ("light", "dark", "high-contrast")
TEXT_SCALES = (0.85, 1.0, 1.15, 1.3, 1.5)
TEXT_SCALE_LABELS = {0.85: "Smaller", 1.0: "Default", 1.15: "Larger", 1.3: "Large", 1.5: "Extra large"}

DEFAULTS = {"theme": "light", "text_scale": 1.0, "compact": False}


def normalize(raw):
    """Return a complete, valid preference dict built from ``raw``."""
    prefs = dict(DEFAULTS)
    if not isinstance(raw, dict):
        return prefs
    theme = str(raw.get("theme", prefs["theme"])).strip().lower()
    if theme in THEMES:
        prefs["theme"] = theme
    try:
        scale = float(raw.get("text_scale", prefs["text_scale"]))
        prefs["text_scale"] = min(TEXT_SCALES, key=lambda s: abs(s - scale))
    except (TypeError, ValueError):
        pass
    prefs["compact"] = bool(raw.get("compact", prefs["compact"]))
    return prefs


def path(directory=None):
    return os.path.join(directory or os.getcwd(), FILE_NAME)


def load(directory=None):
    try:
        with open(path(directory), "r", encoding="utf-8") as handle:
            return normalize(json.load(handle))
    except (OSError, ValueError):
        return dict(DEFAULTS)


def save(prefs, directory=None):
    prefs = normalize(prefs)
    target = path(directory)
    temp = target + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(prefs, handle, indent=2, sort_keys=True)
    os.replace(temp, target)
    return prefs


def scale_label(scale):
    return TEXT_SCALE_LABELS.get(scale, f"{scale:g}x")


def scale_from_label(label):
    for scale, name in TEXT_SCALE_LABELS.items():
        if name == label:
            return scale
    return DEFAULTS["text_scale"]
