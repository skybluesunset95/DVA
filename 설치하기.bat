@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo --------------------------------------------------
echo   닥터빌 자동화 프로그램(DVA) 설치를 시작합니다.
echo --------------------------------------------------
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\install.ps1"

if %errorlevel% neq 0 (
    echo.
    echo ❌ 설치 중 오류가 발생했습니다.
    pause
    exit /b %errorlevel%
)

echo.
echo ✅ 모든 설치가 완료되었습니다!
pause