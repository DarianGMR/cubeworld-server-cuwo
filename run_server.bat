@echo off
REM Inicia el servidor cuwo (y la interfaz web como script)

cd /d "%~dp0"

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python no está disponible
    pause
    exit /b 1
)

REM Ejecutar servidor cuwo
python -m cuwo.server
pause