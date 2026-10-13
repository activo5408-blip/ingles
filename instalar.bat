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
python -m pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo [2/3] Comprobando FFmpeg...
where ffmpeg >nul 2>nul
if not errorlevel 1 goto ffmpeg_ok
where winget >nul 2>nul
if errorlevel 1 goto ffmpeg_manual
echo FFmpeg no esta disponible. Intentando instalar la version Essentials...
winget install -e --id Gyan.FFmpeg --silent --accept-package-agreements --accept-source-agreements
echo.
where ffmpeg >nul 2>nul
if not errorlevel 1 goto ffmpeg_ok
echo No aparece en PATH todavia. Comprobando paquete Shared como alternativa...
winget install -e --id Gyan.FFmpeg.Shared --silent --accept-package-agreements --accept-source-agreements
echo.
where ffmpeg >nul 2>nul
if not errorlevel 1 goto ffmpeg_ok
echo.
echo WinGet no pudo dejar FFmpeg disponible en esta ventana.
echo Cierra esta ventana, abre una nueva y ejecuta: ffmpeg -version
echo Si sigue sin reconocerse, ejecuta este comando y copia aqui el resultado:
echo   winget install -e --id Gyan.FFmpeg
goto done
:ffmpeg_ok
echo [3/3] FFmpeg esta disponible:
ffmpeg -version
echo.
where ffprobe >nul 2>nul
if errorlevel 1 (
  echo AVISO: no se encuentra ffprobe en PATH.
  echo Comprueba que ffprobe.exe este en la carpeta bin de FFmpeg.
  goto done
)
echo Instalacion completada. Ya puedes ejecutar crear_leccion.bat.
goto done
:ffmpeg_manual
echo.
echo WinGet no esta instalado o no esta en PATH.
echo Puedes descargar FFmpeg desde:
echo https://www.gyan.dev/ffmpeg/builds/
echo Elige "ffmpeg-release-essentials.zip", extraelo y localiza la carpeta bin.
echo Agrega esa carpeta bin al PATH de Windows.
goto done
:error
echo.
echo ERROR instalando las dependencias de Python.
:done
echo.
pause
