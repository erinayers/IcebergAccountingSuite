import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db_calls
import session as session_module
from fixtures import LEDGER, add_transaction, make_database


def make_session():
    log = db_calls.create_connection(":memory:")
    db_calls.create_tables(log, session_module.CONSOLE_LOG_SCHEMA)
    return session_module.IcebergSession(session_log_connection=log)


class TestSession(unittest.TestCase):
    def test_console_log_writes_to_log_and_database(self):
        s = make_session()
        s.connection = make_database()
        db_calls.create_tables(s.connection, session_module.CONSOLE_LOG_SCHEMA)
        s.current_console_messages = s.console_log('Hello "quoted" world', s.current_console_messages)
        self.assertTrue(s.current_console_messages[0].endswith('Hello "quoted" world'))
        self.assertEqual(s.session_log_connection.execute("select count(*) from tbl_Console_Log").fetchone()[0], 1)
        stored = s.connection.execute("select Console_Messages, Created_Time from tbl_Console_Log").fetchone()
        self.assertIn('"quoted"', stored[0])
        self.assertRegex(stored[1], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$")

    def test_console_log_echoes_to_window_when_available(self):
        s = make_session()
        s.window = MagicMock()
        s.window.TKrootDestroyed = False
        s.console_log("Shown", [])
        s.window["-Console_Log-"].update.assert_called_once()

    def test_unsaved_change_tracking_ignores_console_writes(self):
        s = make_session()
        s.connection = make_database()
        db_calls.create_tables(s.connection, session_module.CONSOLE_LOG_SCHEMA)
        s.database_loaded = True
        s.reset_change_tracking()
        self.assertFalse(s.has_unsaved_changes())
        s.current_console_messages = s.console_log("just a message", s.current_console_messages)
        self.assertFalse(s.has_unsaved_changes())
        add_transaction(s.connection, "2025-01-01", "Rent", 100, "11001", "10002")
        self.assertTrue(s.has_unsaved_changes())
        s.mark_saved()
        self.assertFalse(s.has_unsaved_changes())
        self.assertTrue(s.last_saved_display)
        s.current_console_messages = s.console_log("another message", s.current_console_messages)
        self.assertFalse(s.has_unsaved_changes())

    def test_no_database_means_no_unsaved_changes(self):
        s = make_session()
        self.assertFalse(s.has_unsaved_changes())
        self.assertLessEqual(s.seconds_until_autosave(), session_module.AUTOSAVE_INTERVAL_SECONDS)

    def test_current_date_is_fresh(self):
        s = make_session()
        self.assertRegex(s.current_date, r"^\d{4}/\d{1,2}/\d{1,2}$")


if __name__ == "__main__":
    unittest.main()
