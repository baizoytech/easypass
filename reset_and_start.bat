@echo off
title EasyPass - Reset
echo.
echo   ========================================
echo     EasyPass - Reset and Start
echo   ========================================
echo.

cd /d "%~dp0"

echo   [1] Deleting old database...
del /f /q "data\passwords.db" 2>nul
del /f /q "data\passwords.db-wal" 2>nul
del /f /q "data\passwords.db-shm" 2>nul
echo       Done.
echo.

echo   [2] Starting app (will auto-seed)...
echo.

call start.bat
