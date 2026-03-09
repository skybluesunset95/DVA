param()

Write-Host "Checking Python..." -ForegroundColor Cyan
python --version 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Python found!" -ForegroundColor Green
}
else {
    Write-Host "Python not found. Installing..." -ForegroundColor Yellow
    
    $pythonUrl = "https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe"
    $installerPath = "$env:TEMP\python_installer.exe"

    try {
        Write-Host "Downloading Python..." -ForegroundColor Cyan
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing
        
        Write-Host "Installing Python..." -ForegroundColor Cyan
        $process = Start-Process -FilePath $installerPath `
            -ArgumentList "/passive InstallAllUsers=1 PrependPath=1" `
            -Wait -PassThru
        
        if ($process.ExitCode -ne 0) {
            Write-Host "Installation failed with exit code: $($process.ExitCode)" -ForegroundColor Red
            Read-Host "Press Enter"
            exit 1
        }
        
        Start-Sleep -Seconds 5
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        
        Write-Host "Python installed! Reloading environment..." -ForegroundColor Green
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        # Verify installation
        Start-Sleep -Seconds 2
        python --version 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Python verification failed. Please restart your computer and try again." -ForegroundColor Red
            Read-Host "Press Enter"
            exit 1
        }
    }
    catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        Read-Host "Press Enter"
        exit 1
    }
}

Write-Host ""
Write-Host "Installing packages..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet --disable-pip-version-check
python -m pip install -r "$PSScriptRoot\requirements.txt"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Packages installed successfully!" -ForegroundColor Green
}
else {
    Write-Host "Package installation failed!" -ForegroundColor Red
    Read-Host "Press Enter"
    exit 1
}

Write-Host ""
Write-Host "Setting up account information..." -ForegroundColor Cyan
Write-Host ""

$accountName = Read-Host "계정 별칭을 입력하세요 (예: 계정1, 홍길동 - 파일명 앞에 붙을 이름입니다. 한글 가능)"
if ([string]::IsNullOrWhiteSpace($accountName)) { $accountName = "Account1" }
$accountUsername = Read-Host "닥터빌 로그인 이메일(ID)을 입력하세요"
$accountPassword = Read-Host "닥터빌 로그인 비밀번호를 입력하세요" -AsSecureString
$plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($accountPassword))

# Create account batch file
$batFileName = "$accountName`_닥터빌.bat"
$batContent = "@echo off`r`nchcp 65001 >nul 2>&1`r`nset ACCOUNT_NAME=$accountName`r`nset ACCOUNT_USERNAME=$accountUsername`r`nset ACCOUNT_PASSWORD=$plainPassword`r`nstart /min `"`" pythonw main.py"

try {
    # 한글 호환성을 위해 BOM이 포함된 UTF8로 저장 (Windows CMD 필수)
    $batContent | Out-File -FilePath $batFileName -Encoding UTF8 -Force
    Write-Host "Account file '$batFileName' created successfully!" -ForegroundColor Green
}
catch {
    Write-Host "Error creating account file: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter"
    exit 1
}

Write-Host ""
Write-Host "설정이 완료되었습니다!" -ForegroundColor Green
Write-Host "실행 방법: '$batFileName' 파일을 더블클릭하여 프로그램을 시작하세요." -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter"

