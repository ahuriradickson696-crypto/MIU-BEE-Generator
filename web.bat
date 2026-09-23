@echo off
title MIU BEE — Web Interface
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv not found. Set it up first.
    pause
    exit /b 1
)

echo ============================================================
echo   MIU BEE Web Interface
echo ============================================================
echo.

REM --- If React build exists, serve it from Flask ---
if exist "frontend\dist\index.html" (
    echo [INFO] Serving React build from frontend\dist\
    echo [INFO] Opening http://localhost:5000
    start "" http://localhost:5000
    ".venv\Scripts\python.exe" server.py
) else (
    echo [INFO] React build not found.
    echo [INFO] Falling back to Vite dev server mode...
    echo.
    echo   1. Start backend:  python server.py
    echo   2. Start frontend: cd frontend ^&^& npm run dev
    echo   3. Open:           http://localhost:5173
    echo.
    echo   Or run dev.bat to do all that automatically.
    echo.
    pause
)