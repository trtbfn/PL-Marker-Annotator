@echo off
REM Entity Annotator v2.0 - Quick Launch Script
REM Usage: run_annotator.bat [optional_file.jsonl]

echo ========================================
echo Entity Annotator v2.0
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.7 or higher.
    pause
    exit /b 1
)

REM Check if pygame is installed
python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo WARNING: pygame not found!
    echo Installing pygame...
    pip install pygame
    if errorlevel 1 (
        echo ERROR: Failed to install pygame
        pause
        exit /b 1
    )
    echo pygame installed successfully!
    echo.
)

REM Run the application
echo Starting Entity Annotator...
echo.

if "%~1"=="" (
    python main.py
) else (
    python main.py "%~1"
)

if errorlevel 1 (
    echo.
    echo ERROR: Application encountered an error
    pause
    exit /b 1
)

echo.
echo Application closed.


