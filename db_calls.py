"""Database access, encryption, and safe persistence for Iceberg.

Saving (ST-003) follows an atomic pattern so an interrupted save can never
leave a half-written or missing book:

1. The in-memory SQLite database is serialized with ``Connection.backup``.
2. The bytes are encrypted in memory with the database's Fernet key.
3. The encrypted bytes are written to a temporary file *in the same folder*,
   flushed, and ``fsync``-ed.
4. The temporary file is verified by decrypting it and checking the SQLite
   header.
5. Only then is it moved over the live ``.icb`` with ``os.replace`` (atomic on
   Windows and POSIX).  A timestamped backup is taken afterwards (ST-004).

Every save returns a ``SaveResult`` that states whether it succeeded, so the
user interface can report success or failure instead of assuming.
"""

import logging
import os
import sqlite3
import tempfile
from sqlite3 import Error

from cryptography.fernet import Fernet, InvalidToken

import backups

logger = logging.getLogger(__name__)

SQLITE_HEADER = b"SQLite format 3\x00"


class DatabaseError(Exception):
    """A database could not be opened or saved.  The message is user readable."""


class SaveResult:
    """Outcome of ``save_database``.

    ``ok`` is True when the file on disk now holds the saved data.  ``message``
    is suitable for the console log.  ``backup_path`` is set when a backup was
    written, and ``error`` carries the underlying exception on failure.
    """

    def __init__(self, ok, message, path=None, backup_path=None, error=None):
        self.ok = ok
        self.message = message
        self.path = path
        self.backup_path = backup_path
        self.error = error

    def __str__(self):
        return self.message

    def __repr__(self):
        return f"SaveResult(ok={self.ok!r}, message={self.message!r})"


# ----------------------------------------------------------------- connections


def create_connection(path):
    connection = None
    try:
        logger.debug("create_connection: %s", path)
        connection = sqlite3.connect(path, check_same_thread=False)
    except Error as e:
        return f"""An error occured: {e}"""

    return connection


def close_connection(connection):
    sqlite3.Connection.close(connection)


def create_tables(connection, query):
    """
    Creates a table in the database.

    Args:
        connection: The sqlite3 connection object.
        query: The SQL query to create the table.
    """

    cursor = connection.cursor()
    try:
        cursor.execute(query)
        success_message = f"""Query executed successfully"""
        return success_message

    except Error as e:
        logger.error("Table Creation Error: %s", e)
        return e


def execute_query(connection, query):
    """Write databse query."""
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        success_message = f"""Query executed successfully"""
        return success_message

    except Error as e:
        logger.error("An error occured: %s", e)
        return e


def execute_read_query(connection, query):
    """
    Executes a read query and returns results as a list of tuples.
    """
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        logger.error("An error occured: %s", e)


def execute_read_query_tuple(connection, query):
    """
    Executes a read query and returns results as a list of tuple objects.
    """
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    results = None
    try:
        cursor.execute(query)
        results = tuple(zip(cursor.fetchall()))
        res_tuples = [result for result in results]
        return res_tuples
    except Error as e:
        logger.error("An error occured: %s", e)


def execute_read_query_dict(connection, query):
    """
    Executes a read query and returns results as a list of dictionaries.
    """
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    results = None
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        res_dicts = [dict(zip(result.keys(), result)) for result in results]
        return res_dicts
    except Error as e:
        return f"""An error occured: {e}"""


# ------------------------------------------------------------ memory <-> bytes


def load_db_to_memory(database):
    """
    Loads a disk-based database into memory.
    """
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    logger.debug("Opening db: %s", database)
    database.commit()  # make sure nothing pending is left out of the copy
    database.backup(connection)
    return connection


