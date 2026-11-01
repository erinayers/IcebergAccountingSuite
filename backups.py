"""Timestamped database backups and restore (ST-004).

Backups are byte-for-byte copies of the encrypted ``.icb`` file, so they are
opened with the same ``.icbkey`` as the live database.  They live in a
``backups`` folder next to the database::

    backups/
        A_Alpha_Corportation/
            A_Alpha_Corportation_20251221T224703Z.icb
            A_Alpha_Corportation_20251221T225203Z.icb

Names use UTC (``Z``) so the order is correct no matter which timezone or
daylight-saving rule the machine is using.  Only the newest ``keep`` backups
are retained for each database.
"""

import os
import re
import shutil
import tempfile

import iceberg_time

DEFAULT_KEEP = 20
BACKUP_FOLDER_NAME = "backups"

_BACKUP_NAME = re.compile(
    r"^(?P<stem>.+)_(?P<stamp>\d{8}T\d{6}Z)(?P<suffix>-\d+)?(?P<ext>\.[A-Za-z0-9]+)$"
)


class BackupError(Exception):
    """Raised when a backup cannot be created, listed, or restored."""


def _split(db_path):
    directory, filename = os.path.split(os.path.abspath(db_path))
    stem, ext = os.path.splitext(filename)
    return directory, stem, ext


def backup_directory(db_path, backup_root=None):
    """Return the folder that holds backups for ``db_path`` (not created)."""
    directory, stem, _ = _split(db_path)
    root = backup_root or os.path.join(directory, BACKUP_FOLDER_NAME)
    return os.path.join(root, stem)


def backup_name(db_path, moment=None):
    """Return the file name a backup of ``db_path`` would get at ``moment``."""
    _, stem, ext = _split(db_path)
    return f"{stem}_{iceberg_time.file_timestamp(moment)}{ext}"


def _copy_atomically(source, destination):
    """Copy ``source`` to ``destination`` so a partial copy is never visible."""
    target_dir = os.path.dirname(destination)
    os.makedirs(target_dir, exist_ok=True)
    handle, temp_path = tempfile.mkstemp(prefix=".tmp-", dir=target_dir)
    try:
        with os.fdopen(handle, "wb") as out, open(source, "rb") as src:
            shutil.copyfileobj(src, out)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp_path, destination)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def create_backup(db_path, backup_root=None, keep=DEFAULT_KEEP, moment=None):
    """Copy ``db_path`` into the backup folder and prune old copies.

    Returns the path of the new backup file.  Raises ``BackupError`` with a
    readable message if the database is missing or the copy fails.
    """
    if not os.path.isfile(db_path):
        raise BackupError(f"Cannot back up '{db_path}': the database file does not exist.")

    folder = backup_directory(db_path, backup_root)
    destination = os.path.join(folder, backup_name(db_path, moment))

    # Two saves inside the same second would collide; add a counter suffix.
    counter = 1
    base, ext = os.path.splitext(destination)
    while os.path.exists(destination):
        destination = f"{base}-{counter}{ext}"
        counter += 1

    try:
        _copy_atomically(db_path, destination)
    except OSError as error:
        raise BackupError(f"Backup of '{db_path}' failed: {error}") from error

    if keep is not None:
        prune_backups(db_path, backup_root=backup_root, keep=keep)
    return destination


def list_backups(db_path, backup_root=None):
    """Return backup paths for ``db_path``, newest first."""
    folder = backup_directory(db_path, backup_root)
    if not os.path.isdir(folder):
        return []
    _, stem, ext = _split(db_path)
    found = []
    for name in os.listdir(folder):
        match = _BACKUP_NAME.match(name)
        if not match or match.group("stem") != stem or match.group("ext") != ext:
            continue
        found.append(os.path.join(folder, name))
    found.sort(key=lambda path: os.path.basename(path), reverse=True)
    return found


def prune_backups(db_path, backup_root=None, keep=DEFAULT_KEEP):
    """Delete all but the newest ``keep`` backups.  Returns the removed paths."""
    removed = []
    if keep is None or keep < 0:
        return removed
    for path in list_backups(db_path, backup_root)[keep:]:
        try:
            os.remove(path)
            removed.append(path)
        except OSError:
            # Leaving an extra backup behind is harmless; never fail a save for it.
            continue
    return removed


def restore_backup(backup_path, db_path, backup_root=None):
    """Replace ``db_path`` with ``backup_path``.

    The current database file (if any) is first preserved as a regular backup
    so a restore can itself be undone.  Returns the path of that safety copy,
    or ``None`` when there was nothing to preserve.
    """
    if not os.path.isfile(backup_path):
        raise BackupError(f"Cannot restore: backup file '{backup_path}' does not exist.")

    safety_copy = None
    if os.path.isfile(db_path):
        safety_copy = create_backup(db_path, backup_root=backup_root, keep=None)

    try:
        _copy_atomically(backup_path, db_path)
    except OSError as error:
        raise BackupError(f"Restore from '{backup_path}' failed: {error}") from error
    return safety_copy


def describe_backup(backup_path):
    """Return a human readable label such as ``Sunday, 12/21/2025  -  17:47:03 (UTC-05:00)``."""
    match = _BACKUP_NAME.match(os.path.basename(backup_path))
    if not match:
        return os.path.basename(backup_path)
    stamp = match.group("stamp")
    iso = f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}+00:00"
    return iceberg_time.display_timestamp(iso)
