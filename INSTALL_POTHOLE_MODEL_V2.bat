@echo off
setlocal
cd /d "%~dp0"

echo ================================================================
echo RAAH AI - POTHOLE MODEL INSTALLER V2
echo ================================================================
echo.

if not exist "venv\Scripts\python.exe" (
  echo [ERROR] Put these installer files inside your existing:
  echo RAAH_AI_v2_1_FIXED\RAAH_AI_v2_1_FIXED
  echo.
  echo Missing: venv\Scripts\python.exe
  pause
  exit /b 1
)

"venv\Scripts\python.exe" "download_pothole_model_v2.py"

echo.
if errorlevel 1 (
  echo INSTALL FAILED.
  echo Send ChatGPT this exact window.
) else (
  echo INSTALL SUCCESSFUL.
  echo Now run run_dashboard.bat.
)
pause
