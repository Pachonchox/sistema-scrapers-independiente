#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧹 LIMPIADOR AUTOMÁTICO DE PRECIOS
==================================
Script que se ejecuta automáticamente para detectar y limpiar
precios anómalos después de cada ciclo del orquestador V5.

Características:
- ✅ Se ejecuta automáticamente cada hora
- ✅ Detecta precios ridículos y los exporta a Excel
- ✅ Elimina automáticamente precios obviamente erróneos
- ✅ Envía alertas cuando encuentra muchas anomalías
- ✅ Se integra perfectamente con el orquestador V5
"""

import asyncio
import schedule
import time
import os
import sys
from pathlib import Path
from datetime import datetime

# Añadir paths y soporte emojis
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))
from portable_orchestrator_v5.core.emoji_support import force_emoji_support
force_emoji_support()

from price_anomaly_detector import PriceAnomalyDetector


class AutoPriceCleaner:
    """🧹 Limpiador automático de precios"""
    
    def __init__(self):
        self.detector = PriceAnomalyDetector()
        self.running = False
        
        # Configuración
        self.check_interval_minutes = int(os.getenv('PRICE_CHECK_INTERVAL', '60'))  # 1 hora por defecto
        self.alert_threshold = int(os.getenv('ANOMALY_ALERT_THRESHOLD', '50'))     # Alerta si > 50 anomalías
        
        print("🧹 Limpiador Automático de Precios inicializado")
        print(f"⏰ Intervalo de verificación: {self.check_interval_minutes} minutos")
        print(f"🚨 Umbral de alerta: {self.alert_threshold} anomalías")
    
    def cleanup_prices(self):
        """🧹 Ejecutar limpieza de precios"""
        
        print(f"\n{'='*60}")
        print(f"🧹 LIMPIEZA AUTOMÁTICA - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            # Ejecutar detección solo de las últimas 4 horas (datos recientes)
            results = self.detector.run_full_detection(days_back=1)  # Solo último día
            
            if results['status'] == 'success':
                anomalies = results['anomalies_found']
                
                if anomalies == 0:
                    print("✅ No se encontraron precios anómalos - Sistema limpio")
                    
                elif anomalies <= self.alert_threshold:
                    print(f"✅ Limpieza completada: {anomalies} anomalías detectadas y procesadas")
                    
                else:
                    print(f"🚨 ALERTA: {anomalies} anomalías detectadas (umbral: {self.alert_threshold})")
                    print(f"📊 Excel generado: {results['excel_file']}")
                    print(f"🗑️ Eliminados automáticamente: {results['deleted_count']}")
                    
                    # Aquí se podría integrar con sistema de alertas (Telegram, email, etc.)
                    self.send_alert(anomalies, results)
                
                return True
                
            else:
                print("❌ Error en la limpieza automática")
                return False
                
        except Exception as e:
            print(f"❌ Error crítico en limpieza: {e}")
            return False
    
    def send_alert(self, anomalies_count: int, results: dict):
        """📢 Enviar alerta cuando hay muchas anomalías"""
        
        alert_message = f"""
🚨 ALERTA DE PRECIOS ANÓMALOS
=============================
⏰ Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔍 Anomalías detectadas: {anomalies_count}
📊 Excel generado: {results['excel_file'].split('/')[-1] if results['excel_file'] else 'Error'}
🗑️ Eliminados automáticamente: {results['deleted_count']}
🏷️ Marcados para revisión: {results['marked_count']}

Acción requerida: Revisar Excel de anomalías
        """
        
        print(alert_message)
        
        # Guardar alerta en archivo
        alert_dir = Path("data/price_anomalies/alerts")
        alert_dir.mkdir(parents=True, exist_ok=True)
        
        alert_file = alert_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(alert_file, 'w', encoding='utf-8') as f:
                f.write(alert_message)
            print(f"📁 Alerta guardada en: {alert_file}")
        except Exception as e:
            print(f"❌ Error guardando alerta: {e}")
        
        # TODO: Aquí se puede integrar con:
        # - Bot de Telegram
        # - Sistema de email
        # - Webhook de Slack
        # - API de notificaciones
    
    def start_auto_cleaning(self):
        """🚀 Iniciar limpieza automática programada"""
        
        print(f"\n🚀 Iniciando limpieza automática cada {self.check_interval_minutes} minutos")
        print("Presiona Ctrl+C para detener\n")
        
        # Programar la tarea
        schedule.every(self.check_interval_minutes).minutes.do(self.cleanup_prices)
        
        # Ejecutar una limpieza inicial inmediatamente
        print("🧹 Ejecutando limpieza inicial...")
        self.cleanup_prices()
        
        self.running = True
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(30)  # Verificar cada 30 segundos si hay tareas pendientes
                
        except KeyboardInterrupt:
            print("\n\n✋ Limpieza automática detenida por usuario")
            self.running = False
    
    def run_single_cleanup(self):
        """🎯 Ejecutar una sola limpieza (para testing)"""
        
        print("🧹 Ejecutando limpieza única...")
        return self.cleanup_prices()


def main():
    """🎯 Función principal"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description='🧹 Limpiador Automático de Precios Anómalos'
    )
    
    parser.add_argument(
        '--auto', 
        action='store_true',
        help='Ejecutar en modo automático continuo'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Intervalo en minutos entre limpiezas (default: 60)'
    )
    
    parser.add_argument(
        '--single',
        action='store_true', 
        help='Ejecutar una sola limpieza y salir'
    )
    
    args = parser.parse_args()
    
    # Configurar variables de entorno
    if args.interval:
        os.environ['PRICE_CHECK_INTERVAL'] = str(args.interval)
    
    cleaner = AutoPriceCleaner()
    
    if args.single:
        # Ejecutar una sola vez
        success = cleaner.run_single_cleanup()
        exit(0 if success else 1)
        
    elif args.auto:
        # Ejecutar en modo automático continuo
        cleaner.start_auto_cleaning()
        
    else:
        # Mostrar ayuda por defecto
        print("\n🧹 Limpiador Automático de Precios")
        print("====================================")
        print("Opciones:")
        print("  --single    : Ejecutar limpieza una vez")
        print("  --auto      : Ejecutar en modo automático")
        print("  --interval N: Intervalo en minutos (default: 60)")
        print("\nEjemplos:")
        print("  python auto_price_cleaner.py --single")
        print("  python auto_price_cleaner.py --auto --interval 30")


if __name__ == "__main__":
    main()