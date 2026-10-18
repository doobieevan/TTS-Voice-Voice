@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=piper-master\src\python_run\.venv-voice\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Voice environment is missing. Run voice_menu.bat and choose option 2.
  pause
  exit /b 1
)
"%PYTHON_EXE%" sassy_menu.py
if errorlevel 1 pause
endlocal
