#!/usr/bin/env python3
"""Build the website into site/public (ST-027 to ST-031).

    python site/build.py            # writes site/public/
    python site/build.py --check    # build, then verify links, structure, and accessibility basics

Pages are fragments in site/pages/*.html (first line holds title/description);
downloads.html is generated from site/releases.json; layout.html wraps everything.
"""

import argparse
import html
import json
import os
import re
import shutil
import sys

SITE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SITE)
PUBLIC = os.path.join(SITE, "public")
sys.path.insert(0, ROOT)
from version import VERSION  # noqa: E402

NAV = [("index.html", "Overview"), ("downloads.html", "Downloads"), ("getting-started.html", "Getting started"), ("about.html", "License & privacy")]
SCREENSHOTS = {"dashboard.png": "04-dashboard.png", "ledger.png": "06-new-transaction.png", "invoices.png": "10-invoices.png"}


def load_releases():
    with open(os.path.join(SITE, "releases.json"), encoding="utf-8") as handle:
        return json.load(handle)


def page_meta(text):
    match = re.match(r"\s*<!--\s*title:\s*(.*?)\s*\|\s*description:\s*(.*?)\s*-->", text, re.S)
    if not match:
        raise SystemExit("page fragment must start with <!-- title: ... | description: ... -->")
    return match.group(1), match.group(2), text[match.end():]


def downloads_page(data):
    repo = data["repository"]
    parts = [
        "<h1>Downloads</h1>",
        '<p class="lead">Packaged builds for Windows and Linux. Every file is listed with its SHA-256 checksum so you can confirm the download is intact and unmodified.</p>',
    ]
    for release in data["releases"]:
        tag = f"v{release['version']}"
        status = {"current": ("ok", "Current"), "previous": ("info", "Previous"), "preview": ("warn", "Preview")}.get(release.get("status", "previous"), ("info", "Previous"))
        parts.append(f'<h2 id="{html.escape(tag)}">Iceberg {html.escape(release["version"])} <span class="pill {status[0]}">{status[1]}</span> <span class="muted">{html.escape(release["date"])}</span></h2>')
        parts.append(f'<p>{html.escape(release["notes"])} <a href="{repo}/releases/tag/{tag}">Full release notes</a>.</p>')
        parts.append('<div class="table-scroll"><table><thead><tr><th>File</th><th>For</th><th>Type</th><th>SHA-256</th></tr></thead><tbody>')
        for f in release["files"]:
            url = f"{repo}/releases/download/{tag}/{f['name']}"
            parts.append(f'<tr><td><a href="{url}">{html.escape(f["name"])}</a></td><td>{html.escape(f["os"])}</td><td>{html.escape(f["kind"])}</td><td class="mono" style="word-break:break-all;font-size:12px;">{html.escape(f["sha256"])}</td></tr>')
        parts.append("</tbody></table></div>")
        parts.append(f'<p class="muted">Checksums for every file: <a href="{repo}/releases/download/{tag}/SHA256SUMS.txt">SHA256SUMS.txt</a></p>')
    parts.append('''
<h2 id="verify">Verify your download</h2>
<div class="panel">
  <p>Compare the checksum of the file you downloaded with the table above. They must match exactly.</p>
  <p><strong>Windows (PowerShell):</strong></p>
  <pre><code>Get-FileHash .\\Iceberg-{v}-windows-x64-setup.exe -Algorithm SHA256</code></pre>
  <p><strong>Linux:</strong></p>
  <pre><code>sha256sum -c SHA256SUMS.txt --ignore-missing</code></pre>
</div>
<h2>Supported systems</h2>
<div class="table-scroll"><table>
  <thead><tr><th>System</th><th>Requirements</th></tr></thead>
  <tbody>
    <tr><td>Windows 10 / 11 (64-bit)</td><td>Edge WebView2 runtime (included with Windows; installable from Microsoft if missing).</td></tr>
    <tr><td>Linux x86-64</td><td>glibc 2.28 or newer (Ubuntu 20.04+, Debian 10+, Fedora 29+); WebKitGTK for the window, or use <code>--browser</code>.</td></tr>
    <tr><td>macOS</td><td>Not packaged yet; runs from source with Python 3.11-3.14.</td></tr>
  </tbody>
</table></div>
<p>Install, upgrade, rollback, and uninstall steps for each system are in the <a href="{repo}/blob/master/docs/DEPLOYMENT.md">deployment guide</a>.</p>
'''.replace("{v}", html.escape(data["releases"][0]["version"])).replace("{repo}", repo))
    return "Downloads", "Download Iceberg for Windows and Linux with release notes and SHA-256 checksums.", "\n".join(parts)


