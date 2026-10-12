@echo off
setlocal
cd /d "%~dp0"

echo ================================================================
echo RAAH AI - INSTALL POTHOLE MODEL
echo ================================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] This installer must be copied into your existing
    echo RAAH_AI_v2_1_FIXED\RAAH_AI_v2_1_FIXED folder.
    echo.
    echo I cannot find: venv\Scripts\python.exe
    pause
    exit /b 1
)

"venv\Scripts\python.exe" "download_pothole_model.py"

echo.
if errorlevel 1 (
    echo Model installation failed. Send ChatGPT this window.
) else (
    echo ================================================================
    echo DONE.
    echo Close any running RAAH AI dashboard and start run_dashboard.bat.
    echo ================================================================
)
pause
