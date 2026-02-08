@echo off
REM Belgian TOB Tax Calculator - Startup Script
REM Double-click this file to start the calculator

echo ============================================================
echo Belgian TOB Tax Calculator
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or later from https://www.python.org
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Checking dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies may not have installed correctly
)

echo.
echo ============================================================
echo Starting TOB Calculator...
echo Server will open at: http://localhost:5000
echo ============================================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start Flask app
python app.py

REM Deactivate when done
deactivate
