# Builds dist\TrademarkImage.exe, a single-file Windows executable that does not need Python.
# Usage:  powershell -ExecutionPolicy Bypass -File build_exe.ps1 [-Python <path to python.exe>] [-SkipTests]
param(
    [string]$Python = "python",
    [switch]$SkipTests
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venv = Join-Path $PSScriptRoot ".venv-build"
$venvPython = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating build environment in $venv"
    & $Python -m venv $venv
    if ($LASTEXITCODE) { throw "Cannot create the virtual environment." }
}

Write-Host "Installing build requirements"
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r requirements.txt pytest "pyinstaller>=6.16" --quiet
if ($LASTEXITCODE) { throw "pip install failed." }

if (-not $SkipTests) {
    Write-Host "Running tests"
    & $venvPython -m pytest -q
    if ($LASTEXITCODE) { throw "Tests failed, the executable was not built." }
}

Write-Host "Building executable"
& $venvPython -m PyInstaller --noconfirm --clean TrademarkImage.spec
if ($LASTEXITCODE) { throw "PyInstaller failed." }

Copy-Item criterias.example.json dist\criterias.example.json -Force
Write-Host "Done: $(Join-Path $PSScriptRoot 'dist\TrademarkImage.exe')"
