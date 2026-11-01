#!/usr/bin/env python3
"""Release checks (ST-013): one command that verifies a checkout is releasable.

Run locally with ``python scripts/check_release.py`` (add ``--wheels`` to
also confirm that every pinned dependency has a prebuilt wheel for the
supported interpreters; that step needs network access).  The same script
runs in CI on every supported OS/Python combination.

Checks, in order:
  1. Interpreter is a supported version (startup_checks.SUPPORTED_PYTHON).
  2. Every Python file compiles.
  3. pyflakes finds no undefined names (if pyflakes is installed).
  4. Required data files and documentation referenced by the code exist.
  5. The test suite passes.
  6. ``pip check`` reports consistent installed packages.
  7. (--wheels) pinned requirements resolve to wheels for each supported Python.
"""

import argparse
import os
import py_compile
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import startup_checks  # noqa: E402

REQUIRED_DOCS = ["README.md", "docs/SETUP.md", "docs/BACKUP_AND_RESTORE.md", "docs/RECONCILIATION.md",
                 "docs/REPORTS.md", "docs/IMPORT_EXPORT.md", "docs/UI_GUIDE.md", "docs/ARCHITECTURE.md", "docs/DEPLOYMENT.md",
                 "CHANGELOG.md", "LICENSE", "packaging/iceberg.spec", "site/build.py", "site/releases.json",
                 "web/index.html", "web/app.css", "web/routes.js", "web/client.js", "web/render.js", "web/app.js", "web/mock.js"]
SKIP_DIRS = {".venv", "venv", "build", "dist", "release", "__pycache__", ".git", "backups", "node_modules", "public"}


def python_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(base, name)


def step(title):
    print(f"\n=== {title}")


def check_python():
    step("Python version")
    problem = startup_checks.python_version_problem()
    print(f"Python {sys.version.split()[0]}")
    if problem and problem.fatal:
        print(problem)
        return False
    if problem:
        print(f"warning: {problem.title}")
    return True


def check_compile():
    step("Compile")
    ok = True
    for path in python_files():
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as error:
            print(error)
            ok = False
    print("all files compile" if ok else "compile errors found")
    return ok


def check_pyflakes():
    step("pyflakes (undefined names)")
    try:
        import pyflakes  # noqa: F401
    except ImportError:
        print("pyflakes not installed; skipped (pip install pyflakes)")
        return True
    result = subprocess.run([sys.executable, "-m", "pyflakes", *python_files()], capture_output=True, text=True)
    serious = [line for line in result.stdout.splitlines() if "undefined name" in line or "syntax error" in line]
    for line in serious:
        print(line)
    print("no undefined names" if not serious else f"{len(serious)} problem(s)")
    return not serious


def check_files():
    step("Data files and documentation")
    problems = startup_checks.data_file_problems(ROOT)
    missing_docs = [d for d in REQUIRED_DOCS if not os.path.isfile(os.path.join(ROOT, d))]
    for problem in problems:
        print(problem)
    for doc in missing_docs:
        print(f"missing documentation: {doc}")
    print("all present" if not problems and not missing_docs else "missing files")
    return not problems and not missing_docs


def check_tests():
    step("Tests")
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", os.path.join(ROOT, "tests")], cwd=ROOT)
    return result.returncode == 0


def check_web_tests():
    step("Web interface render tests (node)")
    import shutil
    node = shutil.which("node")
    if not node:
        print("node not installed; skipped")
        return True
    tests = [os.path.join(ROOT, "web", "tools", name) for name in ("render.test.js", "client.test.js")]
    # page.test.js (index.html in jsdom against a live server) runs from tests/test_server.py
    result = subprocess.run([node, "--test", *tests], cwd=ROOT, capture_output=True, text=True)
    summary = [line for line in result.stdout.splitlines() if line.startswith("# pass") or line.startswith("# fail")]
    print("\n".join(summary) or result.stderr.strip()[-400:])
    return result.returncode == 0


def check_site():
    step("Website build and checks")
    result = subprocess.run([sys.executable, os.path.join(ROOT, "site", "build.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
    print(result.stdout.strip().splitlines()[-1] if result.stdout.strip() else result.stderr.strip()[-300:])
    return result.returncode == 0


def check_pip():
    step("pip check")
    result = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True)
    print(result.stdout.strip() or result.stderr.strip())
    return result.returncode == 0


def _requirements_for(label):
    """requirements.txt without the lines marked for other platforms."""
    keep = []
    with open(os.path.join(ROOT, "requirements.txt"), encoding="utf-8") as handle:
        for line in handle:
            if "sys_platform" in line and (("win32" in line) != (label == "windows")):
                continue
            keep.append(line.split(";")[0].rstrip() + "\n" if ";" in line else line)
    target = os.path.join(ROOT, "build", f"requirements-{label}.txt")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.writelines(keep)
    return target


def check_wheels():
    step("Prebuilt wheels for supported interpreters")
    low, high = startup_checks.SUPPORTED_PYTHON
    ok = True
    for minor in range(low[1], high[1] + 1):
        version = f"{low[0]}.{minor}"
        for label, platforms in (("windows", ["win_amd64"]), ("linux", ["manylinux_2_28_x86_64", "manylinux2014_x86_64", "manylinux_2_17_x86_64"])):
            command = [sys.executable, "-m", "pip", "download", "--only-binary=:all:", "--no-deps", "-q",
                       "--python-version", version, "--implementation", "cp", "-r", _requirements_for(label),
                       "-d", os.path.join(ROOT, "build", "wheel-check")]
            for platform in platforms:
                command += ["--platform", platform]
            platform = label
            result = subprocess.run(command, capture_output=True, text=True)
            status = "ok" if result.returncode == 0 else "MISSING"
            print(f"Python {version} {platform}: {status}")
            if result.returncode != 0:
                print(result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "")
                ok = False
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--wheels", action="store_true", help="also verify prebuilt wheels exist (needs network)")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    checks = [check_python, check_compile, check_pyflakes, check_files]
    if not args.skip_tests:
        checks.append(check_tests)
        checks.append(check_web_tests)
    checks.append(check_site)
    checks.append(check_pip)
    if args.wheels:
        checks.append(check_wheels)
    results = [(check.__name__, check()) for check in checks]
    print("\n=== Summary")
    for name, ok in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    failed = [name for name, ok in results if not ok]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
