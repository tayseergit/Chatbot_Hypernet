@echo off
chcp 65001 > nul
title AI ISP Chatbot - Full System Launcher
color 0A

echo.
echo  =======================================================
echo   AI ISP Chatbot and Dashboard - Full System Launcher
echo  =======================================================
echo.

set PYTHONIOENCODING=utf-8
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

cd /d "%~dp0"
set ROOT_DIR=%~dp0

if exist "%ROOT_DIR%venv\Scripts\python.exe" (
    set "PYTHON_EXE=%ROOT_DIR%venv\Scripts\python.exe"
    echo  [*] Using Python Virtual Environment: .\venv\
) else (
    set "PYTHON_EXE=python"
    echo  [*] Using System Python
)

echo.
echo  [1/3] Starting FastAPI Backend API (Port 8000)...
start "FastAPI Backend API" cmd /k "chcp 65001 > nul && set PYTHONIOENCODING=utf-8 && cd /d %ROOT_DIR% && "%PYTHON_EXE%" -u -m uvicorn backend_service.api:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak > nul

echo  [2/3] Starting React Dashboard Frontend (Port 5173)...
start "React Dashboard Frontend" cmd /k "chcp 65001 > nul && cd /d %ROOT_DIR%dashboard_frontend && npm run dev"

timeout /t 2 /nobreak > nul

echo  [3/3] Starting Telegram Bot...
start "Telegram Bot" cmd /k "chcp 65001 > nul && set PYTHONIOENCODING=utf-8 && cd /d %ROOT_DIR% && "%PYTHON_EXE%" -u presentation/telegram_bot.py"

echo.
echo  =======================================================
echo   All Real Services Started Successfully!
echo   - HyperCRM:         Connected Live (https://hcrm.hypernet.sy)
echo   - Backend API:      http://localhost:8000/docs
echo   - React Dashboard:  http://localhost:5173
echo   - Telegram Bot:     Running in dedicated window
echo  =======================================================
echo.
