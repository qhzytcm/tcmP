@echo off
chcp 65001 >nul
set OV=F:\tcm\openviking-venv\Scripts\openviking.exe
%OV% language zh-CN
%OV% config add custom --name langchao-local --url http://127.0.0.1:1933 --activate
%OV% config list
%OV% health