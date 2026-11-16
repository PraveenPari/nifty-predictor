@echo off
echo ============================================
echo   NIFTY PREDICTOR PRO - Python ML Version
echo ============================================
echo.

REM Check if .venv or venv exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt --quiet
)

echo.
echo Starting server...
echo Dashboard will be available at: http://localhost:5000
echo.

python app.py

pause
