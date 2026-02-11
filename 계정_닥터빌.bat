@echo off
chcp 65001 >nul 2>&1
set ACCOUNT_NAME=Account1
set ACCOUNT_USERNAME=
set ACCOUNT_PASSWORD=
start /min "" pythonw main_GUI.pyw
