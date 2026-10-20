@echo off
chcp 65001 >nul
echo [START] %DATE% %TIME% > F:\tcm\ov_install.log
F:\tcm\openviking-venv\Scripts\python.exe -m pip install openviking "llama-cpp-python" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu openpyxl >> F:\tcm\ov_install.log 2>&1
echo [DONE] errorlevel=%ERRORLEVEL% >> F:\tcm\ov_install.log