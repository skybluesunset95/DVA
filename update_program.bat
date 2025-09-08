@echo off
chcp 65001 >nul
cd /d "%~dp0"
python update_program.py
if errorlevel 1 (
    echo.
    echo 오류가 발생했습니다. Python이 설치되어 있는지 확인해주세요.
    pause
)
