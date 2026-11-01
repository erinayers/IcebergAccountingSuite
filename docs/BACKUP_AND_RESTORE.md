# Saving, Backups, and Restore

This document explains how Iceberg writes your books to disk, where backups go,
and how to recover from an accidental edit or a damaged file.

## How a save works

Your database is edited in memory and written to the encrypted `.icb` file:

- automatically every **5 minutes** while a database is open (*Autosave*);
- when you select **Save** or press `Ctrl+S` (*Manual save*);
- after finishing a reconciliation or importing transactions;
- when you exit Iceberg (*Save on exit*).

Every save is **atomic**: the new contents are written to a temporary file in the
same folder, flushed to disk, decrypted and verified, and only then moved over the
live `.icb` in a single rename. If the power fails, the disk fills up, or the
process is killed halfway through, the previous file is still intact — a save never
leaves a half-written database.

Every save **reports its result** in the status line and in the console log (Tools → Console log), e.g.

```
Console (Sunday, 12/21/2025  -  17:52:20 (UTC-05:00)): Autosave: Database saved: /home/you/Iceberg/Books.icb (103,864 bytes). Backup written: /home/you/Iceberg/backups/Books/Books_20251221T225220Z.icb
```

A failed save is shown in red in the status line and logged as `SAVE FAILED … The previous
file on disk was left untouched.` The database stays open in memory, so fix the cause
(disk space, permissions, the key file location) and save again. Console messages
are stored inside the database as well (`tbl_Console_Log`), so the save history is
part of the audit trail.

If a save fails when you exit, Iceberg asks whether you really want to quit and lose
the unsaved changes.

## Backups

After every successful save, Iceberg copies the encrypted `.icb` to

```
<Iceberg folder>/backups/<Business>/<Business>_<UTC timestamp>.icb
```

for example `backups/Books/Books_20251221T225220Z.icb`. The timestamp is UTC
(the trailing `Z`), so backups sort correctly regardless of your timezone or
daylight-saving changes. The **20 newest** backups are kept per database; older ones
are deleted automatically.

Backups are encrypted with the **same `.icbkey`** as the live database. Keep that key
safe — a backup is useless without it. For protection against disk failure, copy the
`backups` folder and your `.icbkey` to another drive or a cloud folder periodically.

## Restoring from a backup (in the application)

1. Open the database you want to restore.
2. Choose **Tools → Restore from backup**.
3. Pick the backup from the list. Each entry shows the backup's time in your local
   timezone followed by the file name.
4. Select **Restore** next to it and confirm. Iceberg first saves a safety copy of the current file into the backups
   folder, then replaces the live `.icb` with the chosen backup and reopens it. The
   dashboard reloads from the restored data.

If you restored the wrong one, open *Restore from backup* again and choose the safety
copy (it is the newest entry).

## Restoring manually (if Iceberg will not start)

1. Close Iceberg.
2. In the Iceberg folder, rename the damaged `Books.icb` to `Books.icb.damaged`.
3. Copy the backup you want, e.g. `backups/Books/Books_20251221T225220Z.icb`, into the
   Iceberg folder and rename it to `Books.icb`.
4. Start Iceberg and open the database with the usual `Books.icbkey`.

## Moving to another computer

Copy the `.icb`, its `.icbkey`, and (optionally) the `backups/<Business>` folder. Put
the `.icb` and the `backups` folder inside the new Iceberg folder; the key can live
anywhere you choose, as before.

## Timestamps

All `Created_Time` / `Edited_Time` values written since version 1.2 are stored in
UTC (`2025-12-21T22:52:20+00:00`). The application shows them in the local timezone
of the computer with a numeric offset, e.g. `Sunday, 12/21/2025  -  17:52:20 (UTC-05:00)`.
Records written by earlier versions are still displayed correctly. See the
"Consistent time handling" section of the README for details.
