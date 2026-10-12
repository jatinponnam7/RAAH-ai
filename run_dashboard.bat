@echo off
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Run setup.bat first.
    pause
    exit /b 1
)

call "venv\Scripts\activate.bat"
python -m streamlit run app.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Dashboard stopped with an error.
    echo Run doctor.bat and send the output if you need help.
    pause
)
