#!/usr/bin/env bash
# Install the extracted Iceberg folder for the current user (no root needed).
#   tar -xzf Iceberg-<version>-linux-x64.tar.gz && cd Iceberg && ./install.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="${XDG_DATA_HOME:-$HOME/.local/share}/iceberg-app"
BIN="$HOME/.local/bin"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICONS="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/256x256/apps"
mkdir -p "$TARGET" "$BIN" "$APPS" "$ICONS"
rm -rf "$TARGET"/*
cp -r "$HERE"/. "$TARGET"/
ln -sf "$TARGET/Iceberg" "$BIN/iceberg"
cp "$HERE/iceberg-256.png" "$ICONS/iceberg.png" 2>/dev/null || true
sed "s|^Exec=.*|Exec=$BIN/iceberg|" "$HERE/iceberg.desktop" > "$APPS/iceberg.desktop"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" || true
echo "Installed to $TARGET. Start with 'iceberg' (make sure $BIN is on your PATH) or from the application menu."
echo "Your books will be stored in ${XDG_DATA_HOME:-$HOME/.local/share}/iceberg."
