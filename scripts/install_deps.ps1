$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$target = Join-Path $root "work\pydeps"
New-Item -ItemType Directory -Force -Path $target | Out-Null

& $python -m pip install --target $target -r (Join-Path $root "requirements.txt")

