# One-command build for Windows (ST-021): creates the virtual environment if needed,
# installs the pinned dependencies, then builds, verifies, and packages Iceberg.
#   .\build.ps1
$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv")) { py -3.13 -m venv .venv }
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts\build_release.py
if ($LASTEXITCODE -ne 0) { Write-Host "Build failed - see the messages above." -ForegroundColor Red; exit $LASTEXITCODE }
Write-Host "Artifacts are in .\release"
