@echo off
setlocal enabledelayedexpansion
title MIU BEE — Full Pipeline
cd /d "%~dp0"

echo ============================================================
echo   Metropolitan International University
echo   BEE Slide Generator — FULL PIPELINE
echo ============================================================
echo.
echo   This will run:
echo     1. Generate slides from curriculum (uses AI)
echo     2. Check progress
echo     3. Convert all pptx to PDF
echo     4. Clean up junk files
echo.
echo ============================================================
echo.

REM --- Check for venv ---
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] .venv not found.
    echo Create it first:
    echo   py -3.12 -m venv .venv
    echo   .venv\Scripts\activate
    echo   python -m pip install -r requirements.txt
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

REM --- Step 1: Generate ---
echo.
echo ------------------------------------------------------------
echo   STEP 1 / 4 — Generating slides
echo ------------------------------------------------------------
echo.
python gen_topic.py

if errorlevel 1 (
    echo.
    echo [WARN] Generator exited with an error.
    echo Continuing with remaining steps anyway...
)

REM --- Step 2: Progress ---
echo.
echo ------------------------------------------------------------
echo   STEP 2 / 4 — Progress Report
echo ------------------------------------------------------------
echo.
python check_progress.py

REM --- Step 3: Convert to PDF ---
echo.
echo ------------------------------------------------------------
echo   STEP 3 / 4 — Converting to PDF
echo ------------------------------------------------------------
echo.
if exist "convert_to_pdf.py" (
    python convert_to_pdf.py --skip-existing
) else (
    echo [SKIP] convert_to_pdf.py not found.
)

REM --- Step 4: Cleanup ---
echo.
echo ------------------------------------------------------------
echo   STEP 4 / 4 — Cleanup (dry run)
echo ------------------------------------------------------------
echo.
if exist "cleanup.py" (
    python cleanup.py
) else (
    echo [SKIP] cleanup.py not found.
)

echo.
echo ============================================================
echo   PIPELINE COMPLETE
echo ============================================================
echo.
echo   Outputs:
echo     - Slides:  output_slides\
echo     - PDFs:    output_pdfs\
echo     - Cache:   generated_content\
echo.
echo   To delete junk files, run:
echo     python cleanup.py --apply
echo.
pause
endlocal