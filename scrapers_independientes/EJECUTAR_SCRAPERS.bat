@echo off
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║           🚀 SISTEMA SCRAPERS INDEPENDIENTE V5               ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🚀 Iniciando Sistema de Scrapers...
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Verificar si Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Instala Python 3.8 o superior.
    echo 📥 Descarga desde: https://www.python.org/downloads/
    goto :end
)

REM Verificar si existe el archivo principal
if not exist "run_scrapers_system.py" (
    echo ❌ Archivo run_scrapers_system.py no encontrado.
    echo 📁 Asegúrate de estar en el directorio correcto.
    goto :end
)

REM Ejecutar el sistema
echo 🔄 Ejecutando scrapers...
echo.
python run_scrapers_system.py

:end
echo.
echo 📋 Presiona cualquier tecla para cerrar...
pause >nul