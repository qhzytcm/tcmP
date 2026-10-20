# bootstrap_desktop.ps1 -- one-shot OpenViking install + validation for a Windows box
# Pulls payload from the LAN drop server, installs OpenViking, runs the 25-case
# template, uploads the xlsx report back to the drop server.
# ASCII-only on purpose: PS 5.1 reads BOM-less UTF-8 as ANSI, so non-ASCII would break.
param(
    [string]$Base = "http://192.168.0.105:8099"
)

$ErrorActionPreference = "Continue"
$stamp  = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = Join-Path $env:USERPROFILE "Desktop"
$log    = Join-Path $logDir "ov_bootstrap_$stamp.log"

function Log([string]$m) {
    $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $m
    Write-Host $line
    Add-Content -Path $log -Value $line -Encoding UTF8
}

# Run an external command, log its stdout AND stderr as readable text.
# (Plain `2>&1 | ForEach-Object` turns stderr into "RemoteException" and hides the message.)
function RunLogged([string]$exe, [string[]]$argList) {
    # EAP=Stop + native stderr redirected turns into a terminating NativeCommandError on PS 5.1,
    # which used to kill the whole bootstrap. Relax it locally and restore afterwards.
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

# Upload the log so the operator can see progress even if this script dies mid-way.
function UploadLog() {
    try {
        if (Test-Path $log) {
            $leaf = Split-Path $log -Leaf
            Invoke-RestMethod -Method Post -Uri "$Base/upload/$leaf" -InFile $log -TimeoutSec 30 | Out-Null
        }
    } catch {}
}

# Any terminating error: record it with file/line, push the log, then stop.
trap {
    $where = "line $($_.InvocationInfo.ScriptLineNumber): $($_.InvocationInfo.Line.Trim())"
    Log "UNHANDLED ERROR: $($_.Exception.Message)"
    Log "  at $where"
    UploadLog
    exit 1
}

function Die([string]$m) {
    Log "FATAL: $m"
    try { Invoke-RestMethod -Method Post -Uri "$Base/upload/ov_bootstrap_$stamp.log" -InFile $log -TimeoutSec 20 | Out-Null } catch {}
    throw $m
}

Log "=== OpenViking bootstrap on $env:COMPUTERNAME ==="
Log "base=$Base  log=$log"

# ---- 0. admin? ----
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Log "isAdmin=$isAdmin"
if (-not $isAdmin) { Die "must run as Administrator (right-click -> Run as administrator)" }

# ---- 1. pick a work root with enough free space ----
$root = $null
foreach ($d in @("C:", "D:", "E:", "F:")) {
    try {
        $drv = Get-PSDrive -Name $d.TrimEnd(":") -ErrorAction Stop
        $freeGB = [math]::Round($drv.Free / 1GB, 1)
        Log ("drive {0} free={1} GB" -f $d, $freeGB)
        if ($freeGB -ge 8 -and -not $root) { $root = "$d\ov" }
    } catch {}
}
if (-not $root) { Die "no drive with >= 8 GB free" }
New-Item -ItemType Directory -Force -Path $root | Out-Null
Log "work root = $root"

# ---- 2. find python ----
$cands = @(
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "C:\Python314\python.exe",
    "C:\Python313\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe",
    "C:\Program Files\Python311\python.exe",
    "C:\ProgramData\Anaconda3\python.exe"
)
$py = $null
foreach ($c in $cands) { if (Test-Path $c) { $py = $c; break } }
if (-not $py) {
    $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source }
}
if ($py) {
    $ver = (& $py --version 2>&1) -join " "
    Log "python = $py  ($ver)"
    $major = (& $py -c "import sys;print(sys.version_info[0])").Trim()
    $minor = (& $py -c "import sys;print(sys.version_info[1])").Trim()
    if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 10)) {
        Log "python too old ($major.$minor), will install 3.11"
        $py = $null
    }
}
if (-not $py) {
    Log "no suitable python -> installing Python 3.11.9 from huaweicloud mirror"
    $inst = Join-Path $env:TEMP "python-3.11.9-amd64.exe"
    try {
        Invoke-WebRequest -Uri "https://mirrors.huaweicloud.com/python/3.11.9/python-3.11.9-amd64.exe" -OutFile $inst -TimeoutSec 600 -UseBasicParsing
    } catch { Die "cannot download python installer: $($_.Exception.Message)" }
    Log "installer downloaded, silent install..."
    Start-Process -FilePath $inst -ArgumentList "/quiet","InstallAllUsers=0","PrependPath=1","Include_pip=1" -Wait
    $py = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
    if (-not (Test-Path $py)) { Die "python install did not produce $py" }
    Log "python installed: $py"
}

