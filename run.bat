@echo off
echo ========================================
echo   ENSAM Agentic OS - Starting Services
echo ========================================
echo.

echo [1/2] Starting Backend (FastAPI on port 8000)...
cd /d "%~dp0backend"
start "ENSAM-Backend" cmd /k "uv run uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend (Next.js on port 3000)...
cd /d "%~dp0frontend"
start "ENSAM-Frontend" cmd /k "npm start -- -p 3000"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   All services started!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Press any key to open the dashboard...
pause >nul
start http://localhost:3000
