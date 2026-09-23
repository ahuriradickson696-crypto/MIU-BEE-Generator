@echo off
title MIU BEE Slide Generator
cd /d "%~dp0"

echo ============================================================
echo   Metropolitan International University
echo   BEE Slide Generator
echo ============================================================
echo.

REM --- Check for venv ---
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] .venv not found.
    echo.
    echo Create it first:
    echo   py -3.12 -m venv .venv
    echo   .venv\Scripts\activate
    echo   python -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM --- Activate venv ---
call ".venv\Scripts\activate.bat"

REM --- Sanity check .env ---
if not exist ".env" (
    echo [ERROR] .env file not found. Add your API keys first.
    pause
    exit /b 1
)

REM --- Run the generator ---
echo Starting generation...
echo.
python gen_topic.py

echo.
echo ============================================================
echo   DONE. Check the "output_slides" folder.
echo ============================================================
pause