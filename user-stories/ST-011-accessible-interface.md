# ST-011 — Accessible interface

- **Status:** Implemented (Tk in 1.4; carried forward to the web interface in 2.0);
  needs a screen-reader pass on a real desktop
- **Priority:** P2
- **Area:** Accessibility

## User story

As a keyboard or screen-reader user, I want predictable focus order, readable
contrast, and keyboard access to common actions so I can use the app efficiently.

## Acceptance criteria

- [x] A documented set of keyboard shortcuts covers navigation and common actions
      (originally `ui/accessibility.py` in Tk: Ctrl+N/S/O/I/F, Ctrl+1-8, F1, Ctrl+,); a
      Help/Tools dialog lists them, generated from the same source as the actual
      bindings.
- [x] Every form focuses its first field on open and submits on Enter.
- [x] All color palettes (light/dark/high-contrast) meet WCAG AA contrast (≥4.5:1),
      verified by `tests/test_ui.py::TestTheme`.
- [x] These behaviors are carried forward into the 2.0 web interface
      (`docs/UI_GUIDE.md`, `docs/WEB_INTERFACE.md`).
- [ ] A screen-reader pass on a real Windows/Linux desktop (not just automated
      contrast/structure checks) has not yet been performed.

## Implementation evidence

`docs/UI_GUIDE.md`, `docs/WEB_INTERFACE.md`, `tests/test_ui.py::TestTheme`.
