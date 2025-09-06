# -*- coding: utf-8 -*-
"""
🔍 Debug Script - Comparar selectores Paris V5 vs PORT funcional
================================================================

Este script va a navegar a la misma URL que PORT y extraer información
del DOM para comparar qué elementos encuentra cada método.
"""

import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_paris_dom():
    """🔍 Debug del DOM de Paris para comparar con PORT"""
    
    async with async_playwright() as playwright:
        # Configurar navegador como V5
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        url = "https://www.paris.cl/tecnologia/celulares/"
        logger.info(f"🌐 Navegando a: {url}")
        
        try:
            # Navegar con timing del PORT
            await page.goto(url, timeout=45000)
            
            # Esperar carga inicial (como PORT funcional)
            logger.info("⏰ Esperando 10 segundos (como PORT)...")
            await page.wait_for_timeout(10000)
            
            # Scroll exacto del PORT
            logger.info("📜 Scroll completo...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(5000)
            
            logger.info("📜 Scroll a mitad...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
            await page.wait_for_timeout(3000)
            
            # DIAGNÓSTICO: ¿Qué elementos encuentra?
            logger.info("🔍 DIAGNÓSTICO DE SELECTORES:")
            
            # 1. Selector principal del PORT
            containers_port = await page.query_selector_all("div[data-cnstrc-item-id]")
            logger.info(f"📦 Contenedores PORT (data-cnstrc-item-id): {len(containers_port)}")
            
            if containers_port:
                # Analizar primer contenedor
                first_container = containers_port[0]
                
                # Data attributes
                product_id = await first_container.get_attribute('data-cnstrc-item-id')
                product_name = await first_container.get_attribute('data-cnstrc-item-name')
                product_price = await first_container.get_attribute('data-cnstrc-item-price')
                
                logger.info(f"✅ PRIMER PRODUCTO ENCONTRADO:")
                logger.info(f"   ID: {product_id}")
                logger.info(f"   Nombre: {product_name}")
                logger.info(f"   Precio: {product_price}")
                
                # Probar selectores de precio
                price_selectors = [
                    'span[class*="ui-text-"]',
                    'span[class*="ui-font-semibold"]',
                    'span:has-text("$")',
                    '.price',
                    '[data-price]',
                    'span'
                ]
                
                logger.info("💰 PROBANDO SELECTORES DE PRECIO:")
                for selector in price_selectors:
                    elements = await first_container.query_selector_all(selector)
                    if elements:
                        for i, elem in enumerate(elements[:3]):  # Solo primeros 3
                            text = await elem.text_content()
                            if text and text.strip():
                                logger.info(f"   {selector}[{i}]: '{text.strip()}'")
            
            else:
                logger.warning("❌ NO se encontraron contenedores con data-cnstrc-item-id")
                
                # Probar selectores alternativos
                logger.info("🔍 PROBANDO SELECTORES ALTERNATIVOS:")
                
                alt_selectors = [
                    "div[data-*]",
                    ".product-item", 
                    ".product-card",
                    "[data-testid*='product']",
                    ".grid-item"
                ]
                
                for selector in alt_selectors:
                    elements = await page.query_selector_all(selector)
                    logger.info(f"   {selector}: {len(elements)} elementos")
            
            # Guardar HTML para inspección manual
            html_content = await page.content()
            with open("debug_paris_v5.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("💾 HTML guardado en debug_paris_v5.html")
            
        except Exception as e:
            logger.error(f"❌ Error en debug: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_paris_dom())