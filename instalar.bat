@echo off
setlocal
cd /d "%~dp0"
echo ========================================
echo   Instalador - Canal de ingles Windows
echo ========================================
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python no esta en PATH. Instala Python 3.10+ y marca Add Python to PATH.
  pause
  exit /b 1
)
python -m pip install --upgrade pip
if errorlevel 1 goto error
python -m pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo Dependencias instaladas. Comprueba FFmpeg con: ffmpeg -version
pause
exit /b 0
:error
echo Hubo un error instalando dependencias.
pause
exit /b 1
