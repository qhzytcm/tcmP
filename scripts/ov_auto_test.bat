@echo off
chcp 65001 >nul
start "" /b cmd /c "hermes chat -q ping > F:\tcm\hermes_auto.log 2>&1"
ping -n 14 127.0.0.1 >nul
echo === HEALTH === > F:\tcm\auto_result.txt
curl -s -m 6 http://127.0.0.1:1933/health >> F:\tcm\auto_result.txt 2>&1
echo. >> F:\tcm\auto_result.txt
echo === NETSTAT === >> F:\tcm\auto_result.txt
netstat -ano | findstr :1933 >> F:\tcm\auto_result.txt
echo === PROC === >> F:\tcm\auto_result.txt
tasklist | findstr /I openviking >> F:\tcm\auto_result.txt
type F:\tcm\auto_result.txt