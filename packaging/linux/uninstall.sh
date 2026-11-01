#!/usr/bin/env bash
# Remove the program only; books, backups, and logs in ~/.local/share/iceberg are kept.
set -e
rm -rf "${XDG_DATA_HOME:-$HOME/.local/share}/iceberg-app"
rm -f "$HOME/.local/bin/iceberg" "${XDG_DATA_HOME:-$HOME/.local/share}/applications/iceberg.desktop" "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/256x256/apps/iceberg.png"
echo "Iceberg removed. Your data folder was left in place: ${XDG_DATA_HOME:-$HOME/.local/share}/iceberg"
