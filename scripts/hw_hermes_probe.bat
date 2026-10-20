@echo off
chcp 65001 >nul
echo === where hermes ===
where hermes 2>nul
echo === desktop install dir ===
if exist "C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop" (echo HAS_DESKTOP_DIR) else (echo NO_DESKTOP_DIR)
echo === hermes-home ===
if exist "C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\hermes-home" (echo HAS_HOME) else (echo NO_HOME)
echo === config.yaml ===
if exist "C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\hermes-home\config.yaml" (echo HAS_CONFIG) else (echo NO_CONFIG)
echo === exe files under desktop dir ===
dir /s /b "C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\hermes.exe" 2>nul
dir /s /b "C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\*.cmd" 2>nul
echo === .hermes ===
if exist "C:\Users\Administrator\.hermes" (echo HAS_DOT_HERMES) else (echo NO_DOT_HERMES)
echo === uv tool install ===
if exist "C:\Users\Administrator\.local\share\uv\tools\hermes-agent\Scripts\hermes.exe" (echo HAS_UV_HERMES) else (echo NO_UV_HERMES)
echo === user PATH (has hermes?) ===
powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','User')"
echo === machine PATH (has hermes?) ===
powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','Machine')"
