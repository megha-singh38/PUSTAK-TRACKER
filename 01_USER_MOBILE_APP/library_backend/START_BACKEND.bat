@echo off
echo ========================================
echo Library Management System - Backend
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Check if requirements are installed
echo Checking dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
) else (
    echo Dependencies already installed.
    echo.
)

REM Run the backend
echo Starting backend server...
echo.
echo Backend will be available at: http://localhost:5001
echo API Base URL: http://localhost:5001/api
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python run.py

