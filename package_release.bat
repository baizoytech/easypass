@echo off
setlocal
cd /d "%~dp0"

echo.
echo   ========================================
echo     EasyPass One-Click Package
echo   ========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\maintenance\publish_release.ps1" %*
if errorlevel 1 (
    echo.
    echo   [ERROR] Packaging failed.
    pause
    exit /b 1
)

echo.
echo   [OK] Packaging finished.
pause
