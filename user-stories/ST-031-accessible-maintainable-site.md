# ST-031 — Accessible, maintainable site

- **Status:** Implemented
- **Priority:** P1
- **Area:** Site Accessibility

## User story

As a visitor, I want the site to work on mobile and desktop with accessible
navigation and readable content so I can use it on my preferred device.

## Acceptance criteria

- [x] One shared layout plus page fragments are built by `site/build.py` (not
      copy-pasted per-page HTML).
- [x] A skip link, labelled navigation with `aria-current`, a single h1 per page, and
      alt text on images are present.
- [x] Focus styles and reduced-motion support are present; a mobile breakpoint is
      implemented.
- [x] `site/build.py --check` validates structure and links; covered by
      `tests/test_site.py`.
- [x] Deployed automatically by `.github/workflows/site.yml`.

## Implementation evidence

`site/build.py`, `site/layout.html`, `tests/test_site.py`,
`.github/workflows/site.yml`.
