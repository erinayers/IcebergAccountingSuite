# ST-028 — Trusted downloads

- **Status:** Implemented
- **Priority:** P1
- **Area:** Downloads

## User story

As a user, I want the website to offer versioned downloads with supported operating
systems, release notes, and integrity checks so I can find and verify the right
package.

## Acceptance criteria

- [x] `downloads.html` is generated from `site/releases.json`, listing versions,
      OS/type per file, and SHA-256 checksums.
- [x] Each entry links to its release notes and states verification commands for the
      checksum.
- [x] A supported-systems table is present.
- [x] `scripts/publish_release_info.py` fills in checksums automatically from the
      build output (no manual copy/paste of hashes).

## Implementation evidence

`site/releases.json`, `scripts/publish_release_info.py`.
