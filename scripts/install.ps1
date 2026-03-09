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

# 2. 계정 정보 설정 (인코딩 문제 방지를 위해 파이썬으로 위임)
python "$PSScriptRoot\account_setup.py"

exit 0

