@echo off
setlocal
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo First run detected - launching setup...
    call setup.bat
    if %errorlevel% neq 0 exit /b 1
)
call run_dashboard.bat
