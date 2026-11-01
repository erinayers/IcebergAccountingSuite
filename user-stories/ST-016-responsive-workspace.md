# ST-016 — Responsive workspace

- **Status:** Implemented (structural); visual check on small screens pending
- **Priority:** P2
- **Area:** Layout

## User story

As a user on a smaller screen or resized window, I want panels and tables to adapt to
the available space so important information and actions remain visible.

## Acceptance criteria

- [x] The window/layout sizes itself relative to the available screen, with a sensible
      minimum size.
- [x] Tab content, tables, and the status bar expand to fill available space rather
      than clipping or requiring horizontal scrolling at normal sizes.
- [x] A "compact rows" preference and adjustable text size are available for small
      displays.
- [ ] Visual verification on a range of actual small-screen devices/resolutions has not
      yet been performed (structural behavior is implemented and tested, but not
      eyeballed on hardware).

## Implementation evidence

`web/app.css`, `preferences.py` (compact rows, text size).
