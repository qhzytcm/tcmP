@echo off
chcp 65001 >nul
set LOG=F:\tcm\ov_e2e.log
echo [START] %DATE% %TIME% > %LOG%
start "" /b cmd /c "F:\tcm\openviking-venv\Scripts\openviking-server.exe --host 127.0.0.1 --port 1933 > F:\tcm\ov_server.log 2>&1"
set /a n=0
:waitloop
ping -n 4 127.0.0.1 >nul
curl -s -o NUL -m 3 http://127.0.0.1:1933/health
if errorlevel 1 goto waitmore
goto ready
:waitmore
set /a n+=1
if %n% GEQ 50 goto fail
goto waitloop
:ready
echo [HEALTH_OK] attempts=%n% >> %LOG%
curl -s -m 5 http://127.0.0.1:1933/health >> %LOG%
echo. >> %LOG%
set OV=F:\tcm\openviking-venv\Scripts\openviking.exe
%OV% language zh-CN >> %LOG% 2>&1
%OV% config add custom --name langchao-local --url http://127.0.0.1:1933 --activate >> %LOG% 2>&1
echo [CONFIG_ADD] errorlevel=%ERRORLEVEL% >> %LOG%
%OV% config list >> %LOG% 2>&1
%OV% health >> %LOG% 2>&1
set OV_EXE=%OV%
set OPENVIKING_ENDPOINT=http://127.0.0.1:1933
set OPENVIKING_ACCOUNT=default
set OPENVIKING_USER=default
set OPENVIKING_AGENT=hermes
set HERMES_HOME=F:\tcm\no-hermes
F:\tcm\openviking-venv\Scripts\python.exe F:\tcm\ov_custom_connectivity_test.py --out F:\tcm\OV-test-langchao.xlsx >> %LOG% 2>&1
echo [TESTDONE] errorlevel=%ERRORLEVEL% >> %LOG%
goto end
:fail
echo [FAIL] health timeout >> %LOG%
:end
echo [END] %DATE% %TIME% >> %LOG%