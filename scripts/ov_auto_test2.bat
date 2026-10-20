@echo off
chcp 65001 >nul
del /q F:\tcm\auto_result.txt 2>nul
taskkill /F /IM openviking-server.exe >nul 2>&1
ping -n 3 127.0.0.1 >nul
start "" /b cmd /c "hermes chat -q ping > F:\tcm\hermes_auto.log 2>&1"
set /a n=0
:loop
ping -n 5 127.0.0.1 >nul
curl -s -m 4 http://127.0.0.1:1933/health > F:\tcm\h.txt 2>&1
findstr /C:healthy F:\tcm\h.txt >nul
if not errorlevel 1 goto ok
set /a n+=1
if %n% GEQ 12 goto done
goto loop
:ok
echo [AUTO_HEALTH_OK] attempts=%n% >> F:\tcm\auto_result.txt
type F:\tcm\h.txt >> F:\tcm\auto_result.txt
:done
echo. >> F:\tcm\auto_result.txt
echo === PROC === >> F:\tcm\auto_result.txt
tasklist | findstr /I openviking >> F:\tcm\auto_result.txt
type F:\tcm\auto_result.txt