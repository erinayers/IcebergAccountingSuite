#!/usr/bin/env python3
"""Record a release in site/releases.json from the checksum files (ST-024, ST-028).

    python scripts/publish_release_info.py --notes "What changed" [--date 2026-10-31] [--sums release/SHA256SUMS-*.txt ...]

Reads every SHA256SUMS-*.txt (by default all of them in release/), matches the
artifact names to their platform, marks this version as current and earlier
ones as previous, and rewrites site/releases.json so the downloads page shows
the real checksums.  Run it after the build on each platform (or after
downloading the CI artifacts) and commit the result.
"""

import argparse
import datetime
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from version import VERSION  # noqa: E402

RELEASES = os.path.join(ROOT, "site", "releases.json")
KINDS = [
    (r"-windows-x64-setup\.exe$", "Windows 10/11 (64-bit)", "Installer"),
    (r"-windows-x64\.zip$", "Windows 10/11 (64-bit)", "Portable archive"),
    (r"-linux-x64\.tar\.gz$", "Linux x86-64 (glibc 2.28+)", "Archive with install.sh"),
    (r"-linux-arm64\.tar\.gz$", "Linux ARM64 (glibc 2.28+)", "Archive with install.sh"),
    (r"-macos-(x64|arm64)\.zip$", "macOS", "Archive"),
]


def parse_sums(paths):
    files = []
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                parts = line.split()
                if len(parts) != 2:
                    continue
                digest, name = parts
                for pattern, os_name, kind in KINDS:
                    if re.search(pattern, name):
                        files.append({"name": name, "os": os_name, "kind": kind, "sha256": digest})
                        break
                else:
                    files.append({"name": name, "os": "", "kind": "Archive", "sha256": digest})
    files.sort(key=lambda f: (f["os"], f["kind"]))
    return files


def update(data, version, date, notes, files):
    releases = [r for r in data["releases"] if r["version"] != version]
    for release in releases:
        if release.get("status") == "current":
            release["status"] = "previous"
    releases.insert(0, {"version": version, "date": date, "status": "current", "notes": notes, "files": files})
    data["releases"] = releases
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--notes", required=True, help="one-paragraph summary for the downloads page")
    parser.add_argument("--date", default=datetime.date.today().isoformat())
    parser.add_argument("--sums", nargs="*", default=None, help="SHA256SUMS files (default: release/SHA256SUMS-*.txt)")
    parser.add_argument("--version", default=VERSION)
    args = parser.parse_args()
    sums = args.sums or sorted(glob.glob(os.path.join(ROOT, "release", "SHA256SUMS-*.txt")))
    if not sums:
        raise SystemExit("no SHA256SUMS files found; run scripts/build_release.py first")
    files = parse_sums(sums)
    with open(RELEASES, encoding="utf-8") as handle:
        data = json.load(handle)
    data = update(data, args.version, args.date, args.notes, files)
    with open(RELEASES, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    print(f"recorded {args.version} with {len(files)} file(s) in {os.path.relpath(RELEASES, ROOT)}")


if __name__ == "__main__":
    main()
