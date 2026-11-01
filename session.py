"""Application session state (ST-012).

``IcebergSession`` holds everything the running application knows: the open
database connection and its names, the cached lists behind the tables, the
console log, and the save/autosave state.  It has no knowledge of widgets
beyond the ``window`` reference used to echo console messages, so it can be
created and exercised in tests without a display.

Unsaved-change tracking (ST-018) uses SQLite's ``total_changes`` counter on
the in-memory connection.  Console messages are also written to the
database, so those writes are counted separately and excluded; "unsaved
changes" therefore means *bookkeeping* data changed since the last save.
"""

import os
import sys

import db_calls as db
import iceberg_time
from iceberg_utils import get_current_time_info

AUTOSAVE_INTERVAL_SECONDS = 5 * 60

CONSOLE_LOG_SCHEMA = """CREATE TABLE IF NOT EXISTS tbl_Console_Log (Log_ID INTEGER NOT NULL
    , Console_Messages VARCHAR(9999) NOT NULL
    , Created_Time VARCHAR(9999) NOT NULL
    , Edited_Time VARCHAR(9999) NOT NULL
    , PRIMARY KEY ("Log_ID" AUTOINCREMENT));"""

WELCOME = "Welcome to Iceberg Accounting Suite! Create or open a database to get started."


def session_log_paths(folder="."):
    return os.path.join(folder, "sessions.icbs"), os.path.join(folder, "sessions.icbskey")


def open_session_log(folder="."):
    """Load sessions.icbs into memory, creating the log and its key if absent.

    Earlier versions crashed with FileNotFoundError when the session files
    were missing.  The log only holds console messages, so it is safe to
    start a new one.
    """
    db_path, key_path = session_log_paths(folder)
    if not os.path.isfile(key_path):
        db.generate_filekey("sessions.icbs", folder)
    if not os.path.isfile(db_path):
        connection = db.create_connection(":memory:")
        db.create_tables(connection, CONSOLE_LOG_SCHEMA)
        result = db.save_encrypted_database(connection, db_path, key_path, backup=False)
        if not result.ok:
            print(result.message, file=sys.stderr)
        return connection
    try:
        connection, _ = db.open_encrypted_database(db_path, key_path)
    except db.DatabaseError as error:
        print(f"Session log could not be opened ({error}); starting a new in-memory log.", file=sys.stderr)
        connection = db.create_connection(":memory:")
    db.create_tables(connection, CONSOLE_LOG_SCHEMA)
    return connection


def save_session_log(session, folder="."):
    """Persist the session console log; failures are reported, never raised."""
    db_path, key_path = session_log_paths(folder)
    if not os.path.isfile(key_path):
        db.generate_filekey("sessions.icbs", folder)
    result = db.save_encrypted_database(session.session_log_connection, db_path, key_path, backup=False)
    if not result.ok:
        print(result.message, file=sys.stderr)
    return result


