# Canal de inglés — Windows

Proyecto para preparar lecciones de inglés y producir vídeos educativos en Windows 10/11.

## Requisitos
- Python 3.10 o posterior (marca **Add Python to PATH** al instalar).
- FFmpeg para Windows; `ffmpeg` y `ffprobe` deben estar en `PATH`.

## Instalar
1. Descarga o clona este repositorio.
2. Instala Python y FFmpeg.
3. Ejecuta `instalar.bat`.
4. Ejecuta `crear_leccion.bat` y escribe la ruta del JSON de la lección, por ejemplo `lecciones\leccion-01.json`.

El generador guarda sus resultados en `salida\` y lee audios opcionales desde `audio\<nombre-leccion>\`. Los originales no se modifican. No subas audios privados ni vídeos renderizados al repositorio.

## Estructura
- `crear_video.py`: generador de diapositivas y vídeo.
- `lecciones\`: contenido de las lecciones en JSON.
- `audio\`: audios por escena (locales).
- `salida\`: resultados generados (locales).

Estado: base del proyecto adaptada a Windows; continuaremos desarrollando la interfaz y validando el flujo de producción.