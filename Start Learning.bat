@echo off
rem LearnPack launcher for Windows. Double-click to start.
rem Starts the app and opens your browser. Keep this window open while you study.
cd /d "%~dp0"

where python >nul 2>nul || (echo Python 3.10 or newer is needed. Install it from https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^) and run this again. & pause & exit /b 1)

rem First run: create .venv with the packages the course exercises use.
if not exist .venv (
  echo First run: setting up exercise packages ^(one minute^)...
  where uv >nul 2>nul && (uv venv -q && uv pip install -q -r requirements.txt) || (python -m venv .venv && .venv\Scripts\pip install -q -r requirements.txt)
)

python server.py
pause
