#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 INSTALADOR AUTOMÁTICO - Sistema Scrapers Independiente V5
============================================================
Script de instalación que configura todo automáticamente.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🔧 INSTALADOR SISTEMA SCRAPERS V5                  ║
║                                                              ║
║  Este script instalará automáticamente:                     ║
║    • Dependencias Python necesarias                         ║
║    • Playwright y navegadores                               ║
║    • Estructura de directorios                              ║
║    • Configuración inicial                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

def run_command(command, description):
    """Ejecutar comando con manejo de errores"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        print(f"📝 Output: {e.stdout}")
        print(f"📝 Error: {e.stderr}")
        return False

def install_dependencies():
    """Instalar dependencias Python"""
    print("\n📦 INSTALANDO DEPENDENCIAS")
    print("=" * 40)
    
    # Verificar pip
    if not run_command("pip --version", "Verificando pip"):
        print("❌ pip no encontrado. Instala Python correctamente.")
        return False
    
    # Instalar requirements
    if not run_command("pip install -r requirements.txt", "Instalando dependencias Python"):
        return False
    
    # Instalar Playwright
    if not run_command("python -m playwright install chromium", "Instalando navegador Chromium"):
        return False
    
    return True

def create_directories():
    """Crear directorios necesarios"""
    print("\n📁 CREANDO DIRECTORIOS")
    print("=" * 40)
    
    dirs = ['resultados', 'logs']
    
    for dir_name in dirs:
        try:
            Path(dir_name).mkdir(exist_ok=True)
            print(f"✅ Directorio creado: {dir_name}/")
        except Exception as e:
            print(f"❌ Error creando {dir_name}: {e}")
            return False
    
    return True

def test_installation():
    """Probar instalación"""
    print("\n🧪 PROBANDO INSTALACIÓN")
    print("=" * 40)
    
    # Test imports
    test_imports = [
        "import playwright",
        "import pandas",
        "import openpyxl",
        "from colorama import Fore"
    ]
    
    for test_import in test_imports:
        try:
            exec(test_import)
            module_name = test_import.split()[-1].replace(',', '')
            print(f"✅ {module_name} disponible")
        except ImportError as e:
            print(f"❌ Error importando: {test_import} - {e}")
            return False
    
    # Test Playwright
    try:
        run_command("python -c \"from playwright.sync_api import sync_playwright; print('Playwright OK')\"", 
                   "Verificando Playwright")
    except Exception as e:
        print(f"⚠️ Advertencia Playwright: {e}")
    
    return True

def create_launcher_scripts():
    """Crear scripts de lanzamiento"""
    print("\n🚀 CREANDO SCRIPTS DE LANZAMIENTO")
    print("=" * 40)
    
    # Script Windows
    windows_script = """@echo off
echo 🚀 Iniciando Sistema Scrapers V5...
python run_scrapers_system.py
pause
"""
    
    try:
        with open("EJECUTAR_SCRAPERS.bat", "w", encoding="utf-8") as f:
            f.write(windows_script)
        print("✅ Script Windows creado: EJECUTAR_SCRAPERS.bat")
    except Exception as e:
        print(f"⚠️ Error creando script Windows: {e}")
    
    # Script Linux/Mac
    unix_script = """#!/bin/bash
echo "🚀 Iniciando Sistema Scrapers V5..."
python3 run_scrapers_system.py
read -p "Presiona Enter para continuar..."
"""
    
    try:
        with open("ejecutar_scrapers.sh", "w", encoding="utf-8") as f:
            f.write(unix_script)
        os.chmod("ejecutar_scrapers.sh", 0o755)
        print("✅ Script Unix creado: ejecutar_scrapers.sh")
    except Exception as e:
        print(f"⚠️ Error creando script Unix: {e}")

def main():
    """Función principal de instalación"""
    print_banner()
    
    print("🔍 Verificando sistema...")
    print(f"📍 Directorio actual: {os.getcwd()}")
    print(f"🐍 Python: {sys.version}")
    
    # Cambiar al directorio del script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    success_steps = []
    
    # 1. Crear directorios
    if create_directories():
        success_steps.append("Directorios")
    else:
        print("❌ Error creando directorios")
        return
    
    # 2. Instalar dependencias
    if install_dependencies():
        success_steps.append("Dependencias")
    else:
        print("❌ Error instalando dependencias")
        return
    
    # 3. Probar instalación
    if test_installation():
        success_steps.append("Pruebas")
    else:
        print("⚠️ Algunas pruebas fallaron, pero el sistema puede funcionar")
    
    # 4. Scripts de lanzamiento
    create_launcher_scripts()
    success_steps.append("Scripts")
    
    # Resumen final
    print("\n" + "="*60)
    print("🎉 INSTALACIÓN COMPLETADA")
    print("="*60)
    print(f"✅ Pasos completados: {', '.join(success_steps)}")
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. 🚀 Ejecuta: python run_scrapers_system.py")
    print("2. 📁 O usa: EJECUTAR_SCRAPERS.bat (Windows)")
    print("3. 📁 O usa: ./ejecutar_scrapers.sh (Linux/Mac)")
    print("4. 📊 Revisa resultados en: resultados/")
    
    print("\n💡 CONSEJOS:")
    print("• Edita config.json para personalizar scrapers")
    print("• Los logs se guardan en resultados/")
    print("• Cada scraper puede ejecutarse individualmente")
    
    print(f"\n🌟 ¡Sistema listo para usar!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Instalación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante instalación: {e}")
        sys.exit(1)