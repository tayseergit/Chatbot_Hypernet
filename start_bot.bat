@echo off
chcp 65001 > nul
title AI ISP Chatbot - Telegram Bot
color 0A

echo.
echo  ==========================================
echo   AI ISP Chatbot - Telegram Bot
echo  ==========================================
echo.

set PYTHONIOENCODING=utf-8
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

cd /d "%~dp0"

echo  [1/2] Starting Mock CRM Server in background...
start "Mock CRM Server" cmd /k "chcp 65001 > nul && set PYTHONIOENCODING=utf-8 && python mock_crm_server.py"

timeout /t 2 /nobreak > nul

echo  [2/2] Starting Telegram Bot...
echo.
echo  NOTE: First launch may take a few minutes to download AI models.
echo  Once you see "Telegram bot is running!" the bot is ready.
echo.

python application/app.py --mode telegram

echo.
echo  Bot stopped. Press any key to exit...
pause > nul
