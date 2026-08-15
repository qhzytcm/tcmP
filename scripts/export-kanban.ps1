# 看板 JSON 批量导出脚本（PowerShell 兼容）
# 用法：powershell -ExecutionPolicy Bypass -File export-kanban.ps1
$ErrorActionPreference = 'SilentlyContinue'
Set-Location 'C:\Users\DELL\textbook-project'
$boards = @("textbook","tcm-epic","tcm-domain-d01","tcm-domain-d02","tcm-domain-d03","tcm-domain-d04","tcm-domain-d05","tcm-domain-d06","tcm-domain-d07","tcm-domain-d08","network-service-engineering")
$all = @()
foreach ($b in $boards) {
    hermes kanban boards switch $b | Out-Null
    $json = hermes kanban list --json 2>&1 | Out-String
    $all += "===BOARD:$b==="
    $all += $json.Trim()
}
$all -join "`n" | Out-File -FilePath 'C:\Users\DELL\textbook-project\kanban_tmp.json' -Encoding utf8
Write-Output "EXPORT_DONE $($all.Count) lines"
