import importlib.util
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)


def load_script():
    spec = importlib.util.spec_from_file_location("check_release", os.path.join(ROOT, "scripts", "check_release.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckRelease(unittest.TestCase):
    def test_compile_and_files_pass_on_this_checkout(self):
        script = load_script()
        self.assertTrue(script.check_compile())
        self.assertTrue(script.check_files())

    def test_python_files_skip_virtualenvs(self):
        script = load_script()
        files = list(script.python_files())
        self.assertTrue(any(f.endswith("webapp.py") for f in files))
        self.assertFalse(any(os.sep + ".venv" + os.sep in f for f in files))

    def test_ci_workflow_covers_supported_matrix(self):
        import startup_checks
        with open(os.path.join(ROOT, ".github", "workflows", "ci.yml"), encoding="utf-8") as handle:
            text = handle.read()
        low, high = startup_checks.SUPPORTED_PYTHON
        for minor in range(low[1], high[1] + 1):
            self.assertIn(f'"{low[0]}.{minor}"', text)
        self.assertIn("windows-latest", text)
        self.assertIn("ubuntu-latest", text)
        self.assertIn("scripts/check_release.py", text)


if __name__ == "__main__":
    unittest.main()
