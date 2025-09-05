# 🚀 Script para ejecutar Sistema V5 con entorno virtual
Write-Host "🚀 Iniciando Sistema V5 con entorno virtual..." -ForegroundColor Green

# Activar entorno virtual
& .\venv\Scripts\Activate.ps1

# Verificar Python
Write-Host "📍 Python actual:" (Get-Command python).Source -ForegroundColor Blue

# Ejecutar el sistema con argumentos pasados
python start_tiered_system.py @args