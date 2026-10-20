# connect_hermes_desktop.ps1 -- wire an existing Hermes install to the local OpenViking,
# then re-run the 25-case template and upload the report back to the drop server.
# Assumes bootstrap_desktop.ps1 already ran (venv + server + model in place).
# ASCII-only: PS 5.1 reads BOM-less UTF-8 as ANSI.
param(
    [string]$Base = "http://192.168.0.105:8099",
    [string]$Root = "C:\ov"
)

$ErrorActionPreference = "Continue"
$stamp  = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = Join-Path $env:USERPROFILE "Desktop"
$log    = Join-Path $logDir "ov_connect_$stamp.log"

function Log([string]$m) {
    $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $m
    Write-Host $line
    Add-Content -Path $log -Value $line -Encoding UTF8
}

function RunLogged([string]$exe, [string[]]$argList) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $out = & $exe @argList 2>&1
        $code = $LASTEXITCODE
        foreach ($o in $out) {
            if ($o -is [System.Management.Automation.ErrorRecord]) { Log ("  " + $o.Exception.Message) }
            else { Log ("  " + $o.ToString()) }
        }
        return $code
    } finally {
        $ErrorActionPreference = $prev
    }
}

function UploadLog() {
    try {
        if (Test-Path $log) {
            Invoke-RestMethod -Method Post -Uri "$Base/upload/$(Split-Path $log -Leaf)" -InFile $log -TimeoutSec 30 | Out-Null
        }
    } catch {}
}

trap {
    Log "UNHANDLED ERROR: $($_.Exception.Message)"
    Log "  at line $($_.InvocationInfo.ScriptLineNumber): $($_.InvocationInfo.Line.Trim())"
    UploadLog
    exit 1
}

function Die([string]$m) { Log "FATAL: $m"; UploadLog; exit 1 }

Log "=== Hermes <-> OpenViking wiring on $env:COMPUTERNAME ==="

# ---- 0. admin? (config lives under a user profile, but Hermes may write machine state) ----
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Log "isAdmin=$isAdmin"

# ---- 1. locate the venv created by bootstrap_desktop.ps1 ----
$venvPy = Join-Path $Root "ov-venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    $hit = Get-ChildItem -Path "$env:SystemDrive\", "D:\" -Filter "python.exe" -Recurse -Depth 4 -ErrorAction SilentlyContinue |
           Where-Object { $_.FullName -match '\\ov\\ov-venv\\Scripts\\python\.exe$' } | Select-Object -First 1
    if ($hit) { $venvPy = $hit.FullName; $Root = Split-Path (Split-Path (Split-Path $venvPy -Parent) -Parent) -Parent }
}
if (-not (Test-Path $venvPy)) { Die "OpenViking venv not found. Run bootstrap_desktop.ps1 first (expected $Root\ov-venv)." }
Log "venv python = $venvPy"
UploadLog

# ---- 2. make sure the OpenViking server is up ----
$healthy = $false
try {
    $h = Invoke-WebRequest -Uri "http://127.0.0.1:1933/health" -TimeoutSec 4 -UseBasicParsing
    if ($h.Content -match '"healthy"\s*:\s*true') { $healthy = $true; Log "server already healthy: $($h.Content)" }
} catch {}
if (-not $healthy) {
    $srvExe = Join-Path $Root "ov-venv\Scripts\openviking-server.exe"
    Log "starting openviking-server from $srvExe"
    Start-Process -FilePath $srvExe -ArgumentList "--host","127.0.0.1","--port","1933" -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $Root "server.log") -RedirectStandardError (Join-Path $Root "server.err.log")
    for ($i = 1; $i -le 40; $i++) {
        Start-Sleep -Seconds 3
        try {
            $h = Invoke-WebRequest -Uri "http://127.0.0.1:1933/health" -TimeoutSec 4 -UseBasicParsing
            if ($h.Content -match '"healthy"\s*:\s*true') { $healthy = $true; Log "HEALTH_OK after $($i*3)s"; break }
        } catch {}
        if (-not (Get-Process openviking-server -ErrorAction SilentlyContinue)) { Log "server exited at attempt $i"; break }
    }
}
if (-not $healthy) {
    $sl = Join-Path $Root "server.log"
    $tail = ""
    if (Test-Path $sl) { $tail = (Get-Content $sl -Tail 12) -join " | " }
    Die "OpenViking server not healthy. log tail: $tail"
}
UploadLog

# ---- 3. locate hermes ----
$hermes = $null
$cmd = Get-Command hermes -ErrorAction SilentlyContinue
if ($cmd) { $hermes = $cmd.Source }
if (-not $hermes) {
    foreach ($c in @("$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\hermes.exe",
                     "$env:USERPROFILE\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe")) {
        if (Test-Path $c) { $hermes = $c; break }
    }
}
if (-not $hermes) { Die "hermes CLI not found on PATH; cannot wire memory provider." }
Log "hermes = $hermes"
$null = RunLogged $hermes @("--version")

