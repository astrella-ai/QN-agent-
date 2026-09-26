@echo off
REM One-time setup for Windows. Double-click this file.
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.11 or newer is required. Install it from python.org and tick "Add python.exe to PATH".
  pause
  exit /b 1
)
if not exist .venv python -m venv .venv
call .venv\Scripts\python -m pip install --upgrade pip
call .venv\Scripts\python -m pip install -r requirements.txt
where ffmpeg >nul 2>nul
if errorlevel 1 echo NOTE: FFmpeg was not found. Install it with:  winget install Gyan.FFmpeg   (then reopen this window)
if not exist .env call .venv\Scripts\python manage.py init
call .venv\Scripts\python manage.py doctor
echo.
echo Setup finished. Start the app with run.bat. To start it by itself at every sign-in, run autostart.bat.
pause
