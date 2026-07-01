@echo off
echo ============================================
echo   Starting Travel Planner Backend Server
echo ============================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment found
    call venv\Scripts\activate
) else (
    echo [WARN] No venv found, using system Python
)

echo [INFO] Starting Uvicorn on 0.0.0.0:8000...
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
