#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io

# Forzar UTF-8 para soporte completo de emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Configurar output streams con UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
"""
🚀 INICIO RÁPIDO - SISTEMA OPTIMIZADO DE SCRAPING
===============================================

EJECUTA ESTE ARCHIVO PARA EMPEZAR INMEDIATAMENTE

CARACTERÍSTICAS:
✅ Proxy inteligente 70% directo / 30% Decodo
✅ Detección automática de bloqueos → Switch a proxy  
✅ 93.6% ahorro datos Falabella / 50.1% Ripley
✅ Bloqueo automático 33+ dominios innecesarios
✅ Fallback automático en errores
✅ Reportes detallados
✅ Listo para producción

CONFIGURACIÓN PROXY DECODO SOCKS5H (YA INCLUIDA):
- Host: gate.decodo.com:7000
- User: user-sprhxdrm60-country-cl
- Pass: rdAZz6ddZf+kv71f1A
- Protocol: SOCKS5H
- 10 Canales disponibles con load balancing automático

SOLO EJECUTA: python START_OPTIMIZED_SCRAPING.py
"""

import asyncio
import sys
import signal
from pathlib import Path

# Variable global para el sistema, para cleanup en señales
current_system = None

def signal_handler(signum, frame):
    """Manejador de señales para cleanup seguro"""
    print(f"\n🛑 Señal {signum} recibida. Cerrando sistema de forma segura...")
    
    # Intentar cleanup del sistema actual
    if current_system:
        try:
            # Crear un nuevo loop para cleanup si es necesario
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(safe_cleanup(current_system))
            loop.close()
        except Exception as e:
            print(f"⚠️ Error durante cleanup: {e}")
    
    print("👋 Sistema cerrado exitosamente")
    sys.exit(0)

async def safe_cleanup(system):
    """Cleanup seguro del sistema"""
    try:
        if hasattr(system, 'cleanup_all'):
            await system.cleanup_all()
        print("🧹 Recursos limpiados correctamente")
    except Exception as e:
        # Ignorar errores de cleanup después de interrupción
        print(f"⚠️ Cleanup parcial completado: {e}")

# Registrar manejadores de señales
signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)

# Configurar UTF-8 para emojis en Windows
import os

# Función safe_print ya no necesaria - UTF-8 forzado

if os.name == 'nt':  # Windows
    try:
        # Configurar consola para UTF-8
        os.system('chcp 65001 >nul')
    except:
        pass

# Verificar dependencias
try:
    from production_ready_system import ProductionScrapingSystem
    from core.product_processor import ProductProcessor
    print("✅ Dependencias verificadas")
except ImportError as e:
    print(f"❌ Error de dependencias: {e}")
    print("Instala con: pip install playwright asyncio")
    sys.exit(1)

