import unittest
import sqlite3
import os
import sys

# Add parent directory to path to import db_calls
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db_calls

class TestDbCalls(unittest.TestCase):
    def setUp(self):
        # Use in-memory database for testing
        self.conn = db_calls.create_connection(':memory:')
        self.create_table_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id integer PRIMARY KEY,
                name text NOT NULL,
                email text
            );
        """
        db_calls.create_tables(self.conn, self.create_table_sql)

    def tearDown(self):
        db_calls.close_connection(self.conn)

    def test_create_connection(self):
        self.assertIsInstance(self.conn, sqlite3.Connection)

    def test_execute_query(self):
        insert_sql = "INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com')"
        result = db_calls.execute_query(self.conn, insert_sql)
        self.assertEqual(result, "Query executed successfully")

    def test_execute_read_query(self):
        insert_sql = "INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com')"
        db_calls.execute_query(self.conn, insert_sql)
        select_sql = "SELECT * FROM users WHERE name='Bob'"
        rows = db_calls.execute_read_query(self.conn, select_sql)
        self.assertIsNotNone(rows)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], 'Bob')

    def test_execute_read_query_dict(self):
        insert_sql = "INSERT INTO users (name, email) VALUES ('Charlie', 'charlie@example.com')"
        db_calls.execute_query(self.conn, insert_sql)
        select_sql = "SELECT * FROM users WHERE name='Charlie'"
        rows = db_calls.execute_read_query_dict(self.conn, select_sql)
        self.assertIsNotNone(rows)
        self.assertEqual(len(rows), 1)
        self.assertIsInstance(rows[0], dict)
        self.assertEqual(rows[0]['name'], 'Charlie')

    def test_execute_read_query_tuple(self):
        # This function sets row_factory to sqlite3.Row and does some zip magic
        insert_sql = "INSERT INTO users (name, email) VALUES ('David', 'david@example.com')"
        db_calls.execute_query(self.conn, insert_sql)
        select_sql = "SELECT * FROM users WHERE name='David'"
        rows = db_calls.execute_read_query_tuple(self.conn, select_sql)
        
        self.assertIsNotNone(rows)
        self.assertTrue(len(rows) > 0)
        
        # Based on analysis: results = tuple(zip(cursor.fetchall()))
        # rows is a list of tuples, where each tuple contains one element which is the Row object.
        first_row_wrapper = rows[0]
        self.assertIsInstance(first_row_wrapper, tuple)
        
        actual_row = first_row_wrapper[0]
        self.assertIsInstance(actual_row, sqlite3.Row)
        self.assertEqual(actual_row['name'], 'David')

    def test_error_handling(self):
        # Test executing invalid query
        result = db_calls.execute_query(self.conn, "SELECT * FROM non_existent_table")
        # execute_query returns the exception object on error
        self.assertIsInstance(result, sqlite3.Error)

    def test_load_db_to_memory(self):
        # Populate current in-memory db
        insert_sql = "INSERT INTO users (name, email) VALUES ('Eve', 'eve@example.com')"
        db_calls.execute_query(self.conn, insert_sql)
        
        # Load into a NEW memory connection
        new_conn = db_calls.load_db_to_memory(self.conn)
        
        self.assertNotEqual(self.conn, new_conn)
        
        # Verify data is present in new connection
        select_sql = "SELECT * FROM users WHERE name='Eve'"
        rows = db_calls.execute_read_query(new_conn, select_sql)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], 'Eve')
        new_conn.close()

    def test_generate_filekey(self):
        # Use a temporary file path
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            db_name = "test_db.icb"
            # generate_filekey(db_name, save_location)
            # It appends '/' to save_location if missing
            key, filename = db_calls.generate_filekey(db_name, temp_dir)
            
            self.assertIsInstance(key, bytes)
            self.assertEqual(filename, "test_db.icbkey")
            
            expected_key_path = os.path.join(temp_dir, filename)
            self.assertTrue(os.path.exists(expected_key_path))
            
            with open(expected_key_path, 'rb') as f:
                content = f.read()
                self.assertEqual(content, key)
                
        finally:
            shutil.rmtree(temp_dir)


class TestSafeSaves(unittest.TestCase):
    """ST-003 / ST-004: saves are atomic, verified, reported, and backed up."""

    def setUp(self):
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "Books.icb")
        self.key, _ = db_calls.generate_filekey("Books.icb", self.temp_dir)
        self.key_path = os.path.join(self.temp_dir, "Books.icbkey")
        self.conn = db_calls.create_connection(":memory:")
        db_calls.create_tables(self.conn, "CREATE TABLE ledger (id INTEGER PRIMARY KEY, name TEXT)")
        db_calls.execute_query(self.conn, "INSERT INTO ledger (name) VALUES ('rent')")

    def tearDown(self):
        import shutil
        self.conn.close()
        shutil.rmtree(self.temp_dir)

    def test_save_writes_encrypted_file_and_backup(self):
        result = db_calls.save_encrypted_database(self.conn, self.db_path, self.key_path)
        self.assertTrue(result.ok, result.message)
        self.assertIn("Database saved", str(result))
        self.assertTrue(os.path.isfile(self.db_path))
        self.assertFalse(db_calls.is_sqlite_file(self.db_path))  # encrypted on disk
        self.assertTrue(os.path.isfile(result.backup_path))
        self.assertIn(os.path.join("backups", "Books"), result.backup_path)

    def test_saved_file_round_trips(self):
        db_calls.save_encrypted_database(self.conn, self.db_path, self.key_path, backup=False)
        reopened, key = db_calls.open_encrypted_database(self.db_path, self.key_path)
        self.assertEqual(key, self.key)
        self.assertEqual(db_calls.execute_read_query(reopened, "SELECT name FROM ledger"), [("rent",)])
        reopened.close()

    def test_no_temporary_files_left_behind(self):
        db_calls.save_encrypted_database(self.conn, self.db_path, self.key_path, backup=False)
        self.assertEqual(sorted(os.listdir(self.temp_dir)), ["Books.icb", "Books.icbkey"])

    def test_failed_save_leaves_previous_file_untouched(self):
        db_calls.save_encrypted_database(self.conn, self.db_path, self.key_path, backup=False)
        with open(self.db_path, "rb") as file:
            before = file.read()
        db_calls.execute_query(self.conn, "INSERT INTO ledger (name) VALUES ('new')")
        # Simulate the disk failing mid-write.
        original = os.fsync

        def broken_fsync(fd):
            raise OSError(28, "No space left on device")

        os.fsync = broken_fsync
        try:
            result = db_calls.save_encrypted_database(self.conn, self.db_path, self.key_path, backup=False)
        finally:
            os.fsync = original
        self.assertFalse(result.ok)
        self.assertIn("SAVE FAILED", result.message)
        self.assertIn("left untouched", result.message)
        self.assertIsInstance(result.error, OSError)
        with open(self.db_path, "rb") as file:
            self.assertEqual(file.read(), before)
        self.assertEqual(sorted(os.listdir(self.temp_dir)), ["Books.icb", "Books.icbkey"])

    def test_missing_key_is_reported_not_raised(self):
        result = db_calls.save_encrypted_database(self.conn, self.db_path, os.path.join(self.temp_dir, "nope.icbkey"), backup=False)
        self.assertFalse(result.ok)
        self.assertIn("Filekey not found", result.message)
        self.assertFalse(os.path.exists(self.db_path))

    def test_save_database_wrapper_returns_result_and_connection(self):
        cwd = os.getcwd()
        os.chdir(self.temp_dir)
        try:
            result, connection = db_calls.save_database(self.conn, "Books.icb", "Books.icbkey", self.temp_dir)
        finally:
            os.chdir(cwd)
        self.assertTrue(result.ok, result.message)
        self.assertIs(connection, self.conn)
        self.assertFalse(db_calls.save_database(self.conn, "Books.icb", False, self.temp_dir)[0].ok)
        self.assertFalse(db_calls.save_database(None, "Books.icb", "Books.icbkey", self.temp_dir)[0].ok)

    def test_backups_accumulate_per_save(self):
        import backups
        db_calls.save_encrypted_database(self.conn, self.db_path, self.key_path)
        db_calls.save_encrypted_database(self.conn, self.db_path, self.key_path)
        self.assertEqual(len(backups.list_backups(self.db_path)), 2)


class TestOpenDatabase(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "Books.icb")
        self.key, _ = db_calls.generate_filekey("Books.icb", self.temp_dir)
        self.key_path = os.path.join(self.temp_dir, "Books.icbkey")
        conn = db_calls.create_connection(":memory:")
        db_calls.create_tables(conn, "CREATE TABLE tbl_Accounts (Account_ID INTEGER PRIMARY KEY)")
        db_calls.save_encrypted_database(conn, self.db_path, self.key_path, backup=False)
        conn.close()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_open_does_not_write_plaintext_to_disk(self):
        with open(self.db_path, "rb") as file:
            before = file.read()
        conn, _ = db_calls.open_encrypted_database(self.db_path, self.key_path)
        conn.close()
        with open(self.db_path, "rb") as file:
            self.assertEqual(file.read(), before)
        self.assertEqual(sorted(os.listdir(self.temp_dir)), ["Books.icb", "Books.icbkey"])

    def test_missing_database_message(self):
        with self.assertRaises(db_calls.DatabaseError) as raised:
            db_calls.open_encrypted_database(os.path.join(self.temp_dir, "Other.icb"), self.key_path)
        self.assertIn("Database not found", str(raised.exception))

    def test_missing_key_message(self):
        with self.assertRaises(db_calls.DatabaseError) as raised:
            db_calls.open_encrypted_database(self.db_path, os.path.join(self.temp_dir, "Other.icbkey"))
        self.assertIn("Filekey not found", str(raised.exception))

    def test_wrong_key_message(self):
        db_calls.generate_filekey("Other.icb", self.temp_dir)
        with self.assertRaises(db_calls.DatabaseError) as raised:
            db_calls.open_encrypted_database(self.db_path, os.path.join(self.temp_dir, "Other.icbkey"))
        self.assertIn("does not match", str(raised.exception))

    def test_invalid_key_file_message(self):
        bad_key = os.path.join(self.temp_dir, "bad.icbkey")
        with open(bad_key, "wb") as file:
            file.write(b"not a key")
        with self.assertRaises(db_calls.DatabaseError) as raised:
            db_calls.open_encrypted_database(self.db_path, bad_key)
        self.assertIn("not a valid Iceberg key", str(raised.exception))

    def test_damaged_file_message(self):
        with open(self.db_path, "wb") as file:
            file.write(b"garbage")
        with self.assertRaises(db_calls.DatabaseError):
            db_calls.open_encrypted_database(self.db_path, self.key_path)

    def test_legacy_unencrypted_database_still_opens(self):
        plain = db_calls.create_connection(":memory:")
        db_calls.create_tables(plain, "CREATE TABLE tbl_Accounts (Account_ID INTEGER PRIMARY KEY)")
        db_calls.atomic_write_bytes(self.db_path, db_calls.serialize_connection(plain))
        self.assertTrue(db_calls.is_sqlite_file(self.db_path))
        conn, _ = db_calls.open_encrypted_database(self.db_path, self.key_path)
        self.assertEqual(db_calls.execute_read_query(conn, "SELECT COUNT(*) FROM tbl_Accounts"), [(0,)])
        conn.close()

    def test_open_database_wrapper_requires_key(self):
        with self.assertRaises(db_calls.DatabaseError):
            db_calls.open_database(False, "Books.icb", self.temp_dir)

    def test_atomic_write_bytes_replaces_existing(self):
        target = os.path.join(self.temp_dir, "file.bin")
        db_calls.atomic_write_bytes(target, b"one")
        db_calls.atomic_write_bytes(target, b"two")
        with open(target, "rb") as file:
            self.assertEqual(file.read(), b"two")
        self.assertFalse([n for n in os.listdir(self.temp_dir) if n.startswith(".tmp-")])



if __name__ == '__main__':
    unittest.main()
