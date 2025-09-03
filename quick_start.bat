@echo off
:: 🚀 INICIO RÁPIDO - SISTEMA V5 TIERS
:: ==================================
::
:: Lanza directamente el sistema en modo completo
:: Para configuraciones avanzadas use start_tiered_system.bat
::
:: Autor: Sistema V5 Production
:: Fecha: 03/09/2025

title 🚀 Quick Start - Sistema V5 Tiers

:: UTF-8 para emojis
chcp 65001 >nul

echo "🚀 Iniciando Sistema V5 con Tiers Inteligente..."
echo.

:: Verificar Python rápidamente
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo "❌ Python no disponible"
    pause
    exit /b 1
)

:: Crear logs si no existe
if not exist "logs" mkdir logs

:: Ejecutar directamente
python start_tiered_system.py

pause