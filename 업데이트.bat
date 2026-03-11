@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo --------------------------------------------------
echo   닥터빌 자동화 프로그램(DVA) 업데이트 확인
echo --------------------------------------------------
echo.

:: Python 실행 명령 찾기
set PY_CMD=python
where !PY_CMD! >nul 2>&1
if !errorlevel! neq 0 (
    set PY_CMD=py
    where !PY_CMD! >nul 2>&1
    if !errorlevel! neq 0 (
        echo ❌ Python을 찾을 수 없습니다.
        echo 먼저 [설치하기.bat]을 실행하여 Python을 설치해주세요.
        pause
        exit /b 1
    )
)

:: 필요한 패키지(requests) 설치 확인 및 자동 설치
!PY_CMD! -c "import requests" >nul 2>&1
if !errorlevel! neq 0 (
    echo 📦 업데이트에 필요한 라이브러리를 설치 중입니다...
    !PY_CMD! -m pip install requests --quiet
)

:: 업데이트 스크립트 실행
!PY_CMD! scripts/update_program.py

if !errorlevel! neq 0 (
    echo.
    echo ❌ 업데이트 도중 오류가 발생했습니다.
    echo Python 설치 상태와 인터넷 연결을 확인해주세요.
    pause
    exit /b !errorlevel!
)

exit /b 0
