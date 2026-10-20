@echo off
chcp 65001 >nul
set RT=C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\versions\0.19.0-cn.7\hermes-agent-cn-runtime-win32-x64.exe
echo === exists ===
if exist "%RT%" (echo RT_EXISTS) else (echo RT_MISSING)
echo === version ===
"%RT%" --version 2>&1
echo === memory status ===
call :runms
goto :eof
:runms
set HERMES_HOME=C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\hermes-home
"%RT%" memory status 2>&1
goto :eof
