param(
  [Parameter(Mandatory=$true)][string]$TextFile,
  [Parameter(Mandatory=$true)][string]$Out,
  [string]$Voice = "Microsoft Huihui Desktop",
  [int]$Rate = 0
)
Add-Type -AssemblyName System.Speech
$text = [System.IO.File]::ReadAllText($TextFile, [System.Text.Encoding]::UTF8)
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try { $s.SelectVoice($Voice) } catch { }
$s.Rate = $Rate
$s.SetOutputToWaveFile($Out)
$s.Speak($text)
$s.Dispose()
Write-Output ("SAPI_OK " + (Get-Item $Out).Length)
