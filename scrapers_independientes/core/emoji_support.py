# -*- coding: utf-8 -*-
"""
🎨 SOPORTE COMPLETO DE EMOJIS PARA WINDOWS
===========================================
Módulo que fuerza el soporte de UTF-8 y emojis en Windows
para todos los scripts del sistema V5.

Uso: importar al inicio de cualquier script Python
from portable_orchestrator_v5.core.emoji_support import force_emoji_support
"""

import sys
import os
import io
import codecs
import locale


def force_emoji_support():
    """🎯 Fuerza el soporte completo de UTF-8 y emojis en Windows"""
    
    # 1. CONFIGURAR VARIABLES DE ENTORNO (MÉTODO MÁS SEGURO)
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # 2. CONFIGURAR CONSOLA WINDOWS
    if os.name == 'nt':  # Windows
        try:
            import subprocess
            # Cambiar codepage a UTF-8 en Windows
            subprocess.run(['chcp', '65001'], 
                         capture_output=True, 
                         shell=True, 
                         timeout=5)
        except:
            pass
    
    # 3. CONFIGURAR LOCALE DE FORMA SEGURA
    try:
        locale.setlocale(locale.LC_ALL, '')  # Usar locale del sistema
    except:
        pass
    
    return True


def test_emoji_support():
    """🧪 Probar si el soporte de emojis funciona correctamente"""
    
    test_emojis = [
        "🚀", "✅", "❌", "⚠️", "📊", "💾", "🔄", "🎯", 
        "🕷️", "💰", "🧹", "📦", "⏱️", "🐘", "🤖", "🎨"
    ]
    
    print("\n" + "="*50)
    print("🧪 PRUEBA DE SOPORTE DE EMOJIS")
    print("="*50)
    
    success = 0
    for emoji in test_emojis:
        try:
            print(f"{emoji} Emoji funcionando correctamente")
            success += 1
        except Exception as e:
            print(f"❌ Error con emoji: {e}")
    
    if success == len(test_emojis):
        print("✅ TODOS LOS EMOJIS FUNCIONANDO CORRECTAMENTE")
        return True
    else:
        print(f"⚠️ {success}/{len(test_emojis)} emojis funcionando")
        return False


# AUTO-EJECUTAR AL IMPORTAR
force_emoji_support()


if __name__ == "__main__":
    # Ejecutar prueba si se llama directamente
    test_emoji_support()