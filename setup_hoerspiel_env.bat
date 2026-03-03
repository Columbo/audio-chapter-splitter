@echo off
setlocal

if "%PYTHON_BIN%"=="" set "PYTHON_BIN=python"
if "%FFMPEG_BIN_DIR%"=="" (
    echo FFMPEG_BIN_DIR is not set. Assuming ffmpeg is already available on PATH.
) else (
    set "PATH=%FFMPEG_BIN_DIR%;%PATH%"
)

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
set "VENV_DIR=%PROJECT_DIR%\venv"

where "%PYTHON_BIN%" >nul 2>nul
if errorlevel 1 (
    echo Python executable not found: %PYTHON_BIN%
    exit /b 1
)

"%PYTHON_BIN%" -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo Failed to create the virtual environment.
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate the virtual environment.
    exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    exit /b 1
)

python -m pip install -r "%PROJECT_DIR%\requirements.txt"
if errorlevel 1 (
    echo Failed to install dependencies.
    exit /b 1
)

echo Environment is ready. You can now run the script.
