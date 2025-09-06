"""
Debug Ripley Aislado - Test solo metodo de extraccion
"""

import asyncio
import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.ripley_scraper_v5_improved import RipleyScraperV5Improved

async def debug_ripley_extraction_only():
    """Test aislado del metodo de extraccion de Ripley"""
    
    print("=== DEBUG RIPLEY AISLADO - SOLO EXTRACCION ===")
    
    scraper = None
    try:
        # Crear scraper
        scraper = RipleyScraperV5Improved()
        print("Scraper creado")
        
        # URL exacta como debug exitoso
        url = "https://simple.ripley.cl/tecno/celulares?source=menu&s=mdco&type=catalog"
        print(f"URL: {url}")
        
        # Obtener pagina (usa override con navegador visible)
        page = await scraper.get_page()
        if not page:
            print("ERROR: No se pudo crear pagina")
            return
        
        print("Pagina creada con navegador VISIBLE")
        
        # Navegar EXACTO como debug exitoso
        print("Navegando...")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        
        # Espera inicial EXACTA
        print("Esperando carga inicial (5s)...")
        await asyncio.sleep(5)
        
        # Scroll EXACTO como debug exitoso
        print("Realizando scroll obligatorio...")
        for i in range(5):
            scroll_to = (i + 1) * 720
            print(f"   Scroll {i+1}: hasta {scroll_to}px")
            await page.evaluate(f"window.scrollTo(0, {scroll_to})")
            await asyncio.sleep(1)
        
        # Scroll final
        print("   Scroll final hasta el fondo...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)
        
        # PRUEBA DIRECTA del metodo de extraccion PORT
        print("Ejecutando metodo de extraccion PORT...")
        products = await scraper._extract_products_port_ripley(page)
        
        print(f"RESULTADO: {len(products)} productos extraidos")
        
        if products:
            print("EXTRACCION EXITOSA - Muestra:")
            for i, product in enumerate(products[:3], 1):
                print(f"{i}. {product.name[:50]}...")
                print(f"   Codigo: {product.product_code}")
                print(f"   Marca: {product.brand}")
                print(f"   Precio Internet: {product.internet_price_text}")
                print()
        else:
            print("ERROR: 0 productos - Necesita investigacion adicional")
            
            # Debug del HTML
            print("Guardando HTML para debug...")
            html = await page.content()
            with open("debug_ripley_system_v5.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("HTML guardado en debug_ripley_system_v5.html")
            
            # Verificacion basica con BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            containers = soup.find_all('a', attrs={'data-partnumber': True})
            print(f"BeautifulSoup debug: {len(containers)} contenedores encontrados")
            
            if containers:
                print("CONTENEDORES EXISTEN - Problema en metodo de extraccion")
                # Mostrar primer contenedor para debug
                first = containers[0]
                print(f"Primer contenedor: data-partnumber={first.get('data-partnumber')}")
                print(f"Href: {first.get('href')}")
                
                # Buscar elementos internos
                name_elem = first.select_one('.catalog-product-details__name')
                print(f"Elemento nombre encontrado: {name_elem is not None}")
                if name_elem:
                    print(f"Texto nombre: {name_elem.get_text(strip=True)[:50]}...")
            else:
                print("NO HAY CONTENEDORES - Problema de carga/scroll")
        
    except Exception as e:
        print(f"ERROR CRITICO: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if scraper:
            try:
                await scraper.cleanup()
            except:
                pass
        print("Debug aislado completado")

if __name__ == "__main__":
    asyncio.run(debug_ripley_extraction_only())