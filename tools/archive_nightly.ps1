# Nightly wrapper for archive_history.py; see docs/operations.md.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".siq_env"
$log = Join-Path $PSScriptRoot "archive.log"

function Log($msg) { "$(Get-Date -Format s)  $msg" | Add-Content -Path $log -Encoding utf8 }

if (-not (Test-Path $envFile)) {
    Log "no .siq_env found at $envFile — skipping (create it to enable the nightly archive)"
    exit 0
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#=]+?)\s*=\s*(.*)$') {
        Set-Item -Path "env:$($Matches[1])" -Value $Matches[2]
    }
}

if (-not $env:SIQ_EMAIL -or -not $env:SIQ_PASS) {
    Log "SIQ_EMAIL / SIQ_PASS not set in .siq_env — skipping"
    exit 0
}
if (-not $env:SIQ_ARCHIVE) {
    $env:SIQ_ARCHIVE = Join-Path $root "sleepiq-archive"
}

$py = $env:SIQ_PYTHON
if (-not $py -or -not (Test-Path $py)) {
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $py) { Log "no python found (set SIQ_PYTHON in .siq_env)"; exit 1 }

$env:PYTHONIOENCODING = "utf-8"
$script = Join-Path $PSScriptRoot "archive_history.py"
Log "running archive -> $($env:SIQ_ARCHIVE)"
& $py $script *>> $log
Log "done (exit $LASTEXITCODE)"
