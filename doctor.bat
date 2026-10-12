@echo off
setlocal
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    call "venv\Scripts\activate.bat"
    python doctor.py
) else (
    echo [ERROR] venv not found. Run setup.bat first.
    pause
)
