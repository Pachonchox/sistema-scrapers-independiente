# -*- coding: utf-8 -*-
"""
🔍 Debug Extraction Flow - Seguir paso a paso la extracción
===========================================================
"""

import asyncio
import logging
from playwright.async_api import async_playwright
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_extraction_step_by_step():
    """🔍 Debug paso a paso del proceso de extracción"""
    
    async with async_playwright() as playwright:
        # Configurar navegador
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        url = "https://www.paris.cl/tecnologia/celulares/"
        logger.info(f"🌐 Navegando a: {url}")
        
        try:
            # Paso 1: Navegar
            await page.goto(url, timeout=45000)
            logger.info("✅ Página cargada")
            
            # Paso 2: Esperar (como PORT)
            logger.info("⏰ Esperando 10 segundos...")
            await page.wait_for_timeout(10000)
            
            # Paso 3: Scroll (como PORT)
            logger.info("📜 Scroll completo...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(5000)
            
            logger.info("📜 Scroll a mitad...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
            await page.wait_for_timeout(3000)
            
            # Paso 4: EXTRAER EXACTAMENTE COMO NUESTRO CÓDIGO V5
            logger.info("🔍 EXTRACCIÓN COMO V5:")
            containers = await page.query_selector_all("div[data-cnstrc-item-id]")
            logger.info(f"📦 Contenedores encontrados: {len(containers)}")
            
            products_extracted = 0
            
            for i, container in enumerate(containers[:3]):  # Solo primeros 3 para debug
                try:
                    logger.info(f"\n--- PRODUCTO {i+1} ---")
                    
                    # Data attributes (como nuestro código)
                    product_code = await container.get_attribute('data-cnstrc-item-id') or ''
                    product_name = await container.get_attribute('data-cnstrc-item-name') or ''
                    price_from_data = await container.get_attribute('data-cnstrc-item-price') or ''
                    
                    logger.info(f"📋 Código: '{product_code}'")
                    logger.info(f"📋 Nombre: '{product_name}'")
                    logger.info(f"📋 Precio data: '{price_from_data}'")
                    
                    # AQUÍ ESTÁ EL PROBLEMA: Nuestra validación
                    if not product_code or not product_name:
                        logger.warning("❌ RECHAZADO: Falta código o nombre")
                        continue
                    
                    # Precio (exactamente como nuestro código)
                    current_price_text = ""
                    current_price_numeric = None
                    
                    # Buscar precio con nuestros selectores
                    price_selectors = [
                        'span[class*="ui-font-semibold"]',
                        'span:has-text("$")',
                        'span[class*="ui-text-"]'
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elements = await container.query_selector_all(selector)
                            logger.info(f"💰 Selector '{selector}': {len(price_elements)} elementos")
                            
                            for j, elem in enumerate(price_elements):
                                text = (await elem.text_content() or '').strip()
                                logger.info(f"   [{j}]: '{text}'")
                                
                                if '$' in text and len(text) < 20:
                                    logger.info(f"   ✅ Precio candidato: '{text}'")
                                    current_price_text = text
                                    
                                    # Parsing (como nuestro código)
                                    import re
                                    price_match = re.search(r'\$?([\d.,]+)', current_price_text.replace('.', ''))
                                    if price_match:
                                        try:
                                            current_price_numeric = int(price_match.group(1).replace(',', ''))
                                            logger.info(f"   ✅ Precio parseado: {current_price_numeric}")
                                            if current_price_numeric > 1000:
                                                logger.info(f"   ✅ Precio válido (>{1000})")
                                                break
                                        except Exception as e:
                                            logger.info(f"   ❌ Error parsing: {e}")
                            
                            if current_price_numeric and current_price_numeric > 1000:
                                logger.info(f"✅ PRECIO ENCONTRADO: {current_price_numeric}")
                                break
                        except Exception as e:
                            logger.info(f"   ❌ Error con selector '{selector}': {e}")
                    
                    # Marca (como nuestro código)
                    brand = ""
                    try:
                        brand_elements = await container.query_selector_all('span[class*="ui-font-semibold"]')
                        if len(brand_elements) >= 2:
                            brand_elem = brand_elements[1]
                            brand_text = (await brand_elem.text_content() or '').strip()
                            if brand_text and len(brand_text) < 20 and '$' not in brand_text:
                                brand = brand_text
                                logger.info(f"✅ MARCA: '{brand}'")
                    except:
                        pass
                    
                    # VERIFICAR SI PASARÍA NUESTRAS VALIDACIONES
                    if product_code and product_name:
                        if current_price_numeric and current_price_numeric > 1000:
                            products_extracted += 1
                            logger.info(f"✅ PRODUCTO {products_extracted} EXTRAÍDO EXITOSAMENTE")
                            logger.info(f"   Código: {product_code}")
                            logger.info(f"   Nombre: {product_name[:50]}...")
                            logger.info(f"   Marca: {brand}")
                            logger.info(f"   Precio: ${current_price_numeric:,}")
                        else:
                            logger.warning(f"❌ RECHAZADO: Sin precio válido (precio: {current_price_numeric})")
                    else:
                        logger.warning(f"❌ RECHAZADO: Falta código ({bool(product_code)}) o nombre ({bool(product_name)})")
                    
                except Exception as e:
                    logger.error(f"❌ Error procesando producto {i+1}: {e}")
            
            logger.info(f"\n🎯 RESUMEN FINAL:")
            logger.info(f"   Contenedores encontrados: {len(containers)}")
            logger.info(f"   Productos extraídos exitosamente: {products_extracted}")
            
            if products_extracted == 0:
                logger.warning("⚠️ NINGÚN PRODUCTO EXTRAÍDO - Revisando validaciones...")
            
        except Exception as e:
            logger.error(f"❌ Error general: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_extraction_step_by_step())