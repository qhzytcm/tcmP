# Deploy TCM Smart Instruments (/device/*) to tcmP production (Huawei Cloud sage-api).
param([switch]$SkipBuild)
$ErrorActionPreference = "Stop"
$HOST_ = "root@114.115.211.254"
$REMOTE = "/var/www/tcm-dashboard"
$SSH = @("-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no")
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not $SkipBuild) {
    Write-Host "=== [1/5] build + verify (local) ===" -ForegroundColor Cyan
    python kg\device\build_device.py ; if ($LASTEXITCODE -ne 0) { throw "build failed" }
    python kg\device\verify_device.py ; if ($LASTEXITCODE -ne 0) { throw "verify failed" }
} else { Write-Host "=== [1/5] build skipped ===" -ForegroundColor Yellow }

Write-Host "=== [2/5] upload kg/device ===" -ForegroundColor Cyan
ssh @SSH $HOST_ "mkdir -p $REMOTE/kg/device"
scp @SSH -q kg\device\tcm-device.json kg\device\holter.py "${HOST_}:$REMOTE/kg/device/"

Write-Host "=== [3/5] upload router + mount helper ===" -ForegroundColor Cyan
scp @SSH -q api\device_router.py scripts\_server_mount_device.py "${HOST_}:$REMOTE/sage-api/"

Write-Host "=== [4/5] idempotent mount + restart ===" -ForegroundColor Cyan
ssh @SSH $HOST_ "cd $REMOTE/sage-api && python3 _server_mount_device.py && python3 -m py_compile main.py && echo COMPILE_OK && systemctl restart sage-api && sleep 3 && systemctl is-active sage-api"

Write-Host "=== [5/5] HTTPS verify ===" -ForegroundColor Cyan
foreach ($u in @(
    "https://www.zyyywaccn.com.cn/api/sages/device/schema",
    "https://www.zyyywaccn.com.cn/api/sages/device/classes",
    "https://www.zyyywaccn.com.cn/api/sages/device/stats",
    "https://www.zyyywaccn.com.cn/api/sages/device/holter/demo"
)) {
    try { $r = Invoke-WebRequest -Uri $u -TimeoutSec 15 -UseBasicParsing; Write-Host ("  " + $r.StatusCode + "  " + $u) }
    catch { Write-Host ("  ERR " + $u + "  " + $_.Exception.Message) }
}
Write-Host "=== done ===" -ForegroundColor Green