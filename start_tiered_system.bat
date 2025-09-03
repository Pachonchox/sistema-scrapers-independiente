@echo off
:: 🚀 INICIADOR SISTEMA V5 CON TIERS INTELIGENTE
:: ============================================
::
:: Script batch para iniciar el sistema de tiers V5 de forma sencilla
:: Incluye verificaciones, configuración automática y manejo de errores
::
:: Autor: Sistema V5 Production  
:: Fecha: 03/09/2025

title 🎯 Sistema V5 Tiers Inteligente

:: Configurar codificación UTF-8 para emojis
chcp 65001 >nul

echo.
echo "🎯════════════════════════════════════════════════════════════════🎯"
echo "🚀                SISTEMA V5 CON TIERS INTELIGENTE               🚀"
echo "🎯════════════════════════════════════════════════════════════════🎯"
echo.
echo "🎚️ Tiers: Crítico(2h) | Importante(6h) | Seguimiento(24h)"
echo "🎭 Anti-detección: Proxies + User Agents + Patrones Humanos"
echo "💰 Arbitraje ML: Detección automática de oportunidades"
echo "📱 Telegram: Alertas y notificaciones en tiempo real"
echo "🗄️ Backend: PostgreSQL + Redis para máximo rendimiento"
echo.
echo "🎯════════════════════════════════════════════════════════════════🎯"
echo.

:: Verificar si Python está disponible
echo "🔍 Verificando Python..."
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo "❌ Error: Python no está instalado o no está en PATH"
    echo "   Por favor instale Python 3.8+ desde https://python.org"
    pause
    exit /b 1
)

:: Obtener versión de Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo "✅ Python %PYTHON_VERSION% detectado"

:: Verificar si estamos en el directorio correcto
echo "🔍 Verificando archivos del sistema..."
if not exist "start_tiered_system.py" (
    echo "❌ Error: start_tiered_system.py no encontrado"
    echo "   Asegúrese de ejecutar este batch desde el directorio correcto"
    pause
    exit /b 1
)

if not exist "portable_orchestrator_v5" (
    echo "❌ Error: Directorio portable_orchestrator_v5 no encontrado"
    echo "   Sistema no instalado correctamente"
    pause
    exit /b 1
)

echo "✅ Archivos del sistema verificados"

:: Crear directorio de logs si no existe
if not exist "logs" (
    echo "📁 Creando directorio de logs..."
    mkdir logs
)

:: Mostrar opciones disponibles
echo.
echo "🎮 OPCIONES DISPONIBLES:"
echo.
echo "[1] 🚀 Modo Completo (Recomendado para producción)"
echo "[2] 🧪 Modo Prueba (10 minutos)"
echo "[3] 🛍️ Retailers Específicos"
echo "[4] ⏰ Con Tiempo Límite"
echo "[5] 🔄 Ejecutar Solo Una Vez"
echo "[6] 🛠️ Configuración Personalizada"
echo "[7] ❓ Ver Todas las Opciones"
echo "[0] 🚪 Salir"
echo.

set /p choice="Seleccione una opción (1-7, 0 para salir): "

if "%choice%"=="0" (
    echo "🚪 Saliendo..."
    exit /b 0
)

if "%choice%"=="1" (
    echo "🚀 Iniciando modo completo..."
    set COMMAND=python start_tiered_system.py
    goto :execute
)

if "%choice%"=="2" (
    echo "🧪 Iniciando modo prueba (10 minutos)..."
    set COMMAND=python start_tiered_system.py --test
    goto :execute
)

if "%choice%"=="3" (
    echo.
    echo "🛍️ Retailers disponibles: ripley falabella paris hites abcdin mercadolibre"
    set /p retailers="Ingrese retailers separados por espacios: "
    if "%retailers%"=="" set retailers=ripley falabella
    echo "🛍️ Iniciando con retailers: %retailers%"
    set COMMAND=python start_tiered_system.py --retailers %retailers%
    goto :execute
)

if "%choice%"=="4" (
    echo.
    set /p hours="Ingrese tiempo máximo en horas (ej: 2.5): "
    if "%hours%"=="" set hours=8
    echo "⏰ Iniciando con tiempo límite: %hours% horas"
    set COMMAND=python start_tiered_system.py --max-runtime %hours%
    goto :execute
)

if "%choice%"=="5" (
    echo "🔄 Iniciando ejecución única (no continuo)..."
    set COMMAND=python start_tiered_system.py --single-run
    goto :execute
)

if "%choice%"=="6" (
    echo.
    echo "🛠️ CONFIGURACIÓN PERSONALIZADA:"
    echo.
    set /p retailers="Retailers (vacío=todos): "
    set /p hours="Horas máximas (vacío=ilimitado): "
    set /p extra="Opciones extra (ej: --disable-telegram): "
    
    set COMMAND=python start_tiered_system.py
    if not "%retailers%"=="" set COMMAND=%COMMAND% --retailers %retailers%
    if not "%hours%"=="" set COMMAND=%COMMAND% --max-runtime %hours%
    if not "%extra%"=="" set COMMAND=%COMMAND% %extra%
    
    echo "🛠️ Comando: %COMMAND%"
    goto :execute
)

if "%choice%"=="7" (
    echo.
    echo "📖 TODAS LAS OPCIONES DISPONIBLES:"
    echo.
    python start_tiered_system.py --help
    echo.
    pause
    goto start
)

:: Opción no válida
echo "❌ Opción no válida. Por favor seleccione 1-7 o 0."
pause
goto start

:execute
echo.
echo "🎯════════════════════════════════════════════════════════════════🎯"
echo "🚀 INICIANDO SISTEMA..."
echo "🎯════════════════════════════════════════════════════════════════🎯"
echo.
echo "📋 Comando: %COMMAND%"
echo "⏰ Hora inicio: %DATE% %TIME%"
echo.

:: Ejecutar comando con manejo de errores
%COMMAND%

:: Verificar código de salida
if %ERRORLEVEL% equ 0 (
    echo.
    echo "✅ Sistema completado exitosamente"
) else (
    echo.
    echo "❌ Sistema terminó con errores (código: %ERRORLEVEL%)"
    echo "📁 Revise los logs en la carpeta 'logs' para más detalles"
)

echo.
echo "⏰ Hora finalización: %DATE% %TIME%"
echo "🎯════════════════════════════════════════════════════════════════🎯"

pause
exit /b %ERRORLEVEL%

:start
goto start