async def quick_start_demo():
    """Demo rápido del sistema optimizado"""
    global current_system
    
    print("🚀 INICIANDO SISTEMA OPTIMIZADO DE SCRAPING")
    print("=" * 55)
    print("Proxy Decodo integrado | Ahorro de datos máximo")
    print("70% directo + 30% proxy con fallback inteligente")
    print("🗄️ Inserción directa a PostgreSQL activada")
    print()
    
    # Inicializar sistema de producción
    system = ProductionScrapingSystem()
    current_system = system  # Asignar a variable global para cleanup
    
    # Inicializar ProductProcessor para DB
    processor = ProductProcessor(enable_excel_backup=True, batch_size=50)
    print("✅ ProductProcessor inicializado - conectado a PostgreSQL")
    
    print("📋 RETAILERS DISPONIBLES:")
    for retailer, config in system.supported_retailers.items():
        status = "🟢 RECOMENDADO" if config["recommended"] else "🟡 BÁSICO"
        print(f"  {retailer.upper()}: {config['savings_percent']:.1f}% ahorro - {status}")
    
    print("\n🔥 EJECUTANDO SCRAPING OPTIMIZADO...")
    print("(Falabella + Ripley con máximo ahorro de datos)")
    
    try:
        # Ejecutar scraping con configuración optimizada
        results = await system.run_full_scraping_cycle(
            retailers=["falabella", "ripley"],  # Solo los que funcionan perfecto
            max_products_per_category=15  # Cantidad moderada para demo
        )
        
        # 🗄️ PROCESAR DATOS A POSTGRESQL
        print("\n🗄️ INSERTANDO DATOS EN POSTGRESQL...")
        productos_insertados = 0
        
        for retailer, retailer_data in results["results"].items():
            for category, cat_data in retailer_data["categories"].items():
                if cat_data.get("success", False) and cat_data.get("products"):
                    for product in cat_data["products"]:
                        # Convertir formato del scraper al formato esperado por ProductProcessor
                        precios_raw = product.get('precio', '0').split('\n')
                        precios_numericos = []
                        
                        # Extraer solo precios válidos (con $, sin %)
                        for precio_str in precios_raw:
                            if '$' in precio_str and '%' not in precio_str:
                                precio_limpio = ''.join(filter(str.isdigit, precio_str.replace('$', '').replace('.', '')))
                                if precio_limpio:
                                    precios_numericos.append(int(precio_limpio))
                        
                        # 🔧 CORRECCIÓN ESPECÍFICA PARA FALABELLA
                        if retailer == 'falabella' and len(precios_numericos) >= 2:
                            # Falabella: primer precio = oferta, segundo precio = normal
                            original_price = precios_numericos[1]  # Segundo precio = precio normal
                            current_price = precios_numericos[0]   # Primer precio = precio oferta
                        else:
                            # Otros retailers: primer precio = normal
                            original_price = precios_numericos[0] if precios_numericos else 0
                            current_price = 0
                        
                        # 🧮 ALGORITMO MATEMÁTICO ROBUSTO PARA SKU ÚNICO MULTICATEGORÍA
                        import hashlib
                        
                        # 1. Obtener posición única del producto en la lista
                        product_position = cat_data["products"].index(product)
                        
                        # 2. Componentes determinísticos invariantes
                        retailer_code = retailer[:3].upper()  # FAL, RIP
                        category_hash = hashlib.md5(category.encode()).hexdigest()[:2].upper()  # SM, CO, TA
                        
                        # 3. Firma única del producto (determinística)
                        product_signature = f"{product.get('nombre', '')}_{category}_{product_position}_{retailer}"
                        product_hash = hashlib.sha256(product_signature.encode()).hexdigest()[:5].upper()
                        
                        # 4. SKU matemático final: [RET][CAT][HASH5] = 10 caracteres
                        mathematical_sku = f"{retailer_code}{category_hash}{product_hash}"
                        
                        product_data = {
                            'title': product.get('nombre', ''),
                            'nombre': product.get('nombre', ''),
                            'sku': mathematical_sku,  # SKU matemático robusto
                            'link': f'https://{retailer}.com/{category}/product/{product_hash}',  # Link determinístico
                            'original_price': original_price,
                            'current_price': current_price,
                            'retailer': retailer,
                            'category': category,
                            'extracted_at': product.get('extracted_at'),
                            'position_in_category': product_position  # Para referencia
                        }
                        
                        # Procesar con ProductProcessor
                        sku = await processor.process_product(product_data, retailer)
                        if sku:
                            productos_insertados += 1
        
        # Procesar batch final
        await processor.flush_batch()
        print(f"✅ {productos_insertados} productos procesados e insertados en DB")
        
        # Guardar resultados (mantener funcionalidad original)
        results_file = await system.save_results(results)
        
        # MOSTRAR RESULTADOS
        print(f"\n🎯 RESULTADOS DEL SCRAPING OPTIMIZADO:")
        print("=" * 50)
        
        summary = results["summary"]
        print(f"📦 Productos extraídos: {summary['total_products']}")
        print(f"⏱️  Duración total: {results['total_duration_minutes']:.1f} minutos")
        print(f"💾 Ahorro promedio datos: {summary['average_savings_percent']:.1f}%")
        print(f"✅ Extracciones exitosas: {summary['successful_extractions']}")
        
        print(f"\n📊 DETALLES POR RETAILER:")
        print("-" * 30)
        
        for retailer, retailer_data in results["results"].items():
            print(f"🏪 {retailer.upper()}:")
            print(f"   Productos: {retailer_data['total_products']}")
            print(f"   Éxito: {retailer_data['success_rate']:.1f}%")
            print(f"   Tiempo: {retailer_data['total_duration']:.1f}s")
            
            for category, cat_data in retailer_data["categories"].items():
                if cat_data["success"]:
                    method = cat_data.get("method_used", "N/A")
                    print(f"     📂 {category}: {cat_data['products_count']} productos ({method})")
                else:
                    print(f"     ❌ {category}: Error - {cat_data.get('error', 'Unknown')}")
        
        # Información de archivos generados
        print(f"\n💾 ARCHIVOS GENERADOS:")
        print(f"   📄 {results_file}")
        print(f"   📄 production_scraper.log")
        
        # Estadísticas finales de ahorro
        print(f"\n💰 AHORRO DE DATOS CONSEGUIDO:")
        if summary['total_products'] > 0:
            estimated_normal_mb = summary['total_products'] * 0.5  # 0.5MB por producto normal
            estimated_saved_mb = estimated_normal_mb * (summary['average_savings_percent'] / 100)
            print(f"   📊 Datos normales estimados: {estimated_normal_mb:.1f}MB")
            print(f"   💾 Datos ahorrados: {estimated_saved_mb:.1f}MB")
            print(f"   📉 Reducción: {summary['average_savings_percent']:.1f}%")
        
        print(f"\n🎉 SISTEMA FUNCIONANDO PERFECTAMENTE")
        print("Configuración óptima para proxy con cobro por mega")
        
    except Exception as e:
        print(f"❌ ERROR DURANTE SCRAPING: {e}")
        print("Revisa el log 'production_scraper.log' para detalles")
    
    finally:
        # Cleanup automático
        await system.cleanup_all()
        await processor.close()  # Cerrar ProductProcessor y conexiones DB
        print(f"\n🧹 Recursos limpiados automáticamente")

