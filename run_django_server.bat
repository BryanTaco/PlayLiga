@echo off
REM Script para iniciar el servidor Django en modo desarrollo con reinicio automático

REM Activar entorno virtual si existe (ajustar ruta si es necesario)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Ejecutar servidor Django con autoreload
python manage.py runserver

REM Mantener ventana abierta
pause
