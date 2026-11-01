# ST-014 — Consistent visual system

- **Status:** Implemented (originally Tk in 1.4; now delivered on the 2.0 web stack)
- **Priority:** P2
- **Area:** Visual Design

## User story

As a user, I want consistent typography, spacing, colors, and controls across every
screen so the app feels coherent and easier to learn.

## Acceptance criteria

- [x] A single theme/style source defines palettes, a type scale, spacing, and row
      heights used by every screen.
- [x] Tables share consistent alternating-row styling, bold headers, and
      right-aligned money columns across the whole app.
- [x] No screen hand-rolls its own colors or spacing outside the shared theme.
- [x] Delivered on the 2.0 web stack per `docs/WEB_INTERFACE.md` and
      `docs/UI_GUIDE.md`.

## Implementation evidence

`docs/WEB_INTERFACE.md`, `docs/UI_GUIDE.md`, `web/app.css`.
