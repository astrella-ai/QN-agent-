@echo off
cd /d "%~dp0"
call .venv\Scripts\python manage.py install-autostart
pause
