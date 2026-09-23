@echo off
title MIU BEE — Dev Mode
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv not found.
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo [ERROR] frontend\package.json not found.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend dependencies...
    pushd frontend
    call npm install
    popd
)

echo ============================================================
echo   MIU BEE — Dev Mode
echo   Backend:  http://localhost:5000
echo   Frontend: http://localhost:5173  (^<-- open this one)
echo ============================================================
echo.

start "MIU BEE · API" cmd /k ""%~dp0.venv\Scripts\python.exe" "%~dp0server.py""

timeout /t 2 /nobreak >nul

start "MIU BEE · Vite" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 4 /nobreak >nul

start "" http://localhost:5173

echo.
echo Two windows opened: API + Vite.
echo Close them to stop.
pause