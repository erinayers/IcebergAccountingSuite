import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import startup_checks


class TestPythonVersion(unittest.TestCase):
    def test_supported_versions_pass(self):
        for minor in range(startup_checks.SUPPORTED_PYTHON[0][1], startup_checks.SUPPORTED_PYTHON[1][1] + 1):
            self.assertIsNone(startup_checks.python_version_problem((3, minor, 0)))

    def test_too_old_is_fatal(self):
        problem = startup_checks.python_version_problem((3, 8, 0))
        self.assertIsNotNone(problem)
        self.assertTrue(problem.fatal)
        self.assertIn("too old", problem.title)

    def test_too_new_is_a_warning_not_an_error(self):
        high = startup_checks.SUPPORTED_PYTHON[1]
        problem = startup_checks.python_version_problem((high[0], high[1] + 1, 0))
        self.assertIsNotNone(problem)
        self.assertFalse(problem.fatal)
        self.assertIn("prebuilt wheels", problem.detail)
        self.assertIn(f"{high[0]}.{high[1]}", problem.fix)


class TestModuleChecks(unittest.TestCase):
    def test_missing_module_reports_package_and_fix(self):
        problems = startup_checks.required_module_problems([("definitely_not_a_module_xyz", "xyz-package", "testing")])
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0].title, "Missing package: xyz-package")
        self.assertIn("pip install -r requirements.txt", problems[0].fix)

    def test_present_module_is_fine(self):
        self.assertEqual(startup_checks.required_module_problems([("os", "os", "testing")]), [])

    def test_webview_missing_message(self):
        with patch.dict(sys.modules, {"webview": None}):
            problem = startup_checks.webview_problem()
        self.assertIsNotNone(problem)
        self.assertIn("pywebview is not installed", problem.title)
        self.assertTrue(problem.fix)

    def test_webview_backend_missing_on_linux(self):
        fake = type(sys)("webview")
        with patch.dict(sys.modules, {"webview": fake}), patch.object(startup_checks.platform, "system", return_value="Linux"), \
             patch.object(startup_checks.importlib.util, "find_spec", return_value=None):
            problem = startup_checks.webview_problem()
        self.assertIsNotNone(problem)
        self.assertIn("backend", problem.title)
        with patch.dict(sys.modules, {"webview": fake}), patch.object(startup_checks.platform, "system", return_value="Windows"):
            self.assertIsNone(startup_checks.webview_problem())


class TestDataFiles(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_missing_files_are_listed(self):
        problems = startup_checks.data_file_problems(self.temp_dir, [("Logo_AI.png", "logo"), ("fonts/x.ttf", "font")])
        self.assertEqual([p.title for p in problems], ["Missing file: Logo_AI.png", "Missing file: fonts/x.ttf"])

    def test_present_files_pass(self):
        with open(os.path.join(self.temp_dir, "Logo_AI.png"), "wb") as file:
            file.write(b"png")
        self.assertEqual(startup_checks.data_file_problems(self.temp_dir, [("Logo_AI.png", "logo")]), [])

    def test_real_project_files_exist(self):
        self.assertEqual(startup_checks.data_file_problems(), [])

    def test_session_db_without_key_is_reported(self):
        with open(os.path.join(self.temp_dir, "sessions.icbs"), "wb") as file:
            file.write(b"x")
        problem = startup_checks.session_log_problem(self.temp_dir)
        self.assertIsNotNone(problem)
        self.assertIn("sessions.icbskey", problem.title)

    def test_missing_session_files_are_not_a_problem(self):
        # They are recreated on launch.
        self.assertIsNone(startup_checks.session_log_problem(self.temp_dir))


class TestReporting(unittest.TestCase):
    def test_report_without_problems(self):
        self.assertFalse(startup_checks.report_problems([], stream=io.StringIO()))

    def test_report_prints_and_flags_fatal(self):
        stream = io.StringIO()
        problems = [startup_checks.Problem("Bad thing", "detail", "do this", fatal=True)]
        with patch.object(startup_checks, "show_message_box", return_value=False) as box:
            self.assertTrue(startup_checks.report_problems(problems, stream=stream, dialog=True))
        box.assert_called_once()
        with patch.object(startup_checks, "show_message_box", return_value=False) as box:
            self.assertTrue(startup_checks.report_problems(problems, stream=io.StringIO()))   # headless (--check): no dialog
        box.assert_not_called()
        text = stream.getvalue()
        self.assertIn("[ERROR] Bad thing", text)
        self.assertIn("How to fix: do this", text)
        self.assertIn(startup_checks.DOCS_SETUP, text)

    def test_warnings_do_not_open_dialog(self):
        problems = [startup_checks.Problem("Hmm", "detail", "fix", fatal=False)]
        with patch.object(startup_checks, "show_message_box") as box:
            self.assertFalse(startup_checks.report_problems(problems, stream=io.StringIO()))
        box.assert_not_called()

    def test_app_directory_is_project_root(self):
        self.assertTrue(os.path.isfile(os.path.join(startup_checks.app_directory(), "webapp.py")))


if __name__ == "__main__":
    unittest.main()
