@echo off
chcp 65001 >nul
set OV_EXE=F:\tcm\openviking-venv\Scripts\openviking.exe
set OPENVIKING_ENDPOINT=http://127.0.0.1:1933
set OPENVIKING_ACCOUNT=default
set OPENVIKING_USER=default
set OPENVIKING_AGENT=hermes
set HERMES_HOME=F:\tcm\no-hermes
F:\tcm\openviking-venv\Scripts\python.exe F:\tcm\ov_custom_connectivity_test.py --out F:\tcm\OV-test-langchao.xlsx > F:\tcm\ov_test.log 2>&1
echo [TESTDONE] errorlevel=%ERRORLEVEL% >> F:\tcm\ov_test.log