@echo off
:: 🧪 MODO PRUEBA - SISTEMA V5 TIERS
:: ================================
::
:: Ejecuta el sistema en modo prueba (10 minutos)
:: Ideal para verificar que todo funciona correctamente
::
:: Autor: Sistema V5 Production
:: Fecha: 03/09/2025

title 🧪 Test Mode - Sistema V5 Tiers

:: UTF-8 para emojis
chcp 65001 >nul

echo.
echo "🧪═══════════════════════════════════════════════════════════════🧪"
echo "🧪                    MODO PRUEBA SISTEMA V5                   🧪"
echo "🧪═══════════════════════════════════════════════════════════════🧪"
echo.
echo "⏰ Duración: 10 minutos"
echo "🛍️ Retailers: ripley, falabella (limitados)"
echo "🎚️ Tiers: Todos los tiers ejecutados en secuencia"
echo "📊 Logs: Detallados para debugging"
echo.

:: Verificar Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo "❌ Python no está disponible"
    pause
    exit /b 1
)

:: Crear directorio de logs
if not exist "logs" mkdir logs

echo "🚀 Iniciando modo prueba..."
echo.

:: Ejecutar en modo test con verbose
python start_tiered_system.py --test --verbose

echo.
echo "🧪═══════════════════════════════════════════════════════════════🧪"
echo "✅ Prueba completada"
echo "📁 Revise los logs en la carpeta 'logs' para detalles"
echo "🧪═══════════════════════════════════════════════════════════════🧪"

pause