def serialize_connection(connection):
    """Return the full contents of ``connection`` as SQLite file bytes."""
    handle, temp_path = tempfile.mkstemp(prefix="iceberg-", suffix=".sqlite")
    os.close(handle)
    try:
        disk = sqlite3.connect(temp_path, check_same_thread=False)
        try:
            connection.commit()
            connection.backup(disk)
        finally:
            disk.close()
        with open(temp_path, "rb") as file:
            return file.read()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def connection_from_bytes(data):
    """Return an in-memory connection loaded from SQLite file bytes."""
    if not data.startswith(SQLITE_HEADER):
        raise DatabaseError("The file is not a SQLite database after decryption.")
    handle, temp_path = tempfile.mkstemp(prefix="iceberg-", suffix=".sqlite")
    try:
        with os.fdopen(handle, "wb") as file:
            file.write(data)
        disk = sqlite3.connect(temp_path, check_same_thread=False)
        try:
            return load_db_to_memory(disk)
        finally:
            disk.close()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def save_db_from_memory(connection, db_name):
    """
    Saves an in-memory database to disk (unencrypted) without ever deleting
    the previous file first.  Returns ``(disk_connection, connection)``.
    """
    atomic_write_bytes(db_name, serialize_connection(connection))
    connection_new = sqlite3.connect(f"{db_name}", check_same_thread=False)
    return connection_new, connection


# ------------------------------------------------------------------- file i/o


