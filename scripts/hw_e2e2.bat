@echo off
chcp 65001 >nul
set LOG=D:\ov\e2e2.log
set VP=D:\ov\openviking-venv\Scripts
set OV_EXE=%VP%\openviking.exe
set OPENVIKING_ENDPOINT=http://127.0.0.1:1933
set OPENVIKING_ACCOUNT=default
set OPENVIKING_USER=default
set OPENVIKING_AGENT=hermes
set HERMES_HOME=C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\hermes-home
set HERMES_EXE=C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\versions\0.19.0-cn.7\hermes-agent-cn-runtime-win32-x64.exe
echo [START] %DATE% %TIME% > %LOG%
taskkill /F /IM openviking-server.exe >nul 2>&1
ping -n 3 127.0.0.1 >nul
echo === START SERVER === >> %LOG%
start "" /b D:\ov\hw_server.bat
set /a n=0
:waitloop
ping -n 4 127.0.0.1 >nul
"%VP%\python.exe" D:\ov\health.py
if errorlevel 1 goto waitmore
goto ready
:waitmore
set /a n+=1
if %n% GEQ 60 goto fail
goto waitloop
:ready
echo [HEALTH_OK] attempts=%n% >> %LOG%
echo === RUN TEST === >> %LOG%
"%VP%\python.exe" D:\ov\ov_custom_connectivity_test.py --out D:\ov\OV-test-huaweihw.xlsx >> %LOG% 2>&1
echo [TESTDONE] errorlevel=%ERRORLEVEL% >> %LOG%
goto end
:fail
echo [FAIL] health timeout >> %LOG%
type D:\ov\server.log >> %LOG%
:end
echo [END] %DATE% %TIME% >> %LOG%
type %LOG%