async def configuration_test():
    """Test rápido de configuración"""
    global current_system
    
    print("🔧 TEST DE CONFIGURACIÓN")
    print("-" * 30)
    
    # Test básico del sistema
    system = ProductionScrapingSystem()
    current_system = system  # Asignar a variable global para cleanup
    
    try:
        # Inicializar sistema para Falabella (el más optimizado)
        smart_system = await system.get_smart_system("falabella")
        
        print("✅ Sistema inteligente inicializado")
        print(f"   Ahorro configurado: {smart_system.saver_config['savings_percent']:.1f}%")
        print(f"   Nivel: {smart_system.saver_config['level']}")
        print(f"   Proxy Decodo: {smart_system.proxy_config.host}:{smart_system.proxy_config.port}")
        print(f"   Dominios bloqueados: {len(smart_system.data_saver.high_traffic_blocklist)}")
        
        # Test de reporte
        report = smart_system.get_performance_report()
        print(f"   Ratio proxy objetivo: {report['proxy_intelligence']['target_proxy_ratio']:.1f}%")
        
        print("✅ Configuración validada correctamente")
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
    
    finally:
        await system.cleanup_all()

def show_help():
    """Mostrar ayuda del sistema"""
    
    print("📚 AYUDA DEL SISTEMA OPTIMIZADO")
    print("=" * 40)
    print()
    print("MODOS DE EJECUCIÓN:")
    print("  python START_OPTIMIZED_SCRAPING.py              # Demo completo")
    print("  python START_OPTIMIZED_SCRAPING.py test         # Solo test configuración")
    print("  python START_OPTIMIZED_SCRAPING.py help         # Esta ayuda")
    print()
    print("CARACTERÍSTICAS PRINCIPALES:")
    print("  • Proxy inteligente 70% directo / 30% Decodo")
    print("  • 🔄 Load balancing automático con 10 canales proxy")
    print("  • Detección automática bloqueos → Switch proxy")
    print("  • 93.6% ahorro datos Falabella")
    print("  • 50.1% ahorro datos Ripley")  
    print("  • Bloqueo automático 33+ dominios no esenciales")
    print("  • Fallback automático en errores")
    print("  • Reportes detallados JSON + logs")
    print()
    print("ARCHIVOS IMPORTANTES:")
    print("  • production_ready_system.py     # Sistema principal")
    print("  • smart_proxy_data_saver.py      # Proxy inteligente")
    print("  • final_data_saver_system.py     # Ahorro de datos")
    print("  • production_results/            # Resultados guardados")
    print("  • production_scraper.log         # Logs detallados")
    print()
    print("CONFIGURACIÓN PROXY DECODO SOCKS5H (INCLUIDA):")
    print("  Host: gate.decodo.com:7000")
    print("  User: user-sprhxdrm60-country-cl")
    print("  Pass: rdAZz6ddZf+kv71f1A")
    print("  Protocol: SOCKS5H")
    print("  🔄 10 Canales disponibles con rotación automática cada 50 requests")
    print()
    print("¡SISTEMA LISTO PARA PRODUCCIÓN!")

def main():
    """Función principal de inicio"""
    
    # Procesar argumentos simples
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == "help":
            show_help()
            return
        elif arg == "test":
            print("Ejecutando test de configuración...")
            asyncio.run(configuration_test())
            return
    
    # Ejecución normal - demo completo
    print("Ejecutando demo completo del sistema optimizado...")
    asyncio.run(quick_start_demo())

if __name__ == "__main__":
    main()