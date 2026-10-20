param(
    [string]$Path = "C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\hermes-home\.env"
)
$keys = [ordered]@{
    OPENVIKING_ENDPOINT = "http://127.0.0.1:1933"
    OPENVIKING_ACCOUNT  = "default"
    OPENVIKING_USER     = "default"
    OPENVIKING_AGENT    = "hermes"
}
$txt  = if (Test-Path $Path) { Get-Content $Path -Raw -Encoding UTF8 } else { "" }
$have = @()
foreach ($l in ($txt -split "`r?`n")) {
    if ($l -match "^([A-Za-z0-9_]+)=") { $have += $matches[1] }
}
$add = @($keys.Keys | Where-Object { $have -notcontains $_ } | ForEach-Object { "$_=$($keys[$_])" })
if ($add.Count -eq 0) { "ALREADY_PRESENT"; exit 0 }
$prefix = if ($txt -and -not $txt.EndsWith("`n")) { "`r`n" } else { "" }
Add-Content -Path $Path -Value ($prefix + ($add -join "`r`n")) -Encoding UTF8 -NoNewline
"ADDED: " + ($add -join ", ")
