# Deploy TCM Informatics (/informatics/*) to tcmP production (Huawei Cloud sage-api).
# Usage: powershell -ExecutionPolicy Bypass -File scripts\deploy-informatics.ps1 [-SkipBuild]
param([switch]$SkipBuild)
$ErrorActionPreference = "Stop"
$HOST_ = "root@114.115.211.254"
$REMOTE = "/var/www/tcm-dashboard"
$SSH = @("-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no")
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not $SkipBuild) {
    Write-Host "=== [1/5] build + verify (local) ===" -ForegroundColor Cyan
    python scripts\build_informatics.py
    if ($LASTEXITCODE -ne 0) { throw "build failed" }
    python scripts\verify_informatics.py
    if ($LASTEXITCODE -ne 0) { throw "verify failed" }
} else { Write-Host "=== [1/5] build skipped ===" -ForegroundColor Yellow }

Write-Host "=== [2/5] upload kg/informatics ===" -ForegroundColor Cyan
ssh @SSH $HOST_ "mkdir -p $REMOTE/kg/informatics"
scp @SSH -q kg\informatics\tcm-informatics.json kg\informatics\schema.json kg\informatics\tcm_mining.py "${HOST_}:$REMOTE/kg/informatics/"

Write-Host "=== [3/5] upload router + mount helper ===" -ForegroundColor Cyan
scp @SSH -q api\informatics_router.py scripts\_server_mount_informatics.py "${HOST_}:$REMOTE/sage-api/"

Write-Host "=== [4/5] idempotent mount + restart ===" -ForegroundColor Cyan
ssh @SSH $HOST_ "cd $REMOTE/sage-api && python3 _server_mount_informatics.py && python3 -m py_compile main.py && echo COMPILE_OK && systemctl restart sage-api && sleep 3 && systemctl is-active sage-api"

Write-Host "=== [5/5] HTTPS verify ===" -ForegroundColor Cyan
$kw = [uri]::EscapeDataString("失眠")
foreach ($u in @(
    "https://www.zyyywaccn.com.cn/api/sages/informatics/stats",
    "https://www.zyyywaccn.com.cn/api/sages/informatics/standards",
    "https://www.zyyywaccn.com.cn/api/sages/informatics/operators",
    "https://www.zyyywaccn.com.cn/api/sages/informatics/dist/six_channel",
    "https://www.zyyywaccn.com.cn/api/sages/informatics/rules/symptom_to_syndrome",
    "https://www.zyyywaccn.com.cn/api/sages/informatics/clusters",
    "https://www.zyyywaccn.com.cn/api/sages/informatics/coverage",
    "https://www.zyyywaccn.com.cn/api/sages/informatics/quality"
)) {
    try { $r = Invoke-WebRequest -Uri $u -TimeoutSec 15 -UseBasicParsing; Write-Host ("  " + $r.StatusCode + "  " + $u) }
    catch { Write-Host ("  ERR " + $u + "  " + $_.Exception.Message) }
}
try { $r = Invoke-WebRequest -Uri ("https://www.zyyywaccn.com.cn/api/sages/informatics/retrieve?q=" + $kw) -TimeoutSec 15 -UseBasicParsing
      Write-Host ("  " + $r.StatusCode + "  retrieve?q=shimian") } catch { Write-Host ("  ERR retrieve " + $_.Exception.Message) }
Write-Host "=== done ===" -ForegroundColor Green