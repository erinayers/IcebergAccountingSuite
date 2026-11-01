import hashlib
import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)


def load_script():
    spec = importlib.util.spec_from_file_location("build_release", os.path.join(ROOT, "scripts", "build_release.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestBuildRelease(unittest.TestCase):
    def test_version_is_consistent_everywhere(self):
        from version import VERSION
        import api
        self.assertEqual(api.VERSION, VERSION)
        with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as handle:
            self.assertIn(f"## {VERSION}", handle.read())
        self.assertRegex(VERSION, r"^\d+\.\d+\.\d+$")

    def test_release_notes_are_the_current_section(self):
        script = load_script()
        notes = script.release_notes()
        self.assertTrue(notes.startswith(f"# Iceberg Accounting Suite {script.VERSION}"))
        self.assertIn("Upgrade notes", notes)
        self.assertNotIn("\n## ", notes.split("\n", 1)[1])  # no other version's section leaked in

    def test_platform_tag(self):
        script = load_script()
        with patch.object(script.platform, "system", return_value="Windows"), patch.object(script.platform, "machine", return_value="AMD64"):
            self.assertEqual(script.platform_tag(), "windows-x64")
        with patch.object(script.platform, "system", return_value="Linux"), patch.object(script.platform, "machine", return_value="aarch64"):
            self.assertEqual(script.platform_tag(), "linux-arm64")
        with patch.object(script.platform, "system", return_value="Darwin"), patch.object(script.platform, "machine", return_value="arm64"):
            self.assertEqual(script.platform_tag(), "macos-arm64")

    def test_package_writes_archive_notes_and_checksums(self):
        script = load_script()
        temp = tempfile.mkdtemp()
        try:
            dist = os.path.join(temp, "dist", "Iceberg")
            os.makedirs(os.path.join(dist, "_internal"))
            with open(os.path.join(dist, "Iceberg"), "wb") as handle:
                handle.write(b"#!/bin/sh\necho fake\n")
            with open(os.path.join(dist, "_internal", "x.txt"), "w") as handle:
                handle.write("resource")
            with patch.object(script, "DIST", dist), patch.object(script, "RELEASE", os.path.join(temp, "release")), \
                 patch.object(script.platform, "system", return_value="Linux"), patch.object(script.platform, "machine", return_value="x86_64"):
                artifacts = script.package()
            self.assertEqual(len(artifacts), 1)
            archive = artifacts[0]
            self.assertTrue(archive.endswith(f"Iceberg-{script.VERSION}-linux-x64.tar.gz"))
            with open(os.path.join(temp, "release", "SHA256SUMS-linux-x64.txt")) as handle:
                digest, name = handle.read().split()
            self.assertEqual(name, os.path.basename(archive))
            self.assertEqual(digest, hashlib.sha256(open(archive, "rb").read()).hexdigest())
            self.assertTrue(os.path.isfile(os.path.join(temp, "release", "RELEASE_NOTES.md")))
            import tarfile
            with tarfile.open(archive) as tf:
                names = tf.getnames()
            self.assertIn("Iceberg/Iceberg", names)
            self.assertIn("Iceberg/_internal/x.txt", names)
        finally:
            shutil.rmtree(temp)

    def test_build_inputs_are_tracked_by_git(self):
        """A .gitignore rule once hid packaging/iceberg.spec from commits; never again."""
        import subprocess
        script = load_script()
        result = subprocess.run(["git", "ls-files", "--error-unmatch", *script.REQUIRED_FOR_BUILD], cwd=ROOT, capture_output=True, text=True)
        if "not a git repository" in result.stderr:
            self.skipTest("not a git checkout")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_spec_and_packaging_files_exist(self):
        for rel in ("packaging/iceberg.spec", "packaging/iceberg.ico", "packaging/iceberg-256.png", "packaging/windows/iceberg.iss",
                    "packaging/linux/iceberg.desktop", "packaging/linux/install.sh", "packaging/linux/uninstall.sh", "build.ps1", "compile.s",
                    "LICENSE", "CHANGELOG.md", ".github/workflows/release.yml"):
            self.assertTrue(os.path.isfile(os.path.join(ROOT, rel)), rel)
        with open(os.path.join(ROOT, "packaging", "iceberg.spec"), encoding="utf-8") as handle:
            spec = handle.read()
        for folder in ("web", "fonts", "docs"):
            self.assertIn(f'"{folder}"', spec)


if __name__ == "__main__":
    unittest.main()
