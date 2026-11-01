# ST-023 — User data locations

- **Status:** Implemented
- **Priority:** P1
- **Area:** Data Locations

## User story

As a user installing a packaged build, I want databases, encryption keys, logs, and
receipts stored in clearly documented user-selected or application data locations so
upgrades do not overwrite or scatter my files.

## Acceptance criteria

- [x] `paths.py` defines a per-user data folder for installed builds
      (`%LOCALAPPDATA%\Iceberg` on Windows, `~/.local/share/iceberg` on Linux).
- [x] A portable mode exists for source checkouts (or via a `portable.txt` marker) that
      keeps data next to the code.
- [x] A `--data-dir` flag / `ICEBERG_DATA_DIR` environment variable can override the
      location.
- [x] Databases, backups, logs, and preferences each have a documented, predictable
      sub-location.
- [x] Tools → Where are my files surfaces the actual resolved paths to the user.
- [x] Covered by `tests/test_paths.py`.

## Implementation evidence

`paths.py`, `tests/test_paths.py`.
