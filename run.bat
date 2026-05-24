@echo off
REM Stock Tracker - use this to run the app
REM Usage: run.bat [command]
REM Commands: (none)=dashboard, add, remove, list, train, setup, report, schedule, serve, subscribers

set VENV=%~dp0.venv\Scripts\python.exe

if "%1"=="" (
    "%VENV%" "%~dp0main.py" dashboard
) else (
    "%VENV%" "%~dp0main.py" %*
)