class IcebergSession:
    def __init__(self, session_log_connection=None):
        self.current_time_display = get_current_time_info()
        self.ledger_name = ""
        self.synchronized = "No"
        self.connection = False
        self.num = 1
        self.db_name = ""
        self.filekey = ""
        self.filename = ""
        self.database_loaded = False
        self.vendor_number = int(0)
        self.save_location = False
        self.account_number = False
        self.window = False
        self.vendors = []
        self.transactions = []
        self.transaction_date = iceberg_time.local_now()
        self.all_accounts = []
        self.business_name = []
        self.business_address = []
        self.owner_name = []
        self.owner_title = []
        self.owner_phone = []
        self.owner_email = []
        self.owner_notes = []
        self.business_ein = []
        self.customers = []
        self.current_year = iceberg_time.local_now().year
        self.receipts_location = "."
        self.current_console_messages = [WELCOME]
        self.session_log_connection = session_log_connection if session_log_connection is not None else open_session_log()
        self.session_filekey, self.session_filename, self.session_save_location = "", "sessions.icbskey", "./"
        self.last_autosave = iceberg_time.monotonic()
        self.last_saved_display = ""
        self.displayed_time = ""
        self.displayed_save_state = ""
        self.reconcile_session = None
        self.reconcile_items = []
        self.reconcile_statement_balance = 0
        self.last_report = None
        self.chart_rows = []
        self.customer_number = 0
        self.invoices = []
        self.service_number = 0
        self.services = []
        self.transaction = ""
        self.these_customers = []
        self.these_skus = []
        self.sales_tax = 0.00
        self.these_line_items = []
        self.this_invoice = {"Invoice_ID": "", "Line_Items": "", "Tracking_Code": "",
                             "Customer_ID": "", "Subtotal": "", "Sales_Tax": "",
                             "Total": "", "Status": "", "Payment_Method": "", "Location": "", "Due_Date": ""}
        self.transaction_debit_account = ""
        self._console_writes = 0
        self._saved_marker = 0
        self.log_file = None  # set by the host: console messages are appended here too

    # ------------------------------------------------------------ dates

    @property
    def current_date(self):
        """Today's local date as YYYY/M/D, recomputed on every use."""
        today = iceberg_time.local_now()
        return f"{today.year}/{today.month}/{today.day}"

    # ------------------------------------------------------ change tracking

    def _data_changes(self):
        if not self.connection:
            return 0
        try:
            return self.connection.total_changes - self._console_writes
        except Exception:
            return 0

    def reset_change_tracking(self):
        """Call after a database is opened or created."""
        self._console_writes = 0
        self._saved_marker = self._data_changes()

    def mark_saved(self):
        self._saved_marker = self._data_changes()
        self.last_saved_display = get_current_time_info()[0].split("  -  ")[-1]

    def has_unsaved_changes(self):
        return bool(self.database_loaded and self.connection) and self._data_changes() != self._saved_marker

    def seconds_until_autosave(self):
        return max(0, AUTOSAVE_INTERVAL_SECONDS - (iceberg_time.monotonic() - self.last_autosave))

    # ------------------------------------------------------------ console

    def console_log(self, message, current_console_messages):
        """Posts a message to the console and logs it in the database."""
        self.current_time_display = get_current_time_info()
        stored_time = iceberg_time.storage_timestamp()
        this_message = f"""Console ({self.current_time_display[1]}): {message}"""
        full_message = f"""{this_message}"""
        for i in range(len(current_console_messages)):
            full_message = full_message + f"""\n{current_console_messages[i]}"""

        # The window may already be destroyed when logging during exit.
        shown = False
        try:
            if self.window and not getattr(self.window, "TKrootDestroyed", False):
                self.window["-Console_Log-"].update(full_message)
                shown = True
        except Exception:
            pass
        if not shown:
            print(this_message)
        self._append_log_file(this_message)
        current_console_messages = [this_message] + current_console_messages

        safe_message = this_message.replace('"', '""')
        insert_log_entry_query = f"""INSERT INTO tbl_Console_Log (Console_Messages, Created_Time, Edited_Time)
            VALUES(("{safe_message}"),("{stored_time}"),("{stored_time}"));
        """
        db.execute_query(self.session_log_connection, insert_log_entry_query)

        if self.connection:
            before = self._data_changes_raw()
            db.execute_query(self.connection, insert_log_entry_query)
            self._console_writes += self._data_changes_raw() - before
        return current_console_messages

    def _append_log_file(self, line, max_bytes=2_000_000):
        """Mirror console messages to the log file with a single rotation (.1)."""
        if not self.log_file:
            return
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            if os.path.isfile(self.log_file) and os.path.getsize(self.log_file) > max_bytes:
                os.replace(self.log_file, self.log_file + ".1")
            with open(self.log_file, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except OSError:
            pass

    def _data_changes_raw(self):
        try:
            return self.connection.total_changes
        except Exception:
            return 0
