@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe main.py
if errorlevel 1 (
  echo Medmate could not start. Copy the error above for troubleshooting.
  pause
  exit /b 1
)
