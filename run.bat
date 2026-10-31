@echo off
setlocal
cd /d "%~dp0"

:: 1. Check for .venv
if exist "%~dp0.venv\Scripts\python.exe" goto :found_dot_venv

:: 2. Check for venv
if exist "%~dp0venv\Scripts\python.exe" goto :found_venv

:: 3. Check for env
if exist "%~dp0env\Scripts\python.exe" goto :found_env

:: 4. Fallback to system Python
goto :fallback_system

:found_dot_venv
echo [CRC] Found virtual environment in .venv
if exist "%~dp0.venv\Scripts\activate.bat" call "%~dp0.venv\Scripts\activate.bat"
set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
goto :launch

:found_venv
echo [CRC] Found virtual environment in venv
if exist "%~dp0venv\Scripts\activate.bat" call "%~dp0venv\Scripts\activate.bat"
set "PYTHON_CMD=%~dp0venv\Scripts\python.exe"
goto :launch

:found_env
echo [CRC] Found virtual environment in env
if exist "%~dp0env\Scripts\activate.bat" call "%~dp0env\Scripts\activate.bat"
set "PYTHON_CMD=%~dp0env\Scripts\python.exe"
goto :launch

:fallback_system
echo [CRC] No virtual environment found. Searching for system Python...
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :launch
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    goto :launch
)

echo [CRC Error] Python is not installed or not found in PATH.
echo Please install Python 3 or set up a virtual environment (.venv).
pause
exit /b 1

:launch
echo [CRC] Starting application using: %PYTHON_CMD%
"%PYTHON_CMD%" app.py %*

if errorlevel 1 (
    echo.
    echo [CRC] Application stopped with error code %errorlevel%.
    pause
)
