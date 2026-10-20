$ErrorActionPreference = 'Stop'
$key = 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
$add = 'F:\tcm\openviking-venv\Scripts'
$cur = (Get-ItemProperty -Path $key -Name Path).Path
Write-Output ('BEFORE_LEN=' + $cur.Length)
$parts = @($cur -split ';' | Where-Object { $_ -ne '' })
if ($parts -contains $add) {
    Write-Output 'PATH_ALREADY_PRESENT'
} else {
    $new = ($parts + $add) -join ';'
    Set-ItemProperty -Path $key -Name Path -Value $new -Type ExpandString
    Write-Output 'PATH_ADDED'
}
$after = (Get-ItemProperty -Path $key -Name Path).Path
Write-Output ('AFTER_LEN=' + $after.Length)
Write-Output ('TAIL=' + $after.Substring([Math]::Max(0, $after.Length - 60)))
$expanded = [Environment]::ExpandEnvironmentVariables($after)
$env:PATH = $expanded
$hit = Get-Command openviking-server -ErrorAction SilentlyContinue
if ($hit) { Write-Output ('RESOLVE_OK=' + $hit.Source) } else { Write-Output 'RESOLVE_FAIL' }