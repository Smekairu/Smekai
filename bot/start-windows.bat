@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >/dev/null 2>/dev/null || (echo Python не найден. Поставьте с python.org, при установке отметьте "Add python.exe to PATH". & pause & exit /b 1)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
python run_local.py
pause
