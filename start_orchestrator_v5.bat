@echo off
echo ========================================
echo    ORQUESTADOR V5 ROBUSTO
echo    Sistema Completo de Scraping
echo ========================================
echo.

REM Activar entorno virtual
echo Activando entorno virtual...
call ..\venv\Scripts\activate

REM Configurar variables de entorno
echo Configurando sistema...
set DATA_BACKEND=postgres
set MASTER_SYSTEM_ENABLED=true
set ARBITRAGE_ENABLED=true
set NORMALIZATION_ENABLED=true

REM Configuración de ejecución
set MAX_RUNTIME_MINUTES=60
set CYCLE_PAUSE_SECONDS=30
set BATCH_SIZE=30
set MAX_RETRIES=3
set SCRAPERS_ENABLED=paris,ripley,falabella

echo.
echo Configuracion:
echo - Tiempo maximo: %MAX_RUNTIME_MINUTES% minutos
echo - Pausa entre ciclos: %CYCLE_PAUSE_SECONDS% segundos
echo - Productos por batch: %BATCH_SIZE%
echo - Scrapers: %SCRAPERS_ENABLED%
echo - Backend: %DATA_BACKEND%
echo.

REM Ejecutar orquestador
echo Iniciando Orquestador V5...
echo ========================================
python orchestrator_v5_robust.py

echo.
echo ========================================
echo Orquestador finalizado
echo ========================================
pause