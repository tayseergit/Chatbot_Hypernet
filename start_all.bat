@echo off
chcp 65001 > nul
title AI ISP Chatbot - Full System Launcher
color 0A

echo.
echo  =======================================================
echo   AI ISP Chatbot ^& Dashboard - Full System Launcher
echo  =======================================================
echo.

set PYTHONIOENCODING=utf-8
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

cd /d "%~dp0"

set ROOT_DIR=%~dp0

echo  [1/4] Starting Mock CRM Server (Port 5000)...
start "Mock CRM Server" cmd /k "chcp 65001 > nul && set PYTHONIOENCODING=utf-8 && cd /d %ROOT_DIR% && python -u mock_crm_server.py"

timeout /t 2 /nobreak > nul

echo  [2/4] Starting FastAPI Backend API (Port 8000)...
start "FastAPI Backend API" cmd /k "chcp 65001 > nul && set PYTHONIOENCODING=utf-8 && cd /d %ROOT_DIR% && python -u -m uvicorn backend_service.api:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak > nul

echo  [3/4] Starting React Dashboard Frontend (Port 5173)...
start "React Dashboard Frontend" cmd /k "chcp 65001 > nul && cd /d %ROOT_DIR%dashboard_frontend && npm run dev"

timeout /t 2 /nobreak > nul

echo  [4/4] Starting Telegram Bot...
start "Telegram Bot" cmd /k "chcp 65001 > nul && set PYTHONIOENCODING=utf-8 && cd /d %ROOT_DIR% && python -u application/app.py --mode telegram"

echo.
echo  =======================================================
echo   All Services Started Successfully!
echo   - Backend API:      http://localhost:8000/docs
echo   - React Dashboard:  http://localhost:5173
echo   - Telegram Bot:     Running in dedicated window
echo  =======================================================
echo.