# ---- 4. config.yaml + .env locations ----
# RunLogged only logs; query again quietly to capture the actual paths as strings.
$prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
$cfgPath  = (& $hermes config path 2>$null | Select-Object -First 1)
$envPath  = (& $hermes config env-path 2>$null | Select-Object -First 1)
$ErrorActionPreference = $prev
if ($cfgPath) { $cfgPath = $cfgPath.Trim() }
if ($envPath) { $envPath = $envPath.Trim() }
if (-not $cfgPath) { $cfgPath = Join-Path $env:LOCALAPPDATA "hermes\config.yaml" }
if (-not $envPath) { $envPath = Join-Path $env:LOCALAPPDATA "hermes\.env" }
Log "config.yaml = $cfgPath"
Log ".env        = $envPath"

# ---- 5. back up config.yaml ----
if (Test-Path $cfgPath) {
    $bak = "$cfgPath.bak.$stamp"
    Copy-Item $cfgPath $bak -Force
    Log "backup -> $bak"
} else {
    Log "WARN: config.yaml not found at $cfgPath (hermes will create it)"
}

# ---- 6. set the provider (idempotent, verified on dev) ----
$rc = RunLogged $hermes @("config","set","memory.provider","openviking")
if ($rc -ne 0) { Die "hermes config set memory.provider failed (exit $rc)" }

# ---- 7. append the 4 OPENVIKING_* keys to .env, idempotently ----
$envDir = Split-Path $envPath -Parent
if (-not (Test-Path $envDir)) { New-Item -ItemType Directory -Force -Path $envDir | Out-Null }
$existing = @()
if (Test-Path $envPath) { $existing = Get-Content $envPath }
$wanted = [ordered]@{
    "OPENVIKING_ENDPOINT" = "http://127.0.0.1:1933"
    "OPENVIKING_ACCOUNT"  = "default"
    "OPENVIKING_USER"     = "default"
    "OPENVIKING_AGENT"    = "hermes"
}
$added = @()
foreach ($k in $wanted.Keys) {
    $has = $existing | Where-Object { $_ -match ("^\s*" + $k + "\s*=") }
    if (-not $has) { $added += "$($k)=$($wanted[$k])" }
}
if ($added.Count -gt 0) {
    Add-Content -Path $envPath -Value $added -Encoding UTF8
    Log "ENV ADDED: $($added.Count) keys -> $envPath"
} else {
    Log "ENV ALREADY_PRESENT (4 keys) -> $envPath"
}
UploadLog

# ---- 8. verify ----
$prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
$status = (& $hermes memory status 2>&1 | Out-String)
$ErrorActionPreference = $prev
foreach ($ln in ($status -split "`r?`n")) { if ($ln.Trim()) { Log ("  " + $ln.Trim()) } }
if ($status -notmatch 'Provider:\s*openviking') { Die "hermes memory status does not report Provider: openviking" }
if ($status -notmatch 'available') { Die "hermes memory status does not report available" }
Log "VERIFY_OK provider=openviking available"
UploadLog

# ---- 9. re-run the 25-case template ----
$tpl = Join-Path $Root "ov_custom_connectivity_test.py"
Invoke-WebRequest -Uri "$Base/ov_custom_connectivity_test.py" -OutFile $tpl -TimeoutSec 120 -UseBasicParsing
$env:OV_EXE = Join-Path $Root "ov-venv\Scripts\openviking.exe"
$env:OPENVIKING_ENDPOINT = "http://127.0.0.1:1933"
$env:OPENVIKING_ACCOUNT  = "default"
$env:OPENVIKING_USER     = "default"
$env:OPENVIKING_AGENT    = "hermes"
$reportHost = Join-Path $Root "OV-test-desktop.xlsx"
$reportDesk = Join-Path $logDir "OV-test-desktop.xlsx"
Log "running 25-case template..."
try { $rc = RunLogged $venvPy @($tpl, "--out", $reportHost) }
catch { Log "template run threw: $($_.Exception.Message)"; $rc = -1 }
Log "template exit=$rc"
UploadLog

if (Test-Path $reportHost) {
    Copy-Item $reportHost $reportDesk -Force
    Log "report copied to $reportDesk ($((Get-Item $reportDesk).Length) bytes)"
    try {
        Invoke-RestMethod -Method Post -Uri "$Base/upload/OV-test-desktop.xlsx" -InFile $reportDesk -TimeoutSec 60 | Out-Null
        Log "report uploaded"
    } catch { Log "report upload failed: $($_.Exception.Message)" }
} else {
    Log "REPORT MISSING at $reportHost"
}
UploadLog

Log "=== DONE ==="
Write-Host ""
Write-Host "Hermes -> OpenViking wiring finished." -ForegroundColor Green
Write-Host "Report: $reportDesk" -ForegroundColor Green
Write-Host "You can close this window." -ForegroundColor Green
