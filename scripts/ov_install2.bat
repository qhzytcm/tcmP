@echo off
chcp 65001 >nul
echo [START] %DATE% %TIME% > F:\tcm\ov_install2.log
F:\tcm\openviking-venv\Scripts\python.exe -m pip install openviking openpyxl >> F:\tcm\ov_install2.log 2>&1
echo [STEP1] errorlevel=%ERRORLEVEL% >> F:\tcm\ov_install2.log
F:\tcm\openviking-venv\Scripts\python.exe -m pip install F:\tcm\llama_cpp_python-0.3.36-py3-none-win_amd64.whl --no-index >> F:\tcm\ov_install2.log 2>&1
echo [STEP2] errorlevel=%ERRORLEVEL% >> F:\tcm\ov_install2.log
echo [DONE] >> F:\tcm\ov_install2.log