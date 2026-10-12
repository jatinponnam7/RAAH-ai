@echo off
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

call "venv\Scripts\activate.bat"
python live_detect.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Live detector stopped with an error.
    pause
)
