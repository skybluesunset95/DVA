param()

Write-Host "Checking Python..." -ForegroundColor Cyan
python --version 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Python found!" -ForegroundColor Green
} else {
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
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        # Verify installation
        Start-Sleep -Seconds 2
        python --version 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Python verification failed. Please restart your computer and try again." -ForegroundColor Red
            Read-Host "Press Enter"
            exit 1
        }
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        Read-Host "Press Enter"
        exit 1
    }
}

Write-Host ""
Write-Host "Installing packages..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet --disable-pip-version-check
python -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "Packages installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Package installation failed!" -ForegroundColor Red
    Read-Host "Press Enter"
    exit 1
}

Write-Host ""
Write-Host "Setting up account information..." -ForegroundColor Cyan
Write-Host ""

$accountUsername = Read-Host "Enter ACCOUNT_USERNAME (your email)"
$accountPassword = Read-Host "Enter ACCOUNT_PASSWORD (your password)" -AsSecureString
$plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($accountPassword))

# Create account batch file
$batContent = "@echo off`r`nchcp 65001 >nul 2>&1`r`nset ACCOUNT_USERNAME=$accountUsername`r`nset ACCOUNT_PASSWORD=$plainPassword`r`nstart /min `"`" pythonw main_GUI.pyw"

try {
    $batContent | Out-File -FilePath "account.bat" -Encoding ASCII -Force
    Write-Host "Account file created successfully!" -ForegroundColor Green
} catch {
    Write-Host "Error creating account file: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter"
    exit 1
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Run: account.bat to start the program" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter"

