@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE="
if exist ".venv-voice\Scripts\python.exe" set "PYTHON_EXE=.venv-voice\Scripts\python.exe"
if not defined PYTHON_EXE if exist "piper-master\src\python_run\.venv-voice\Scripts\python.exe" set "PYTHON_EXE=piper-master\src\python_run\.venv-voice\Scripts\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=py -3"
%PYTHON_EXE% voice_menu.py %*
if errorlevel 1 pause
endlocal
