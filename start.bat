@echo off
title EasyPass
echo.
echo   ========================================
echo     EasyPass - Password Manager
echo   ========================================
echo.

cd /d "%~dp0"

REM --- Find Python ---
set "PYTHON="

REM 1. System PATH
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON=python"
    goto :found
)

REM 2. Common install paths
if exist "C:\Python313\python.exe" ( set "PYTHON=C:\Python313\python.exe" & goto :found )
if exist "C:\Python312\python.exe" ( set "PYTHON=C:\Python312\python.exe" & goto :found )
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" ( set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python313\python.exe" & goto :found )
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" ( set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe" & goto :found )

echo   [ERROR] Python not found!
echo.
echo   Please install Python 3.9+ from:
echo   https://www.python.org/downloads/
echo   (Check "Add Python to PATH" during install)
echo.
pause
exit /b 1

:found
echo   [OK] Python: %PYTHON%

REM --- Install dependencies locally to 'libs' folder ---
if not exist "libs\flask" (
    echo   [1/2] Installing dependencies locally...
    "%PYTHON%" -m pip install -r requirements.txt -t libs
    if %errorlevel% neq 0 (
        echo   [1/2] Retry with mirror...
        "%PYTHON%" -m pip install -r requirements.txt -t libs -i https://pypi.tuna.tsinghua.edu.cn/simple
    )
) else (
    echo   [CHECK] Ensuring dependencies...
    "%PYTHON%" -m pip install -r requirements.txt -t libs -q 2>nul
)

set "PYTHONPATH=%~dp0libs;%PYTHONPATH%"

echo.
echo   [START] http://localhost:5000
echo   [STOP]  Ctrl+C
echo.
"%PYTHON%" -m src.app
if %errorlevel% neq 0 (
    echo.
    echo   [ERROR] App failed to start. Check errors above.
)
pause
