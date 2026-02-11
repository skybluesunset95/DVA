@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title 닥터빌 자동화 프로그램 설치

echo.
echo ========================================
echo    닥터빌 자동화 프로그램 설치
echo ========================================
echo.

REM ========================================
REM 1단계: Python 설치 여부 확인
REM ========================================
echo [1/3] Python 설치 여부 확인 중...
echo.

python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo ✓ Python이 이미 설치되어 있습니다. (버전: %PYTHON_VERSION%)
    goto :install_packages
)

echo Python이 설치되어 있지 않습니다.
echo.
echo Python을 자동으로 설치합니다...
echo (관리자 권한이 필요할 수 있습니다)
echo.

REM Python 설치 프로그램 다운로드 및 실행
set PYTHON_VERSION=3.11.7
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe
set PYTHON_INSTALLER=python_installer.exe

echo Python 설치 프로그램 다운로드 중...
powershell -ExecutionPolicy Bypass -NoProfile -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
     try { ^
         $ProgressPreference = 'SilentlyContinue'; ^
         Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing; ^
         Write-Host '다운로드 완료' ^
     } catch { ^
         Write-Host '다운로드 실패: ' $_.Exception.Message; ^
         exit 1 ^
     }"

if not exist "%PYTHON_INSTALLER%" (
    echo.
    echo 오류: Python 설치 프로그램 다운로드에 실패했습니다.
    echo 인터넷 연결을 확인하거나 수동으로 Python을 설치해주세요.
    echo Python 다운로드: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo.
echo Python 설치 중... (조용히 설치됩니다)
echo 설치가 완료될 때까지 기다려주세요...
echo.

REM Python 설치 (조용히 설치, PATH에 추가, 모든 사용자용)
start /wait "" "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0

REM 설치 프로그램 삭제
if exist "%PYTHON_INSTALLER%" del "%PYTHON_INSTALLER%"

REM PATH 새로고침 시도
call refreshenv.cmd 2>nul
if not exist refreshenv.cmd (
    REM 일반적인 Python 경로 추가
    set "PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"
    set "PATH=%PATH%;C:\Python311;C:\Python311\Scripts"
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311"
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
)

echo.
echo Python 설치가 완료되었습니다!
echo PATH를 새로고침하기 위해 잠시 대기합니다...
timeout /t 3 /nobreak >nul

REM Python 설치 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 경고: Python이 설치되었지만 PATH에 등록되지 않았을 수 있습니다.
    echo 이 창을 닫고 새로 열어서 다시 실행하거나,
    echo 수동으로 Python을 설치해주세요.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python 설치 확인됨 (버전: %PYTHON_VERSION%)
echo.

REM ========================================
REM 2단계: 필요한 패키지 설치
REM ========================================
:install_packages
echo [2/3] 필요한 패키지 설치 중...
echo.

REM pip upgrade
echo pip upgrade in progress...
python -m pip install --upgrade pip --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo Warning: pip upgrade failed. Continuing...
    echo.
)

REM requirements.txt 확인
if not exist "requirements.txt" (
    echo 오류: requirements.txt 파일을 찾을 수 없습니다.
    echo.
    pause
    exit /b 1
)

echo Installing required packages... (This may take a while)
echo.
python -m pip install -r requirements.txt --disable-pip-version-check

if %errorlevel% equ 0 (
    echo.
    echo ✓ 패키지 설치 완료!
) else (
    echo.
    echo Warning: Some packages may have failed to install.
    echo If you encounter errors when running the program, manually run:
    echo   python -m pip install -r requirements.txt
    echo.
)

echo.

REM ========================================
REM 3단계: 계정 설정 파일 열기
REM ========================================
echo [3/3] 계정 설정
echo.

if not exist "계정_닥터빌.bat" (
    echo 경고: 계정_닥터빌.bat 파일을 찾을 수 없습니다.
    echo.
    goto :end
)

echo 계정_닥터빌.bat 파일을 엽니다...
echo.
echo 다음 정보를 입력해주세요:
echo   - ACCOUNT_NAME: 계정 이름 (예: Account1, 내계정)
echo   - ACCOUNT_USERNAME: 로그인 이메일 주소
echo   - ACCOUNT_PASSWORD: 로그인 비밀번호
echo.
echo 파일을 저장한 후 닫으면 계속됩니다...
echo.

REM 메모장으로 계정 파일 열기
start /wait notepad "계정_닥터빌.bat"

echo.
echo ✓ 계정 설정 완료!
echo.

:end
echo ========================================
echo    설치 완료!
echo ========================================
echo.
echo 다음 단계:
echo 1. 계정_닥터빌.bat 파일에 계정 정보가 올바르게 입력되었는지 확인하세요.
echo 2. 계정_닥터빌.bat 파일을 더블클릭하여 프로그램을 실행하세요.
echo.
echo Chrome 브라우저가 설치되어 있어야 합니다.
echo.
pause

