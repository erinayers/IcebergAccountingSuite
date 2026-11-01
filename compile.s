#!/usr/bin/env bash
# One-command build for Linux/macOS (ST-021): creates the virtual environment if
# needed, installs the pinned dependencies, then builds, verifies, and packages Iceberg.
#   ./compile.s
set -e
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python scripts/build_release.py || { echo "Build failed - see the messages above."; exit 1; }
echo "Artifacts are in ./release"
