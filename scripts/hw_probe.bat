@echo off
chcp 65001 >nul
set PY=C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe
echo === PY ===
"%PY%" --version
"%PY%" -m pip --version
echo === NET ===
"%PY%" C:\Users\Administrator\netprobe.py
echo === DONE ===