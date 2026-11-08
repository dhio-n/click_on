@echo off
cd /d "%~dp0"
title Anjun Express - Bipador Automatico
set PYTHONPATH=%~dp0src
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m app.main
) else (
    python -m app.main
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocorreu um erro ao executar o programa.
    pause
)
