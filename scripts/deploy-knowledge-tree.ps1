# Deploy the TCM Knowledge Tree to tcmP production (Huawei Cloud sage-api).
# Usage (Windows dev machine):
#   cd C:\Users\DELL\tcmP
#   powershell -ExecutionPolicy Bypass -File scripts\deploy-knowledge-tree.ps1
# Options:
#   -Host root@114.115.211.254   (default)
#   -SkipBuild                   reuse current kg/tree artifacts (no local rebuild)
#
# Steps: upload data/engine/router -> inject mount block -> restart sage-api -> HTTPS verify.
# NOTE: ASCII-only on purpose (Windows PowerShell 5.1 misparses BOM-less UTF-8 script files).
param(
    [string]$SshHost = "root@114.115.211.254",
    [switch]$SkipBuild
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$base = "/var/www/tcm-dashboard"

Write-Host "=== [1/5] local rebuild (optional) ===" -ForegroundColor Cyan
if (-not $SkipBuild) {
    python scripts\build_knowledge_tree.py
    python scripts\verify_knowledge_tree.py | Select-Object -Last 2
}

Write-Host "=== [2/5] mkdir + upload data/engine ===" -ForegroundColor Cyan
ssh $SshHost "mkdir -p $base/kg/tree"
scp kg\tree\tcm-knowledge-tree.json kg\tree\schema.json kg\tree\tcm_tree.py "${SshHost}:$base/kg/tree/"

Write-Host "=== [3/5] upload router + mount helper ===" -ForegroundColor Cyan
scp api\tree_router.py "${SshHost}:$base/sage-api/tree_router.py"
scp scripts\_server_mount_tree.py "${SshHost}:/tmp/_server_mount_tree.py"

Write-Host "=== [4/5] inject mount block + restart sage-api ===" -ForegroundColor Cyan
ssh $SshHost "/root/.local/share/uv/tools/hermes-agent/bin/python3 /tmp/_server_mount_tree.py"

Write-Host "=== [5/5] HTTPS verify ===" -ForegroundColor Cyan
$kw = [uri]::EscapeDataString("桂枝")
foreach ($u in @(
    "https://www.zyyywaccn.com.cn/api/sages/tree/stats",
    "https://www.zyyywaccn.com.cn/api/sages/tree/node/D07-S04",
    "https://www.zyyywaccn.com.cn/api/sages/tree/neighbors/DSU-00001",
    "https://www.zyyywaccn.com.cn/api/sages/tree/search?q=$kw"
)) {
    try {
        $r = Invoke-WebRequest -Uri $u -TimeoutSec 10 -UseBasicParsing
        $body = [System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
        Write-Host ("  OK  [{0}] {1}" -f $r.StatusCode, ($body.Substring(0, [Math]::Min(200, $body.Length))))
    } catch {
        Write-Host ("  ERR  {0}  {1}" -f $u, $_.Exception.Message) -ForegroundColor Red
    }
}
Write-Host "deploy done." -ForegroundColor Green
