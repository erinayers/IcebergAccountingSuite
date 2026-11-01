# Deployment, Upgrade, and Uninstall Guide

This guide is for users and IT administrators installing the **packaged** builds from
the releases page. (To run from source instead, see [SETUP.md](SETUP.md).)

## Before you start: where your data lives

Installed builds keep the program and your data apart, so upgrades never touch your books:

| | Windows | Linux |
|---|---|---|
| Program | `C:\Program Files\Iceberg` (installer) or wherever you unzip the archive | `~/.local/share/iceberg-app` (`install.sh`) or wherever you extract |
| Books (`.icb`), backups, logs, preferences | `%LOCALAPPDATA%\Iceberg` | `~/.local/share/iceberg` (or `$XDG_DATA_HOME/iceberg`) |
| Filekeys (`.icbkey`) | Wherever you chose when creating the database | same |
| Receipts and invoice PDFs | The receipts folder you chose (Database properties) | same |

*Tools → Where are my files* shows the exact folders on your machine. Two overrides exist:
`--data-dir PATH` (or the `ICEBERG_DATA_DIR` environment variable) relocates the data
folder — useful for a shared drive or a managed profile — and a file named `portable.txt`
next to the program keeps everything beside the program (thumb-drive use).

## Verify the download

Every release ships `SHA256SUMS.txt`. Compare before installing:

- Windows (PowerShell): `Get-FileHash .\Iceberg-2.0.0-windows-x64-setup.exe -Algorithm SHA256`
- Linux: `sha256sum -c SHA256SUMS.txt --ignore-missing`

The hash must match the line for your file exactly.

## Windows

### Install
1. Run `Iceberg-<version>-windows-x64-setup.exe`. The installer offers per-machine
   (`C:\Program Files\Iceberg`, needs administrator rights) or per-user installation and
   creates Start-menu and optional desktop shortcuts.
   *Without the installer:* unzip `Iceberg-<version>-windows-x64.zip` anywhere and run
   `Iceberg\Iceberg.exe`.
2. Windows 10/11 include the Edge WebView2 runtime the window needs. If the window opens
   blank, install the **WebView2 Runtime** from Microsoft and start Iceberg again.

### First run
Iceberg opens on the Welcome screen. Create a database (choose a **filekey folder** you
back up — the key cannot be recovered) or open an existing one with its `.icbkey`.
Moving books from a source checkout or another machine: copy the `.icb` into
`%LOCALAPPDATA%\Iceberg\databases` (*Tools → Where are my files → Open data folder*),
keep the `.icbkey` wherever you like, and open it.

### Upgrade
1. Close Iceberg (it saves on exit).
2. Run the new installer (or replace the unzipped folder). The data folder is not part of
   the program folder and is left exactly as it was.
3. Start Iceberg; *Tools → About* / the title shows the new version. Databases from earlier
   versions open unchanged; any optional tables a newer version needs are added on open.

### Rollback
Install the previous version's installer over the current one (or swap the folder back).
If a database was saved by the newer version and the older one refuses to open it, use
*Tools → Restore from backup* in the newer version to return to an earlier save, or copy
the backup from `%LOCALAPPDATA%\Iceberg\backups\<name>\` over the `.icb` by hand
(see [BACKUP_AND_RESTORE.md](BACKUP_AND_RESTORE.md)).

### Uninstall
*Settings → Apps → Iceberg Accounting Suite → Uninstall* (or delete the unzipped folder).
The uninstaller removes the program only. To remove your data too, delete
`%LOCALAPPDATA%\Iceberg` — after copying any `.icb` you want to keep, together with its
`.icbkey`.

## Linux

### Install
```bash
tar -xzf Iceberg-<version>-linux-x64.tar.gz
cd Iceberg
./install.sh          # copies to ~/.local/share/iceberg-app, adds ~/.local/bin/iceberg and a menu entry
```
The window needs WebKitGTK: `sudo apt install gir1.2-webkit2-4.1` (Debian/Ubuntu) or
`sudo dnf install webkit2gtk4.1` (Fedora). Without it, `iceberg --browser` opens the
interface in your default browser instead.

Running without installing: extract and run `./Iceberg` from the folder.

### First run, upgrade, rollback
As for Windows. To upgrade, extract the new archive and run its `install.sh` again (it
replaces `~/.local/share/iceberg-app`; `~/.local/share/iceberg` is untouched). To roll
back, run the older archive's `install.sh`.

### Uninstall
`~/.local/share/iceberg-app/uninstall.sh` removes the program, launcher, and menu entry and
leaves `~/.local/share/iceberg` in place.

## Managed and shared deployments

- **Per-user data** is the default and the recommendation: each Windows or Linux account
  gets its own `Iceberg` data folder, books, and preferences.
- **Shared books** on a network drive: start Iceberg with `--data-dir \\server\share\Iceberg`
  (or set `ICEBERG_DATA_DIR` in the user's environment). Only one person should have a
  given database open at a time; Iceberg writes the whole file on save.
- **Keep filekeys out of the data folder.** The `.icbkey` is the only way to open a
  database; store it where your backup policy covers it, separately from the `.icb`.
- **Logs** for support requests: `<data folder>/logs/iceberg.log` (rotated at 2 MB).
- **Silent install (Windows):** `Iceberg-<version>-windows-x64-setup.exe /VERYSILENT /NORESTART`
  installs per-machine without prompts.
- **Self-check without a window:** `Iceberg.exe --check` (Linux: `./Iceberg --check`)
  prints the detected problems and the data folder, and exits 0 when everything is fine —
  handy in a deployment script.

## Building the packages yourself

`./compile.s` (Linux/macOS) or `.\build.ps1` (Windows) creates the virtual environment,
installs the pinned dependencies, builds with PyInstaller, verifies the result, and writes
the archive, installer (Windows, when Inno Setup is installed), `RELEASE_NOTES.md`, and
`SHA256SUMS-<platform>.txt` to `release/`. The same steps run in CI for every version tag
(`.github/workflows/release.yml`), which publishes the GitHub release.
