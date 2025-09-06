"""
Debug Ripley Simple - Sin emojis
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from datetime import datetime

async def debug_ripley_simple():
    """Debug directo de Ripley sin sistema de scrapers"""
    
    print("=== DEBUG RIPLEY INDIVIDUAL ===")
    
    url = "https://simple.ripley.cl/tecno/celulares?source=menu&s=mdco&type=catalog"
    print(f"URL: {url}")
    
    async with async_playwright() as p:
        # Configurar navegador VISIBLE como PORT original
        browser = await p.chromium.launch(
            headless=False,  # VISIBLE
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        print("Navegando a Ripley...")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        
        print("Esperando carga inicial...")
        await asyncio.sleep(5)
        
        # SCROLL OBLIGATORIO como PORT
        print("Realizando scroll obligatorio...")
        
        for i in range(5):  # 5 scrolls como el PORT
            scroll_to = (i + 1) * 720
            print(f"   Scroll {i+1}: hasta {scroll_to}px")
            await page.evaluate(f"window.scrollTo(0, {scroll_to})")
            await asyncio.sleep(1)
        
        # Scroll final hasta el fondo
        print("   Scroll final hasta el fondo...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)
        
        # Obtener HTML como PORT (BeautifulSoup)
        print("Obteniendo HTML...")
        html_content = await page.content()
        
        # Guardar HTML para debug
        with open("debug_ripley_v5.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("HTML guardado en: debug_ripley_v5.html")
        
        # Parsear con BeautifulSoup (EXACTO como PORT)
        soup = BeautifulSoup(html_content, 'lxml')
        
        print("\n=== ANALISIS PORT EXACTO ===")
        
        # EXACTO como PORT: buscar contenedores 'a' con data-partnumber
        product_containers = soup.find_all('a', attrs={'data-partnumber': True})
        print(f"Contenedores con 'a[data-partnumber]': {len(product_containers)}")
        
        if not product_containers:
            # Debug adicional si no encuentra
            print("\n=== DEBUG ADICIONAL ===")
            
            # Buscar cualquier 'a' con atributos data-*
            all_data_links = soup.find_all('a', attrs=lambda x: x and any(k.startswith('data-') for k in x.keys()) if x else False)
            print(f"Links con atributos data-*: {len(all_data_links)}")
            
            # Mostrar primeros 3 para análisis
            for i, link in enumerate(all_data_links[:3], 1):
                print(f"   Link {i}: {link.attrs}")
            
            # Buscar contenedores de productos alternativos
            product_divs = soup.find_all('div', class_=re.compile(r'catalog|product'))
            print(f"DIVs con 'catalog' o 'product': {len(product_divs)}")
            
            # Buscar por patrones de clase comunes
            card_divs = soup.find_all('div', class_=re.compile(r'card|item'))
            print(f"DIVs con 'card' o 'item': {len(card_divs)}")
            
        else:
            print("\n=== EXTRACCION PORT EXACTA ===")
            
            products = []
            
            for i, container in enumerate(product_containers[:10], 1):  # Solo primeros 10 para debug
                try:
                    print(f"\nAnalizando producto {i}:")
                    
                    # Extraer data-partnumber (EXACTO como PORT)
                    product_code = container.get('data-partnumber', '')
                    product_url = container.get('href', '')
                    
                    print(f"   Codigo: {product_code}")
                    print(f"   URL: {product_url}")
                    
                    if not product_code:
                        print("   Sin codigo, saltando...")
                        continue
                    
                    # Link completo (EXACTO como PORT)
                    full_link = f"https://simple.ripley.cl{product_url}" if product_url.startswith('/') else product_url
                    
                    # Buscar marca (EXACTO como PORT)
                    brand_elem = container.select_one('.brand-logo span, .catalog-product-details__logo-container span')
                    brand = brand_elem.get_text(strip=True) if brand_elem else ""
                    print(f"   Marca: {brand}")
                    
                    # Buscar nombre (EXACTO como PORT)
                    name_elem = container.select_one('.catalog-product-details__name')
                    product_name = name_elem.get_text(strip=True) if name_elem else ""
                    print(f"   Nombre: {product_name[:50]}...")
                    
                    # Precios (EXACTO como PORT)
                    # Precio normal (tachado)
                    normal_price_elem = container.select_one('.catalog-prices__list-price.catalog-prices__line_thru')
                    normal_price_text = normal_price_elem.get_text(strip=True) if normal_price_elem else ""
                    print(f"   Precio Normal: {normal_price_text}")
                    
                    # Precio internet
                    internet_price_elem = container.select_one('.catalog-prices__offer-price')
                    internet_price_text = internet_price_elem.get_text(strip=True) if internet_price_elem else ""
                    print(f"   Precio Internet: {internet_price_text}")
                    
                    # Precio tarjeta Ripley
                    ripley_price_elem = container.select_one('.catalog-prices__card-price')
                    ripley_price_text = ripley_price_elem.get_text(strip=True) if ripley_price_elem else ""
                    print(f"   Precio Ripley: {ripley_price_text}")
                    
                    # Solo agregar si tiene código y nombre
                    if product_code and product_name:
                        products.append({
                            'code': product_code,
                            'name': product_name,
                            'brand': brand,
                            'normal_price': normal_price_text,
                            'internet_price': internet_price_text,
                            'ripley_price': ripley_price_text,
                            'url': full_link
                        })
                        print(f"   Producto valido agregado")
                    else:
                        print(f"   Producto invalido (falta codigo o nombre)")
                        
                except Exception as e:
                    print(f"   Error procesando producto {i}: {e}")
                    continue
            
            print(f"\n=== RESULTADOS DEBUG ===")
            print(f"Total productos extraidos: {len(products)}")
            
            if products:
                print("\nMuestra de productos:")
                for i, product in enumerate(products, 1):
                    print(f"{i}. {product['name'][:50]}...")
                    print(f"   Codigo: {product['code']}")
                    print(f"   Marca: {product['brand']}")
                    print(f"   Precios: {product['internet_price']} | {product['ripley_price']}")
                    print()
            
        await browser.close()
        print("\nDebug Ripley individual completado")

if __name__ == "__main__":
    asyncio.run(debug_ripley_simple())