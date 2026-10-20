Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*hw_install*' -or $_.CommandLine -like '*-m pip*' } | ForEach-Object {
  Write-Output ("KILL " + $_.ProcessId + " " + $_.Name)
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Write-Output "KILL_DONE"