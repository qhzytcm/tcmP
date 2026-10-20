@echo off
chcp 65001 >nul
echo === old layout: AppData\Local\hermes ===
if exist "C:\Users\Administrator\AppData\Local\hermes" (echo HAS_OLD_DIR) else (echo NO_OLD_DIR)
if exist "C:\Users\Administrator\AppData\Local\hermes\bin" (dir /b "C:\Users\Administrator\AppData\Local\hermes\bin") else (echo NO_OLD_BIN)
echo === search hermes.exe (old layout) ===
dir /s /b "C:\Users\Administrator\AppData\Local\hermes\hermes.exe" 2>nul
dir /s /b "C:\Users\Administrator\AppData\Local\hermes\Scripts\hermes.exe" 2>nul
echo === search hermes.exe (desktop versions) ===
dir /s /b "C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\versions\0.19.0-cn.7\hermes*" 2>nul
echo === list versions dir ===
dir /b "C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\versions" 2>nul
echo === list desktop root exe ===
dir /b "C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\*.exe" 2>nul
echo === list desktop root ===
dir /b "C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop" 2>nul
echo === config.yaml head ===
powershell -NoProfile -Command "Get-Content 'C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\hermes-home\config.yaml' -TotalCount 12"
echo === hermes-home has .env? ===
if exist "C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\hermes-home\.env" (echo HAS_ENV) else (echo NO_ENV)
