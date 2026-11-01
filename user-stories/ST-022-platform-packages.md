# ST-022 — Platform packages

- **Status:** Implemented; Windows installer build needs a Windows run to verify
- **Priority:** P1
- **Area:** Packaging

## User story

As a user, I want an installable package for each supported operating system so I can
install and launch Iceberg without setting up Python or pip dependencies myself.

## Acceptance criteria

- [x] A Windows Inno Setup installer (`packaging/windows/iceberg.iss`) and a portable
      zip are produced.
- [x] A Linux tar.gz archive with `install.sh`/`uninstall.sh` and a desktop entry is
      produced.
- [x] macOS is explicitly documented as from-source-only, not silently unsupported.
- [ ] The Windows installer build has not yet been exercised on an actual Windows
      CI/build machine (verified in principle via the spec/script, not yet via a live
      Windows run at the time of writing).

## Implementation evidence

`packaging/windows/iceberg.iss`, `packaging/linux/`.
