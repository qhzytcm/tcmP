@echo off
chcp 65001 >nul
set LOG=D:\ov\install2.log
set VP=D:\ov\openviking-venv\Scripts\python.exe
set IDX=https://pypi.tuna.tsinghua.edu.cn/simple
echo [START] %DATE% %TIME% > %LOG%
echo === DEFENDER EXCLUSION === >> %LOG%
powershell -NoProfile -Command "try { Add-MpPreference -ExclusionPath 'D:\ov' -ErrorAction Stop; 'EXCL_OK' } catch { 'EXCL_FAIL' }" >> %LOG% 2>&1
echo === INSTALL openviking === >> %LOG%
"%VP%" -m pip install --no-input --no-compile --no-cache-dir openviking openpyxl -i %IDX% >> %LOG% 2>&1
echo [OV] errorlevel=%ERRORLEVEL% >> %LOG%
echo === INSTALL llama wheel === >> %LOG%
"%VP%" -m pip install --no-input --no-compile --no-cache-dir D:\ov\llama_cpp_python-0.3.36-py3-none-win_amd64.whl -i %IDX% >> %LOG% 2>&1
echo [LLAMA] errorlevel=%ERRORLEVEL% >> %LOG%
echo === VERIFY === >> %LOG%
"%VP%" -c "import openviking,openpyxl,llama_cpp;print('IMPORTS_OK')" >> %LOG% 2>&1
echo [DONE] %DATE% %TIME% >> %LOG%
