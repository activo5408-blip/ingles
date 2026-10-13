@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
if "%~1"=="" (
  set /p LECCION=Ruta del JSON de la leccion [lecciones\leccion-01.json]: 
  if "!LECCION!"=="" set LECCION=lecciones\leccion-01.json
) else (
  set "LECCION=%~1"
)
python crear_video.py "%LECCION%"
if errorlevel 1 (
  echo.
  echo El generador termino con un error. Revisa los mensajes anteriores.
)
pause
