@echo off
setlocal
cd /d "%~dp0"

echo =========================================
echo RAAH AI - First Time Setup
echo =========================================

set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py"
if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 set "PY=python"
)

if not defined PY (
    echo [ERROR] Python was not found.
    echo Install Python 3.10, 3.11 or 3.12 and tick "Add Python to PATH".
    pause
    exit /b 1
)

%PY% --version
if errorlevel 1 (
    echo [ERROR] Python could not start.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY% -m venv venv
    if errorlevel 1 goto :fail
)

call "venv\Scripts\activate.bat"
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail

python -m pip install -r requirements.txt
if errorlevel 1 goto :fail

if not exist detections mkdir detections
if not exist models mkdir models

echo.
echo =========================================
echo Setup completed successfully.
echo =========================================
echo Next: run doctor.bat, then run_dashboard.bat
pause
exit /b 0

:fail
echo.
echo [ERROR] Setup failed. Scroll up and copy the FIRST error line.
pause
exit /b 1
