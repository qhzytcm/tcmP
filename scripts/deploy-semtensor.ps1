# Deploy TCM Semtensor (/semtensor/*) to tcmP production (Huawei Cloud sage-api).
# Usage: powershell -ExecutionPolicy Bypass -File scripts\deploy-semtensor.ps1 [-SkipBuild]
param([switch]$SkipBuild)
$ErrorActionPreference = "Stop"
$HOST_ = "root@114.115.211.254"
$REMOTE = "/var/www/tcm-dashboard"
$SSH = @("-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no")
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not $SkipBuild) {
    Write-Host "=== [1/5] build + verify (local) ===" -ForegroundColor Cyan
    python kg\semtensor\build_semtensor.py
    if ($LASTEXITCODE -ne 0) { throw "build failed" }
    python kg\semtensor\verify_semtensor.py
    if ($LASTEXITCODE -ne 0) { throw "verify failed" }
} else { Write-Host "=== [1/5] build skipped ===" -ForegroundColor Yellow }

Write-Host "=== [2/5] upload kg/semtensor ===" -ForegroundColor Cyan
ssh @SSH $HOST_ "mkdir -p $REMOTE/kg/semtensor"
scp @SSH -q kg\semtensor\semtensor.json kg\semtensor\axioms.py kg\semtensor\encoder.py "${HOST_}:$REMOTE/kg/semtensor/"

Write-Host "=== [3/5] upload router + mount helper ===" -ForegroundColor Cyan
scp @SSH -q api\semtensor_router.py scripts\_server_mount_semtensor.py "${HOST_}:$REMOTE/sage-api/"

Write-Host "=== [4/5] idempotent mount + restart ===" -ForegroundColor Cyan
ssh @SSH $HOST_ "cd $REMOTE/sage-api && python3 _server_mount_semtensor.py && python3 -m py_compile main.py && echo COMPILE_OK && systemctl restart sage-api && sleep 3 && systemctl is-active sage-api"

Write-Host "=== [5/5] HTTPS verify ===" -ForegroundColor Cyan
foreach ($u in @(
    "https://www.zyyywaccn.com.cn/api/sages/semtensor/health",
    "https://www.zyyywaccn.com.cn/api/sages/semtensor/spec",
    "https://www.zyyywaccn.com.cn/api/sages/semtensor/cloud?scope=domains",
    "https://www.zyyywaccn.com.cn/api/sages/semtensor/encode/DSU-00001"
)) {
    try { $r = Invoke-WebRequest -Uri $u -TimeoutSec 15 -UseBasicParsing; Write-Host ("  " + $r.StatusCode + "  " + $u) }
    catch { Write-Host ("  ERR " + $u + "  " + $_.Exception.Message) }
}
Write-Host "=== done ===" -ForegroundColor Green