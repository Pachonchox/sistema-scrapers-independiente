@echo off
echo 🚀 Iniciando Sistema V5 con entorno virtual...

:: Activar entorno virtual
call venv\Scripts\activate.bat

:: Verificar que estamos en el venv correcto
echo 📍 Python actual: %VIRTUAL_ENV%

:: Ejecutar el sistema
python start_tiered_system.py %*

:: Mantener ventana abierta si hay error
if errorlevel 1 pause