def atomic_write_bytes(path, data):
    """Write ``data`` to ``path`` so readers see either the old or the new file.

    The data goes to a temporary file in the same directory, is flushed and
    fsync-ed, then renamed over ``path``.
    """
    path = os.path.abspath(path)
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    handle, temp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory)
    try:
        with os.fdopen(handle, "wb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def is_sqlite_file(path):
    """True when ``path`` starts with the SQLite header (i.e. is unencrypted)."""
    try:
        with open(path, "rb") as file:
            return file.read(len(SQLITE_HEADER)) == SQLITE_HEADER
    except OSError:
        return False


def _join_key_path(save_location, filename):
    if save_location in (False, None, "", "."):
        save_location = "./"
    return os.path.join(save_location, filename)


def read_key(key_path):
    """Read a Fernet key file and return the key bytes, validating it."""
    try:
        with open(key_path, "rb") as file:
            key = file.read().strip()
    except FileNotFoundError:
        raise DatabaseError(
            f"Filekey not found: {key_path}. Select the .icbkey that was saved when the database was created."
        )
    except OSError as error:
        raise DatabaseError(f"Filekey could not be read: {key_path} ({error})")
    try:
        Fernet(key)
    except (ValueError, TypeError):
        raise DatabaseError(f"Filekey is not a valid Iceberg key: {key_path}")
    return key


def decrypt_bytes(key, data):
    try:
        return Fernet(key).decrypt(data)
    except InvalidToken:
        raise DatabaseError(
            "The filekey does not match this database (or the file is damaged)."
        )


def encrypt_bytes(key, data):
    return Fernet(key).encrypt(data)


# ------------------------------------------------------------------------ keys


def generate_filekey(db_name, save_location):
    """
    Generates a new encryption key and saves it to a file.
    """
    key = Fernet.generate_key()
    if save_location[-1] != "/":
        save_location = save_location + "/"
    filename = f"{db_name}key"
    file_address = f"{save_location}{db_name}key"
    atomic_write_bytes(file_address, key)
    return key, filename


def encrypt_database(db_name, mode, filename, save_location, new_name):
    """
    Encrypts or decrypts a database file in place, atomically.

    Args:
        db_name: The name of the database file.
        mode: 'encrypt' or 'decrypt'.
        filename: The name of the key file. If False, generates a new key (encrypt mode only).
        save_location: Directory to save the key or None/False for default.
        new_name: Optional new name for the processed database file.

    Returns:
        tuple: (filekey, filename, save_location)
    """
    logger.debug(
        "encrypt db_name %s; mode: %s; filename: %s; save_location: %s",
        db_name, mode, filename, save_location,
    )

    db_name_2 = db_name
    if new_name:
        db_name_2 = new_name

    if save_location == False or save_location == "" or save_location == ".":
        save_location = "./"
    if save_location[-1] != "/":
        save_location = save_location + "/"
    if filename == False and mode == "encrypt":
        filekey, filename = generate_filekey(db_name, save_location)
    elif filename == False and mode == "decrypt":
        return "Error: Attempted decryption without key.", ""
    if mode == "encrypt":
        filekey = read_key(f"{save_location}{filename}")
        with open(f"./{db_name_2}", "rb") as file:
            original_db = file.read()
        atomic_write_bytes(f"./{db_name}", encrypt_bytes(filekey, original_db))
        return filekey, filename, save_location
    elif mode == "decrypt":
        filekey = read_key(f"{save_location}{filename}")
        with open(f"./{db_name}", "rb") as file:
            original_db = file.read()
        atomic_write_bytes(f"./{db_name_2}", decrypt_bytes(filekey, original_db))
        return filekey, filename, save_location
    else:
        return "Error: Mode not selected. (encrypt or decrypt)", "", ""


# ------------------------------------------------------------------ open/save


def open_encrypted_database(db_path, key_path):
    """Load ``db_path`` into memory using the key at ``key_path``.

    The database is decrypted in memory only; no plaintext copy is written
    next to the live file.  Unencrypted ``.icb`` files (from very old
    versions) are still accepted.  Raises ``DatabaseError`` with a clear
    message when anything is wrong.
    """
    if not os.path.isfile(db_path):
        raise DatabaseError(
            f"Database not found: {db_path}. The .icb file must be in the Iceberg folder."
        )
    key = read_key(key_path)
    with open(db_path, "rb") as file:
        raw = file.read()
    if raw.startswith(SQLITE_HEADER):
        logger.warning("%s is not encrypted; it will be encrypted on the next save.", db_path)
        plain = raw
    else:
        plain = decrypt_bytes(key, raw)
    try:
        connection = connection_from_bytes(plain)
    except sqlite3.Error as error:
        raise DatabaseError(f"Database is damaged and could not be loaded: {error}")
    return connection, key


def open_database(filename, db_name, save_location):
    """
    Reads and connects to an encrypted or plain database.

    Returns ``(connection, filekey)``.  Raises ``DatabaseError`` on failure.
    """
    if filename == False:
        raise DatabaseError("Please select a filekey to continue.")
    return open_encrypted_database(f"./{db_name}", _join_key_path(save_location, filename))


def save_encrypted_database(connection, db_path, key_path, backup=True, keep=backups.DEFAULT_KEEP, backup_root=None):
    """Atomically save ``connection`` to ``db_path`` encrypted with ``key_path``.

    Never raises; inspect the returned ``SaveResult``.
    """
    db_path = os.path.abspath(db_path)
    try:
        key = read_key(key_path)
        plain = serialize_connection(connection)
        encrypted = encrypt_bytes(key, plain)

        directory = os.path.dirname(db_path)
        os.makedirs(directory, exist_ok=True)
        handle, temp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory)
        try:
            with os.fdopen(handle, "wb") as file:
                file.write(encrypted)
                file.flush()
                os.fsync(file.fileno())
            # Verify what actually reached the disk before replacing the live file.
            with open(temp_path, "rb") as file:
                written = file.read()
            if written != encrypted or not decrypt_bytes(key, written).startswith(SQLITE_HEADER):
                raise DatabaseError("Verification of the written file failed.")
            os.replace(temp_path, db_path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
    except (DatabaseError, OSError, sqlite3.Error, ValueError) as error:
        message = f"SAVE FAILED for {os.path.basename(db_path)}: {error} The previous file on disk was left untouched."
        logger.error(message)
        return SaveResult(False, message, path=db_path, error=error)

    backup_path = None
    message = f"Database saved: {db_path} ({len(encrypted):,} bytes)."
    if backup:
        try:
            backup_path = backups.create_backup(db_path, backup_root=backup_root, keep=keep)
            message += f" Backup written: {backup_path}"
        except backups.BackupError as error:
            # The save itself succeeded; report the backup problem without failing.
            message += f" WARNING: backup not written ({error})"
            logger.warning("%s", error)
    return SaveResult(True, message, path=db_path, backup_path=backup_path)


def save_database(connection, db_name, filename, save_location, backup=True):
    """
    Saves the current database state to an encrypted file.

    Returns ``(SaveResult, connection)``.  ``str(SaveResult)`` is a console
    friendly message and ``SaveResult.ok`` tells whether the save succeeded.
    """
    if filename == False:
        return SaveResult(False, "SAVE FAILED: no filekey selected."), connection
    if not connection:
        return SaveResult(False, "SAVE FAILED: no database is open."), connection
    result = save_encrypted_database(
        connection, f"./{db_name}", _join_key_path(save_location, filename), backup=backup
    )
    return result, connection
