# ST-025 — Automated release pipeline

- **Status:** Implemented; first full run happens on the first tag
- **Priority:** P1
- **Area:** CI/CD

## User story

As a maintainer, I want builds and packaging checks to run automatically for
supported platforms when a version is released so release artifacts are complete and
consistent.

## Acceptance criteria

- [x] `.github/workflows/release.yml` triggers on `v*` tags.
- [x] The pipeline builds on both Windows and Linux using wheels-only installs.
- [x] The pipeline checks that the git tag and `version.py` agree before proceeding.
- [x] The pipeline runs the full release checks, builds, verifies, and packages before
      publishing.
- [x] The GitHub release is published with artifacts, combined checksums, and release
      notes attached automatically.
- [ ] The very first real tag-triggered run (rather than a simulated/manual run) had
      not yet occurred at time of writing.

## Implementation evidence

`.github/workflows/release.yml`.
