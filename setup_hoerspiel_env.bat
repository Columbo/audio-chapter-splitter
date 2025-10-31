@echo off
SET PYTHON_PATH=C:\Users\Christoph\Documents\Hoerspiel\Python-3.13.9\python.exe
SET FFMPEG_PATH="C:\Users\Christoph\Documents\Hoerspiel\ffmpeg-8.0-full_build\bin
SET PROJECT_DIR=%~dp0
SET VENV_DIR=%PROJECT_DIR%venv

"%PYTHON_PATH%" -m venv "%VENV_DIR%"
SET ACTIVATE_FILE=%VENV_DIR%\Scripts\activate.bat
echo set PATH=%FFMPEG_PATH%;%%PATH%% >> "%ACTIVATE_FILE%"
CALL "%ACTIVATE_FILE%"
pip install --upgrade pip
pip install librosa pydub numpy
echo Umgebung ist bereit. Du kannst jetzt dein Skript ausführen.

