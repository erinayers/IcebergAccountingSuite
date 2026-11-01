"""The visual system: palettes, type scale, spacing (ST-014, ST-020, ST-011).

Every layout reads its colours and font sizes from a ``Theme`` instance so
the whole application changes together.  Palettes are checked against WCAG
contrast ratios in the tests (see ``contrast_ratio``).
"""

FONT_FAMILY = "Helvetica"
MONO_FAMILY = "Courier"

BASE_SIZES = {"small": 9, "medium": 11, "large": 15, "xlarge": 22}

PALETTES = {
    # PySimpleGUI base theme plus the two information backgrounds used on
    # detail panels, the text colour, and the feedback colours.
    "light": {
        "sg_theme": "LightBlue3",
        "text": "#102a43",
        "background": "#f0f6fa",
        "panel": "#dcfffe",
        "panel_alt": "#bbf0f9",
        "table_bg": "#ffffff",
        "table_alt": "#eef6fb",
        "table_text": "#102a43",
        "accent": "#1f5f8b",
        "accent_text": "#ffffff",
        "nav_active": "#1f5f8b",
        "nav_active_text": "#ffffff",
        "nav_inactive": "#d9e8f2",
        "nav_inactive_text": "#102a43",
        "success": "#1e6b3a",
        "error": "#9b1c1c",
        "warning": "#8a5a00",
        "info": "#1f5f8b",
        "feedback_bg": "#ffffff",
        "field_error_bg": "#fde2e2",
        "field_bg": "#ffffff",
    },
    "dark": {
        "sg_theme": "DarkGrey13",
        "text": "#f1f5f9",
        "background": "#1e293b",
        "panel": "#243447",
        "panel_alt": "#2c3e55",
        "table_bg": "#0f172a",
        "table_alt": "#1e293b",
        "table_text": "#f1f5f9",
        "accent": "#7cc4fa",
        "accent_text": "#0f172a",
        "nav_active": "#7cc4fa",
        "nav_active_text": "#0f172a",
        "nav_inactive": "#334155",
        "nav_inactive_text": "#f1f5f9",
        "success": "#86efac",
        "error": "#fca5a5",
        "warning": "#fcd34d",
        "info": "#7cc4fa",
        "feedback_bg": "#0f172a",
        "field_error_bg": "#7f1d1d",
        "field_bg": "#0f172a",
    },
    "high-contrast": {
        "sg_theme": "Black",
        "text": "#ffffff",
        "background": "#000000",
        "panel": "#000000",
        "panel_alt": "#1a1a1a",
        "table_bg": "#000000",
        "table_alt": "#1a1a1a",
        "table_text": "#ffffff",
        "accent": "#ffff00",
        "accent_text": "#000000",
        "nav_active": "#ffff00",
        "nav_active_text": "#000000",
        "nav_inactive": "#000000",
        "nav_inactive_text": "#ffffff",
        "success": "#00ff7f",
        "error": "#ff6b6b",
        "warning": "#ffd700",
        "info": "#7fdbff",
        "feedback_bg": "#000000",
        "field_error_bg": "#660000",
        "field_bg": "#000000",
    },
}

SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 20}


class Theme:
    def __init__(self, name="light", text_scale=1.0, compact=False):
        if name not in PALETTES:
            name = "light"
        self.name = name
        self.colors = dict(PALETTES[name])
        self.text_scale = float(text_scale)
        self.compact = bool(compact)
        self.sizes = {key: max(7, round(size * self.text_scale)) for key, size in BASE_SIZES.items()}
        self.row_height = max(20, round((26 if compact else 34) * self.text_scale))
        self.pad = dict(SPACING)
        if compact:
            self.pad = {k: max(1, v // 2) for k, v in SPACING.items()}

    # ---- fonts
    def font(self, size="medium", bold=False, mono=False):
        family = MONO_FAMILY if mono else FONT_FAMILY
        return (family, self.sizes[size], "bold") if bold else (family, self.sizes[size])

    @property
    def small(self):
        return self.sizes["small"]

    @property
    def medium(self):
        return self.sizes["medium"]

    @property
    def large(self):
        return self.sizes["large"]

    @property
    def xlarge(self):
        return self.sizes["xlarge"]

    def color(self, key):
        return self.colors[key]

    def apply(self, sg):
        """Set PySimpleGUI global options.  Must run before layouts are built."""
        sg.theme(self.colors["sg_theme"])
        sg.set_options(font=self.font("medium"), element_padding=(self.pad["sm"], self.pad["xs"]))

    def window_size(self, screen_size, preferred=(1280, 980), minimum=(1024, 720)):
        """Fit the preferred window into the screen, never below the minimum (ST-016)."""
        try:
            width, height = int(screen_size[0]), int(screen_size[1])
            if width <= 0 or height <= 0:
                raise ValueError
        except (TypeError, ValueError, IndexError):
            return preferred
        usable_w, usable_h = int(width * 0.95), int(height * 0.90)
        w = max(minimum[0], min(preferred[0], usable_w))
        h = max(minimum[1], min(preferred[1], usable_h))
        return w, h


def from_preferences(prefs):
    return Theme(prefs.get("theme", "light"), prefs.get("text_scale", 1.0), prefs.get("compact", False))


# ------------------------------------------------------------------ contrast


def _linear(channel):
    channel /= 255.0
    return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color):
    value = hex_color.lstrip("#")
    r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def contrast_ratio(foreground, background):
    """WCAG 2.x contrast ratio; 4.5 is the AA threshold for normal text."""
    l1, l2 = relative_luminance(foreground), relative_luminance(background)
    light, dark = max(l1, l2), min(l1, l2)
    return (light + 0.05) / (dark + 0.05)


def contrast_report(palette):
    """Return {pair_name: ratio} for the text/background pairs a user reads."""
    pairs = {
        "text on background": ("text", "background"),
        "text on panel": ("text", "panel"),
        "text on panel_alt": ("text", "panel_alt"),
        "table text on table_bg": ("table_text", "table_bg"),
        "table text on table_alt": ("table_text", "table_alt"),
        "accent text on accent": ("accent_text", "accent"),
        "nav active": ("nav_active_text", "nav_active"),
        "nav inactive": ("nav_inactive_text", "nav_inactive"),
        "success on feedback_bg": ("success", "feedback_bg"),
        "error on feedback_bg": ("error", "feedback_bg"),
        "warning on feedback_bg": ("warning", "feedback_bg"),
        "info on feedback_bg": ("info", "feedback_bg"),
        "text on field_error_bg": ("text", "field_error_bg"),
    }
    return {name: contrast_ratio(palette[fg], palette[bg]) for name, (fg, bg) in pairs.items()}
