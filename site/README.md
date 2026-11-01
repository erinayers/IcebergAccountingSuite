# Website

`python site/build.py --check` renders `site/pages/*.html` through `layout.html`, generates
`downloads.html` from `releases.json`, copies screenshots from `docs/screens/`, and checks
structure, accessibility basics, and links. Output: `site/public/` (deployed to GitHub
Pages by `.github/workflows/site.yml`).

After a release, record the real checksums:

    python scripts/publish_release_info.py --notes "One-paragraph summary"

which reads `release/SHA256SUMS-*.txt` (from `scripts/build_release.py` on each platform,
or the CI artifacts) and updates `releases.json`. Commit the result.