# ---- 3. venv + packages ----
$venv   = Join-Path $root "ov-venv"
$venvPy = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Log "creating venv at $venv"
    & $py -m venv $venv
    if ($LASTEXITCODE -ne 0) { Die "venv creation failed" }
}
$tuna = "https://pypi.tuna.tsinghua.edu.cn/simple"
Log "pip install openviking openpyxl (tuna mirror)..."
$rc = RunLogged $venvPy @("-m","pip","install","-q","--no-input","--index-url",$tuna,"openviking","openpyxl")
if ($rc -ne 0) { Die "pip install openviking failed (exit $rc)" }

Log "pip install llama-cpp-python wheel from LAN drop..."
$rc = RunLogged $venvPy @("-m","pip","install","-q","--no-input","$Base/llama_cpp_python-0.3.36-py3-none-win_amd64.whl")
if ($rc -ne 0) { Die "pip install llama wheel failed (exit $rc)" }

$null = RunLogged $venvPy @("-c","import openviking, openpyxl, llama_cpp; print('IMPORTS_OK')")

# ---- 4. ov.conf ----
$ovDir = Join-Path $env:USERPROFILE ".openviking"
New-Item -ItemType Directory -Force -Path $ovDir | Out-Null
$ws = ($root -replace "\\", "/") + "/data"
$conf = @"
{
  "default_account": "default",
  "default_user": "default",
  "output_language_override": "zh-CN",
  "storage": {
    "workspace": "$ws",
    "agfs": { "backend": "local" },
    "vectordb": { "backend": "local" }
  },
  "embedding": { "dense": { "provider": "local", "model": "bge-small-zh-v1.5-f16" } }
}
"@
$confPath = Join-Path $ovDir "ov.conf"
# MUST be BOM-less: OpenViking's JSON parser rejects a UTF-8 BOM with
# "expected value at line 1 column 1". PowerShell 5.1's Set-Content -Encoding UTF8 ADDS a BOM.
[System.IO.File]::WriteAllText($confPath, $conf, (New-Object System.Text.UTF8Encoding($false)))
Log "ov.conf written BOM-less (workspace=$ws)"
$rc = RunLogged $venvPy @("-c", "import io,json;json.load(io.open(r'$confPath',encoding='utf-8'));print('CONF_JSON_OK')")
if ($rc -ne 0) { Die "ov.conf is not valid JSON (likely a BOM): $confPath" }
UploadLog

# ---- 5. embedding model ----
$mdir = Join-Path $env:USERPROFILE ".cache\openviking\models"
New-Item -ItemType Directory -Force -Path $mdir | Out-Null
$mfile = Join-Path $mdir "bge-small-zh-v1.5-f16.gguf"
if ((Test-Path $mfile) -and ((Get-Item $mfile).Length -gt 47000000)) {
    Log "model already present: $((Get-Item $mfile).Length) bytes"
} else {
    Log "downloading model from hf-mirror (46 MB)..."
    try {
        Invoke-WebRequest -Uri "https://hf-mirror.com/CompendiumLabs/bge-small-zh-v1.5-gguf/resolve/main/bge-small-zh-v1.5-f16.gguf" -OutFile $mfile -TimeoutSec 900 -UseBasicParsing
    } catch { Die "model download failed: $($_.Exception.Message)" }
    Log "model size = $((Get-Item $mfile).Length)"
}

# ---- 6. start server ----
$srvExe = Join-Path $venv "Scripts\openviking-server.exe"
Get-Process openviking-server -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Log "starting openviking-server on 127.0.0.1:1933"
Start-Process -FilePath $srvExe -ArgumentList "--host","127.0.0.1","--port","1933" -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $root "server.log") -RedirectStandardError (Join-Path $root "server.err.log")

