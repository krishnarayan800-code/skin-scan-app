@echo off
setlocal enabledelayedexpansion
echo.
echo  ============================================
echo   DermAI - Skin Analysis App
echo  ============================================
echo.

:: ── STEP 1: Find Python ──
set PYEXE=

for %%e in (py python3 python) do (
    if "!PYEXE!"=="" (
        %%e --version >nul 2>&1
        if !errorlevel! == 0 (
            for /f "tokens=*" %%v in ('%%e --version 2^>^&1') do (
                echo %%v | findstr /i "Python 3" >nul
                if !errorlevel! == 0 (
                    set PYEXE=%%e
                )
            )
        )
    )
)

if "!PYEXE!"=="" (
    echo  Python 3 not found on your system.
    echo.
    echo  Downloading Python 3.11 installer...
    echo  IMPORTANT: On the first screen of the installer,
    echo  check the box:  [x] Add Python to PATH
    echo  Then click "Install Now"
    echo.
    echo  After install finishes, close this window and
    echo  double-click start.bat again.
    echo.
    pause
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '$env:TEMP\python_installer.exe'; Start-Process '$env:TEMP\python_installer.exe' -Wait"
    echo.
    echo  Restart this bat file after Python installs.
    pause
    exit /b 1
)

echo  [OK] Python: !PYEXE!

:: ── STEP 2: Check .env ──
echo.
if not exist ".env" (
    echo ANTHROPIC_API_KEY=sk-ant-paste-your-key-here>.env
    echo PORT=5000>>.env
)

set ENVKEY=
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if /i "%%a"=="ANTHROPIC_API_KEY" set ENVKEY=%%b
)

if "!ENVKEY!"=="sk-ant-paste-your-key-here" set ENVKEY=
if "!ENVKEY!"=="" (
    echo  Get your free API key at: https://console.anthropic.com/
    echo.
    set /p NEWKEY="  Paste your Anthropic API key (sk-ant-...): "
    (echo ANTHROPIC_API_KEY=!NEWKEY!)>.env
    (echo PORT=5000)>>.env
    set ENVKEY=!NEWKEY!
)

echo  [OK] API Key set

:: ── STEP 3: Install packages ──
echo.
echo  Installing packages...
!PYEXE! -m pip install flask flask-cors anthropic --quiet --disable-pip-version-check 2>nul
echo  [OK] Packages ready

:: ── STEP 4: Launch ──
echo.
echo  ============================================
echo   Open this in your browser:
echo   http://localhost:5000
echo   Press Ctrl+C to stop the server.
echo  ============================================
echo.
start "" "http://localhost:5000"
!PYEXE! server.py
echo.
pause
