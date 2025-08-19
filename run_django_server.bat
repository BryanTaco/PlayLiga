@echo off
REM Script para iniciar el servidor Django en modo desarrollo con reinicio automático

REM Usar Python directamente sin entorno virtual en WebContainer
echo Iniciando servidor Django...

REM Ejecutar servidor Django con autoreload
python3 manage.py runserver

REM Mantener ventana abierta
pause
