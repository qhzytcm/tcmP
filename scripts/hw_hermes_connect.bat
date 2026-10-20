@echo off
chcp 65001 >nul
set RT=C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\versions\0.19.0-cn.7\hermes-agent-cn-runtime-win32-x64.exe
set HH=C:\Users\Administrator\AppData\Local\Hermes Agent CN Desktop\data\hermes-home
set HERMES_HOME=%HH%
set LOG=D:\ov\hermes_connect.log
echo [START] %DATE% %TIME% > %LOG%
echo === BACKUP === >> %LOG%
copy /y "%HH%\config.yaml" "%HH%\config.yaml.bak.ov" >> %LOG% 2>&1
copy /y "%HH%\.env" "%HH%\.env.bak.ov" >> %LOG% 2>&1
echo === CONFIG SET === >> %LOG%
"%RT%" config set memory.provider openviking >> %LOG% 2>&1
"%RT%" config set memory.openviking.endpoint http://127.0.0.1:1933 >> %LOG% 2>&1
"%RT%" config set memory.openviking.agent hermes >> %LOG% 2>&1
echo === ENV APPEND === >> %LOG%
powershell -NoProfile -ExecutionPolicy Bypass -File D:\ov\append_env.ps1 >> %LOG% 2>&1
echo === STATUS === >> %LOG%
"%RT%" memory status >> %LOG% 2>&1
echo === DONE === >> %LOG%
type %LOG%