def render(layout, title, description, content, current, data):
    nav = "".join(f'<li><a href="{href}"{" aria-current=\"page\"" if href == current else ""}>{label}</a></li>' for href, label in NAV)
    out = layout
    for key, value in {"title": html.escape(title), "description": html.escape(description), "nav": nav, "content": content,
                       "version": html.escape(VERSION), "repo": data["repository"]}.items():
        out = out.replace("{{" + key + "}}", value)
    return out


def build():
    data = load_releases()
    shutil.rmtree(PUBLIC, ignore_errors=True)
    os.makedirs(os.path.join(PUBLIC, "assets"), exist_ok=True)
    shutil.copy(os.path.join(SITE, "site.css"), PUBLIC)
    shutil.copy(os.path.join(ROOT, "packaging", "iceberg-256.png"), os.path.join(PUBLIC, "assets"))
    for target, source in SCREENSHOTS.items():
        shutil.copy(os.path.join(ROOT, "docs", "screens", source), os.path.join(PUBLIC, "assets", target))
    with open(os.path.join(SITE, "layout.html"), encoding="utf-8") as handle:
        layout = handle.read()
    written = []
    for name in sorted(os.listdir(os.path.join(SITE, "pages"))):
        if not name.endswith(".html"):
            continue
        with open(os.path.join(SITE, "pages", name), encoding="utf-8") as handle:
            title, description, content = page_meta(handle.read())
        content = content.replace("{{version}}", html.escape(VERSION)).replace("{{repo}}", data["repository"])
        with open(os.path.join(PUBLIC, name), "w", encoding="utf-8") as handle:
            handle.write(render(layout, title, description, content, name, data))
        written.append(name)
    title, description, content = downloads_page(data)
    with open(os.path.join(PUBLIC, "downloads.html"), "w", encoding="utf-8") as handle:
        handle.write(render(layout, title, description, content, "downloads.html", data))
    written.append("downloads.html")
    return written


def check():
    """Structure, accessibility basics, and internal links for every built page."""
    problems = []
    pages = [n for n in os.listdir(PUBLIC) if n.endswith(".html")]
    for name in pages:
        with open(os.path.join(PUBLIC, name), encoding="utf-8") as handle:
            text = handle.read()
        for needle, what in [('<html lang="en">', "lang attribute"), ('name="viewport"', "viewport meta"), ('class="skip-link"', "skip link"),
                             ('<nav class="primary" aria-label="Main">', "labelled navigation"), ('<main id="main"', "main landmark"),
                             ("<h1>", "an h1"), ('aria-current="page"', "current-page marker"), ('name="description"', "meta description")]:
            if needle not in text:
                problems.append(f"{name}: missing {what}")
        if text.count("<h1>") != 1:
            problems.append(f"{name}: expected exactly one h1")
        for img in re.findall(r"<img [^>]*>", text):
            if 'alt="' not in img:
                problems.append(f"{name}: image without alt text: {img[:60]}")
        for href in re.findall(r'(?:href|src)="([^"]+)"', text):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = href.split("#")[0]
            if target and not os.path.exists(os.path.join(PUBLIC, target)):
                problems.append(f"{name}: broken link {href}")
        for anchor in re.findall(r'href="[^"#]*#([^"]+)"', text):
            page = re.search(r'href="([^"#]*)#' + re.escape(anchor), text).group(1) or name
            with open(os.path.join(PUBLIC, page), encoding="utf-8") as handle:
                if f'id="{anchor}"' not in handle.read():
                    problems.append(f"{name}: anchor #{anchor} not found in {page}")
    for name, _ in NAV:
        if name not in pages:
            problems.append(f"navigation target {name} was not built")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    written = build()
    print("built:", ", ".join(written), "->", os.path.relpath(PUBLIC, ROOT))
    if args.check:
        problems = check()
        for problem in problems:
            print("PROBLEM", problem)
        print("site check:", "ok" if not problems else f"{len(problems)} problem(s)")
        sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
