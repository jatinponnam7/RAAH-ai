@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo RAAH AI - APP PATCH
echo ==========================================

if not exist "app_fixed.py" (
  echo [ERROR] app_fixed.py is missing.
  pause
  exit /b 1
)

if exist "app.py" (
  copy /Y "app.py" "app_before_patch.py" >nul
  echo [OK] Backed up old app.py as app_before_patch.py
)

copy /Y "app_fixed.py" "app.py" >nul
if errorlevel 1 (
  echo [ERROR] Could not replace app.py
  pause
  exit /b 1
)

findstr /C:"Webcam Snapshot" "app.py" >nul
if errorlevel 1 (
  echo [ERROR] Patch verification failed.
  pause
  exit /b 1
)

echo [OK] app.py replaced successfully.
echo [OK] Webcam Snapshot tab verified.
echo.
echo Now launch run_dashboard.bat from this same folder.
echo.
pause
