# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Iceberg (ST-021).  Run through scripts/build_release.py,
or directly:  pyinstaller packaging/iceberg.spec

One-folder build: dist/Iceberg/Iceberg(.exe) plus _internal/ with the web
interface, fonts, and docs.  User data never lives in this folder (see
paths.py); the program folder can be replaced wholesale on upgrade."""

import os
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
sys.path.insert(0, ROOT)
from version import VERSION  # noqa: E402

datas = [
    (os.path.join(ROOT, "web"), "web"),
    (os.path.join(ROOT, "fonts"), "fonts"),
    (os.path.join(ROOT, "docs"), "docs"),
    (os.path.join(ROOT, "LICENSE"), "."),
    (os.path.join(ROOT, "CHANGELOG.md"), "."),
]
icon = os.path.join(ROOT, "packaging", "iceberg.ico") if sys.platform.startswith("win") else os.path.join(ROOT, "packaging", "iceberg-256.png")

a = Analysis(
    [os.path.join(ROOT, "webapp.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=["webview", "webview.platforms.winforms", "webview.platforms.edgechromium", "webview.platforms.gtk", "webview.platforms.qt",
                   "clr_loader", "pythonnet", "bottle", "proxy_tools", "PIL.ImageDraw", "PIL.ImageFont", "img2pdf", "pikepdf"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "PyInstaller"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Iceberg",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Iceberg")