$healthy = $false
for ($i = 1; $i -le 60; $i++) {
    Start-Sleep -Seconds 3
    try {
        $h = Invoke-WebRequest -Uri "http://127.0.0.1:1933/health" -TimeoutSec 4 -UseBasicParsing
        if ($h.Content -match '"healthy"\s*:\s*true') { $healthy = $true; Log "HEALTH_OK after $($i*3)s : $($h.Content)"; break }
    } catch {}
    if (-not (Get-Process openviking-server -ErrorAction SilentlyContinue)) {
        Log "server process exited at attempt $i -- aborting early instead of waiting 3 min"
        break
    }
}
UploadLog
if (-not $healthy) {
    $tail = ""
    $sl = Join-Path $root "server.log"
    if (Test-Path $sl) { $tail = (Get-Content $sl -Tail 20) -join " | " }
    Die "server never became healthy. log tail: $tail"
}

# ---- 7. custom connection ----
$ovExe = Join-Path $venv "Scripts\openviking.exe"
& $ovExe language zh-CN 2>&1 | ForEach-Object { Log "  $_" }
& $ovExe config add custom --name desktop-local --url http://127.0.0.1:1933 --activate 2>&1 | ForEach-Object { Log "  $_" }
& $ovExe config list 2>&1 | ForEach-Object { Log "  $_" }

# ---- 8. Hermes detect ----
$hermesHome = $null; $hermesExe = $null
$desk = Join-Path $env:LOCALAPPDATA "Hermes Agent CN Desktop"
if (Test-Path (Join-Path $desk "data\hermes-home")) {
    $hermesHome = Join-Path $desk "data\hermes-home"
    $rt = Get-ChildItem -Path (Join-Path $desk "data\versions") -Filter "hermes-agent-cn-runtime-win32-x64.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($rt) { $hermesExe = $rt.FullName }
}
if (-not $hermesHome -and (Test-Path (Join-Path $env:LOCALAPPDATA "hermes"))) {
    $hermesHome = Join-Path $env:LOCALAPPDATA "hermes"
}
Log "hermesHome=$hermesHome"
Log "hermesExe=$hermesExe"

# ---- 9. run template ----
$tpl = Join-Path $root "ov_custom_connectivity_test.py"
Invoke-WebRequest -Uri "$Base/ov_custom_connectivity_test.py" -OutFile $tpl -TimeoutSec 120 -UseBasicParsing
$env:OV_EXE = $ovExe
$env:OPENVIKING_ENDPOINT = "http://127.0.0.1:1933"
$env:OPENVIKING_ACCOUNT  = "default"
$env:OPENVIKING_USER     = "default"
$env:OPENVIKING_AGENT    = "hermes"
if ($hermesHome) { $env:HERMES_HOME = $hermesHome }
if ($hermesExe)  { $env:HERMES_EXE  = $hermesExe }
$reportHost = Join-Path $root "OV-test-desktop.xlsx"
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
    } catch { Log "upload report failed: $($_.Exception.Message)" }
} else {
    Log "REPORT MISSING"
}
UploadLog

# ---- 10. if a Hermes install exists, wire it and re-run so the report shows full parity ----
# Delegates to connect_hermes_desktop.ps1 so the wiring logic lives in exactly one file.
$hermesCmd = Get-Command hermes -ErrorAction SilentlyContinue
if ($hermesCmd) {
    Log "hermes found ($($hermesCmd.Source)) -> delegating memory wiring"
    try {
        $conn = Join-Path $root "connect_hermes_desktop.ps1"
        Invoke-WebRequest -Uri "$Base/connect_hermes_desktop.ps1" -OutFile $conn -TimeoutSec 60 -UseBasicParsing
        & powershell -NoProfile -ExecutionPolicy Bypass -File $conn -Base $Base -Root $root
        Log "wiring step exit=$LASTEXITCODE"
    } catch {
        Log "wiring step failed (non-fatal, base report already uploaded): $($_.Exception.Message)"
    }
} else {
    Log "no hermes CLI on PATH -> skipping memory wiring"
}
try {
    Invoke-RestMethod -Method Post -Uri "$Base/upload/ov_bootstrap_$stamp.log" -InFile $log -TimeoutSec 30 | Out-Null
    Log "log uploaded"
} catch {}

Log "=== DONE ==="
Write-Host ""
Write-Host "Finished. Report on this machine: $reportDesk" -ForegroundColor Green
Write-Host "Also uploaded to $Base (checked by the operator)." -ForegroundColor Green
Write-Host "You can close this window." -ForegroundColor Green
