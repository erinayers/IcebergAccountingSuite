import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = load(os.path.join(ROOT, "site", "build.py"), "site_build")
        cls.site.PUBLIC = tempfile.mkdtemp()
        cls.pages = cls.site.build()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.site.PUBLIC)

    def read(self, name):
        with open(os.path.join(self.site.PUBLIC, name), encoding="utf-8") as handle:
            return handle.read()

    def test_all_pages_built_and_check_passes(self):
        self.assertEqual(sorted(self.pages), ["about.html", "downloads.html", "getting-started.html", "index.html"])
        self.assertEqual(self.site.check(), [])

    def test_required_content_per_story(self):
        from version import VERSION
        index = self.read("index.html")
        for text in ("What Iceberg does", "Who it is for", "What it is not (yet)", f"Download {VERSION}"):   # ST-027
            self.assertIn(text, index)
        downloads = self.read("downloads.html")
        for text in (f"Iceberg-{VERSION}-windows-x64-setup.exe", "SHA-256", "Verify your download", "Supported systems", "Get-FileHash", "sha256sum -c"):  # ST-028
            self.assertIn(text, downloads)
        started = self.read("getting-started.html")
        for text in ("Install", "Troubleshooting", "Report an issue", "/issues", "--check"):   # ST-029
            self.assertIn(text, started)
        about = self.read("about.html")
        for text in ('id="license"', "MIT License", 'id="privacy"', "no telemetry", 'id="security"', 'id="status"', "Fernet"):   # ST-030
            self.assertIn(text, about)

    def test_accessibility_and_responsiveness_basics(self):   # ST-031
        for name in self.pages:
            text = self.read(name)
            self.assertIn('<html lang="en">', text)
            self.assertIn('name="viewport"', text)
            self.assertIn('class="skip-link"', text)
            self.assertIn('aria-label="Main"', text)
            self.assertEqual(text.count("<h1>"), 1, name)
        with open(os.path.join(ROOT, "site", "site.css"), encoding="utf-8") as handle:
            css = handle.read()
        self.assertIn("@media (max-width: 640px)", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)

    def test_check_detects_problems(self):
        broken = os.path.join(self.site.PUBLIC, "broken.html")
        with open(broken, "w", encoding="utf-8") as handle:
            handle.write('<html><body><a href="missing.html">x</a><img src="assets/dashboard.png"></body></html>')
        try:
            problems = self.site.check()
            self.assertTrue(any("broken link missing.html" in p for p in problems))
            self.assertTrue(any("image without alt" in p for p in problems))
            self.assertTrue(any("missing lang attribute" in p for p in problems))
        finally:
            os.remove(broken)

    def test_releases_json_is_valid_and_matches_version(self):
        from version import VERSION
        with open(os.path.join(ROOT, "site", "releases.json"), encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertTrue(data["repository"].startswith("https://"))
        current = [r for r in data["releases"] if r["status"] == "current"]
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["version"], VERSION)
        for f in current[0]["files"]:
            self.assertTrue(f["name"].startswith(f"Iceberg-{VERSION}-"))

    def test_publish_release_info_updates_json(self):
        script = load(os.path.join(ROOT, "scripts", "publish_release_info.py"), "publish_release_info")
        temp = tempfile.mkdtemp()
        try:
            sums = os.path.join(temp, "SHA256SUMS-linux-x64.txt")
            with open(sums, "w") as handle:
                handle.write("a" * 64 + "  Iceberg-3.0.0-linux-x64.tar.gz\n")
            sums2 = os.path.join(temp, "SHA256SUMS-windows-x64.txt")
            with open(sums2, "w") as handle:
                handle.write("b" * 64 + "  Iceberg-3.0.0-windows-x64-setup.exe\n" + "c" * 64 + "  Iceberg-3.0.0-windows-x64.zip\n")
            files = script.parse_sums([sums, sums2])
            self.assertEqual([f["kind"] for f in files], ["Archive with install.sh", "Installer", "Portable archive"])
            data = {"repository": "https://x", "releases": [{"version": "2.0.0", "status": "current", "date": "d", "notes": "n", "files": []}]}
            updated = script.update(data, "3.0.0", "2027-01-01", "Big", files)
            self.assertEqual(updated["releases"][0]["version"], "3.0.0")
            self.assertEqual(updated["releases"][0]["status"], "current")
            self.assertEqual(updated["releases"][1]["status"], "previous")
            again = script.update(updated, "3.0.0", "2027-01-02", "Big again", files)
            self.assertEqual(len(again["releases"]), 2)   # re-running replaces, never duplicates
        finally:
            shutil.rmtree(temp)


if __name__ == "__main__":
    unittest.main()
