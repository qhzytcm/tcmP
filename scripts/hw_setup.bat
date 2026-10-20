@echo off
chcp 65001 >nul
set LOG=D:\ov\setup.log
set VP=D:\ov\openviking-venv\Scripts
echo [START] %DATE% %TIME% > %LOG%
echo === MODEL === >> %LOG%
"%VP%\python.exe" D:\ov\dl_model.py >> %LOG% 2>&1
echo [MODEL] errorlevel=%ERRORLEVEL% >> %LOG%
echo === STARTSERVER === >> %LOG%
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
echo === LANGUAGE === >> %LOG%
"%VP%\openviking.exe" language zh-CN >> %LOG% 2>&1
echo === CUSTOM CONN === >> %LOG%
"%VP%\openviking.exe" config add custom --name huaweihw-local --url http://127.0.0.1:1933 --activate >> %LOG% 2>&1
echo [CONFADD] errorlevel=%ERRORLEVEL% >> %LOG%
"%VP%\openviking.exe" config list >> %LOG% 2>&1
echo === PATHDEPLOY === >> %LOG%
powershell -NoProfile -ExecutionPolicy Bypass -Command "$k='HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment'; $c=(Get-ItemProperty -Path $k -Name Path).Path; if (-not (@($c -split ';') -contains 'D:\ov\openviking-venv\Scripts')) { Set-ItemProperty -Path $k -Name Path -Value ((@($c -split ';') + 'D:\ov\openviking-venv\Scripts') -join ';') -Type ExpandString; 'PATH_ADDED' } else { 'PATH_PRESENT' }" >> %LOG% 2>&1
goto end
:fail
echo [FAIL] health timeout >> %LOG%
type D:\ov\server.log >> %LOG%
:end
echo [END] %DATE% %TIME% >> %LOG%
type %LOG%