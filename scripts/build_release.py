#!/usr/bin/env python3
"""One-command build and packaging (ST-021, ST-022, ST-024).

    python scripts/build_release.py            # build with PyInstaller, then package
    python scripts/build_release.py --package  # package an existing dist/Iceberg only
    python scripts/build_release.py --verify   # run the built program's self-check

Produces, in release/:
    Iceberg-<version>-windows-x64.zip | Iceberg-<version>-linux-x64.tar.gz | ...-macos.zip
    Iceberg-<version>-windows-x64-setup.exe   (Windows, when Inno Setup's ISCC is on PATH)
    RELEASE_NOTES.md                           (this version's section of CHANGELOG.md)
    SHA256SUMS.txt                             (checksums of every artifact)
"""

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from version import VERSION  # noqa: E402

DIST = os.path.join(ROOT, "dist", "Iceberg")
RELEASE = os.path.join(ROOT, "release")


def platform_tag():
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = "x64" if machine in ("amd64", "x86_64") else ("arm64" if machine in ("arm64", "aarch64") else machine)
    name = {"windows": "windows", "linux": "linux", "darwin": "macos"}.get(system, system)
    return f"{name}-{arch}"


def executable():
    return os.path.join(DIST, "Iceberg.exe" if platform.system() == "Windows" else "Iceberg")


SPEC = os.path.join(ROOT, "packaging", "iceberg.spec")
REQUIRED_FOR_BUILD = [SPEC, os.path.join(ROOT, "packaging", "iceberg.ico"), os.path.join(ROOT, "packaging", "iceberg-256.png"),
                      os.path.join(ROOT, "web", "index.html"), os.path.join(ROOT, "fonts", "LiberationSerif-Regular.ttf"),
                      os.path.join(ROOT, "LICENSE"), os.path.join(ROOT, "CHANGELOG.md"), os.path.join(ROOT, "version.py")]


def check_inputs():
    missing = [os.path.relpath(p, ROOT) for p in REQUIRED_FOR_BUILD if not os.path.isfile(p)]
    if missing:
        raise SystemExit("Cannot build: these files are missing from your copy of the project:\n  " + "\n  ".join(missing) +
                         "\nUpdate the checkout (git pull) or re-extract the release archive, then run the build again.")


def build():
    print("=== PyInstaller build")
    check_inputs()
    shutil.rmtree(os.path.join(ROOT, "build", "Iceberg"), ignore_errors=True)
    shutil.rmtree(DIST, ignore_errors=True)
    result = subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", os.path.join(ROOT, "dist"),
                             "--workpath", os.path.join(ROOT, "build"), SPEC], cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"PyInstaller failed (exit code {result.returncode}); see the messages above.")
    if not os.path.isfile(executable()):
        raise SystemExit(f"build did not produce {executable()}")
    for name in ("install.sh", "uninstall.sh", "iceberg.desktop"):
        if platform.system() != "Windows":
            shutil.copy(os.path.join(ROOT, "packaging", "linux", name), DIST)
    shutil.copy(os.path.join(ROOT, "packaging", "iceberg-256.png"), DIST)
    print(f"built {executable()}")


def verify():
    print("=== Verify the built program")
    result = subprocess.run([executable(), "--version"], capture_output=True, text=True, timeout=120)
    print(result.stdout.strip() or result.stderr.strip())
    if result.returncode != 0 or VERSION not in result.stdout:
        raise SystemExit("the built program did not report its version")
    result = subprocess.run([executable(), "--check"], capture_output=True, text=True, timeout=120)
    print(result.stdout.strip() or result.stderr.strip())
    if result.returncode != 0:
        raise SystemExit("the built program's self-check failed")


def release_notes():
    with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as handle:
        text = handle.read()
    marker = f"## {VERSION}"
    if marker not in text:
        raise SystemExit(f"CHANGELOG.md has no section for {VERSION}")
    section = text.split(marker, 1)[1]
    section = section.split("\n## ", 1)[0].strip()
    return f"# Iceberg Accounting Suite {VERSION}\n\n{section}\n"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package():
    print("=== Package")
    if not os.path.isfile(executable()):
        raise SystemExit("nothing to package: run the build first")
    os.makedirs(RELEASE, exist_ok=True)
    tag = platform_tag()
    artifacts = []
    if platform.system() == "Windows":
        archive = os.path.join(RELEASE, f"Iceberg-{VERSION}-{tag}.zip")
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for base, _, files in os.walk(DIST):
                for name in files:
                    full = os.path.join(base, name)
                    zf.write(full, os.path.join("Iceberg", os.path.relpath(full, DIST)))
        artifacts.append(archive)
        iscc = shutil.which("iscc") or shutil.which("ISCC")
        if iscc:
            subprocess.run([iscc, f"/DAppVersion={VERSION}", f"/DDistDir={DIST}", os.path.join(ROOT, "packaging", "windows", "iceberg.iss")], check=True)
            artifacts.append(os.path.join(RELEASE, f"Iceberg-{VERSION}-{tag}-setup.exe"))
        else:
            print("Inno Setup (ISCC) not found: installer skipped, zip archive only")
    else:
        archive = os.path.join(RELEASE, f"Iceberg-{VERSION}-{tag}.tar.gz")
        with tarfile.open(archive, "w:gz") as tf:
            tf.add(DIST, arcname="Iceberg")
        artifacts.append(archive)
    notes = os.path.join(RELEASE, "RELEASE_NOTES.md")
    with open(notes, "w", encoding="utf-8") as handle:
        handle.write(release_notes())
    sums = os.path.join(RELEASE, f"SHA256SUMS-{tag}.txt")
    with open(sums, "w", encoding="utf-8") as handle:
        for path in artifacts:
            handle.write(f"{sha256(path)}  {os.path.basename(path)}\n")
    for path in artifacts + [notes, sums]:
        print(f"{os.path.getsize(path):>12,} bytes  {os.path.relpath(path, ROOT)}")
    return artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--package", action="store_true", help="package an existing build without rebuilding")
    parser.add_argument("--verify", action="store_true", help="run the built program's --version and --check")
    parser.add_argument("--no-verify", action="store_true", help="skip the verification step after building")
    args = parser.parse_args()
    print(f"Iceberg {VERSION} on {platform_tag()}")
    if args.verify:
        verify()
        return
    if not args.package:
        build()
        if not args.no_verify:
            verify()
    package()


if __name__ == "__main__":
    main()
