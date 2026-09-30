@echo off
setlocal
cd /d "%~dp0"
echo Medmate setup - Python 3.12 recommended
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo Python 3.12 was not found. Install 64-bit Python 3.12 from python.org.
  echo Include the Python launcher during installation, then run this file again.
  pause
  exit /b 1
)
py -3.12 -m venv .venv
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo Setup complete. Double-click run_windows.bat to start Medmate.
pause
exit /b 0
:failed
echo.
echo Setup failed. Check your internet connection and the message above.
pause
exit /b 1
