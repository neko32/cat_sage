<#
.SYNOPSIS
    Launches Cat & Sage on Windows.

    Creates the local virtualenv on first run (installing the project in
    editable mode with dev extras), seeds .env from .env.example if missing,
    then forwards all arguments to `python -m cat_sage.cli`.

.EXAMPLE
    scripts\run.ps1 "Why is the sky blue?"

.EXAMPLE
    scripts\run.ps1
    # prompts interactively when no question is given
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Question
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvDir = Join-Path $root ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "No virtualenv found -- creating one at $venvDir ..."
    python -m venv $venvDir
    & $venvPython -m pip install --quiet --upgrade pip
    & $venvPython -m pip install --quiet -e "$root[dev]"
}

$envFile = Join-Path $root ".env"
$envExample = Join-Path $root ".env.example"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Write-Host "No .env found -- copying .env.example -> .env"
    Copy-Item $envExample $envFile
}

& $venvPython -m cat_sage.cli @Question
exit $LASTEXITCODE
