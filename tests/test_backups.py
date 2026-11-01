import datetime
import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backups
import iceberg_time


class TestBackups(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "Books.icb")
        with open(self.db_path, "wb") as file:
            file.write(b"version 1")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def moment(self, second):
        return datetime.datetime(2025, 12, 21, 22, 47, second, tzinfo=iceberg_time.UTC)

    def test_backup_name_uses_utc_stamp(self):
        self.assertEqual(backups.backup_name(self.db_path, self.moment(3)), "Books_20251221T224703Z.icb")

    def test_create_backup_copies_file_into_backups_folder(self):
        path = backups.create_backup(self.db_path, moment=self.moment(3))
        self.assertEqual(os.path.dirname(path), os.path.join(self.temp_dir, "backups", "Books"))
        with open(path, "rb") as file:
            self.assertEqual(file.read(), b"version 1")
        self.assertEqual(backups.list_backups(self.db_path), [path])

    def test_same_second_backups_do_not_collide(self):
        first = backups.create_backup(self.db_path, moment=self.moment(3))
        second = backups.create_backup(self.db_path, moment=self.moment(3))
        self.assertNotEqual(first, second)
        self.assertEqual(len(backups.list_backups(self.db_path)), 2)

    def test_list_backups_newest_first(self):
        for second in (5, 1, 9):
            backups.create_backup(self.db_path, moment=self.moment(second))
        names = [os.path.basename(p) for p in backups.list_backups(self.db_path)]
        self.assertEqual(names, ["Books_20251221T224709Z.icb", "Books_20251221T224705Z.icb", "Books_20251221T224701Z.icb"])

    def test_list_ignores_other_databases_and_stray_files(self):
        backups.create_backup(self.db_path, moment=self.moment(1))
        folder = backups.backup_directory(self.db_path)
        with open(os.path.join(folder, "Other_20251221T224701Z.icb"), "wb") as file:
            file.write(b"x")
        with open(os.path.join(folder, "notes.txt"), "wb") as file:
            file.write(b"x")
        self.assertEqual(len(backups.list_backups(self.db_path)), 1)

    def test_prune_keeps_newest(self):
        for second in range(1, 8):
            backups.create_backup(self.db_path, moment=self.moment(second), keep=3)
        names = [os.path.basename(p) for p in backups.list_backups(self.db_path)]
        self.assertEqual(names, ["Books_20251221T224707Z.icb", "Books_20251221T224706Z.icb", "Books_20251221T224705Z.icb"])

    def test_create_backup_missing_database(self):
        with self.assertRaises(backups.BackupError) as raised:
            backups.create_backup(os.path.join(self.temp_dir, "missing.icb"))
        self.assertIn("does not exist", str(raised.exception))

    def test_restore_replaces_file_and_keeps_safety_copy(self):
        old = backups.create_backup(self.db_path, moment=self.moment(1))
        with open(self.db_path, "wb") as file:
            file.write(b"version 2 (bad edit)")
        safety = backups.restore_backup(old, self.db_path)
        with open(self.db_path, "rb") as file:
            self.assertEqual(file.read(), b"version 1")
        with open(safety, "rb") as file:
            self.assertEqual(file.read(), b"version 2 (bad edit)")

    def test_restore_missing_backup(self):
        with self.assertRaises(backups.BackupError):
            backups.restore_backup(os.path.join(self.temp_dir, "nope.icb"), self.db_path)

    def test_restore_when_live_file_missing(self):
        old = backups.create_backup(self.db_path, moment=self.moment(1))
        os.remove(self.db_path)
        self.assertIsNone(backups.restore_backup(old, self.db_path))
        self.assertTrue(os.path.isfile(self.db_path))

    def test_describe_backup_shows_local_time(self):
        from unittest.mock import patch

        zone = datetime.timezone(datetime.timedelta(hours=-5))
        path = backups.create_backup(self.db_path, moment=self.moment(3))
        with patch("iceberg_time.local_timezone", return_value=zone):
            self.assertEqual(backups.describe_backup(path), "Sunday, 12/21/2025  -  17:47:03 (UTC-05:00)")
        self.assertEqual(backups.describe_backup("random.icb"), "random.icb")

    def test_custom_backup_root(self):
        root = os.path.join(self.temp_dir, "elsewhere")
        path = backups.create_backup(self.db_path, backup_root=root, moment=self.moment(1))
        self.assertTrue(path.startswith(os.path.join(root, "Books")))
        self.assertEqual(backups.list_backups(self.db_path, backup_root=root), [path])
        self.assertEqual(backups.list_backups(self.db_path), [])


if __name__ == "__main__":
    unittest.main()
