@echo off
setlocal
cd /d "%~dp0"
echo ========================================
echo   Instalador - Canal de ingles Windows
echo ========================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python no esta en PATH.
  echo Instala Python y marca "Add Python to PATH".
  pause
  exit /b 1
)
echo [1/3] Instalando dependencias de Python...
python -m pip install --upgrade pip
if errorlevel 1 goto error
python -m pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo [2/3] Comprobando FFmpeg...
where ffmpeg >nul 2>nul
if not errorlevel 1 goto ffmpeg_ok
where winget >nul 2>nul
if errorlevel 1 goto ffmpeg_manual
echo FFmpeg no esta disponible. Intentando instalarlo con winget...
winget install --id Gyan.FFmpeg.Shared --exact --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto ffmpeg_manual
echo.
echo Se solicito la instalacion de FFmpeg.
echo Cierra esta ventana y vuelve a abrirla para actualizar PATH.
echo Luego ejecuta: ffmpeg -version
goto done
:ffmpeg_ok
echo FFmpeg esta disponible:
ffmpeg -version
echo.
where ffprobe >nul 2>nul
if errorlevel 1 (
  echo AVISO: no se encuentra ffprobe. Debe estar en la misma carpeta bin de FFmpeg.
  goto ffmpeg_manual
)
echo [3/3] Instalacion completada. Ya puedes ejecutar crear_leccion.bat.
goto done
:ffmpeg_manual
echo.
echo No se pudo instalar o detectar FFmpeg automaticamente.
echo Instala FFmpeg para Windows y agrega su carpeta bin al PATH.
echo Despues abre una ventana CMD nueva y comprueba:
echo   ffmpeg -version
echo   ffprobe -version
echo Descarga del proyecto: https://github.com/activo5408-blip/ingles
goto done
:error
echo.
echo ERROR instalando las dependencias de Python.
:done
echo.
pause
