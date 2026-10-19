@echo off
title OpenMontage Studio Launcher
echo ========================================================
echo               OPENMONTAGE STUDIO LAUNCHER               
echo ========================================================
echo.
echo Activating Python virtual environment...
cd /d "%~dp0"

start "OpenMontage Remotion Studio" cmd /k "cd remotion-composer && npx remotion studio"
timeout /t 3 /nobreak >nul

start "OpenMontage Backlot" cmd /k ".\.venv\Scripts\python.exe -m backlot serve --port 4750"
timeout /t 2 /nobreak >nul

start http://127.0.0.1:4750

echo.
echo [OK] Backlot Living Storyboard: http://127.0.0.1:4750
echo [OK] Remotion Studio:           http://localhost:3000
echo.
pause
