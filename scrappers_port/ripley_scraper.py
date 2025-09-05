"""
Scraper para Ripley.cl - Smartphones
Extrae productos con precios, descuentos y especificaciones
"""

from bs4 import BeautifulSoup
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime

def setup_driver():
    """Configura driver de Chrome"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Comentado para navegador visible
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_products(soup):
    """Extrae productos de Ripley basado en la estructura identificada"""
    products = []
    
    print("=== BUSCANDO PRODUCTOS RIPLEY ===" )
    
    # Buscar contenedores de productos con clase catalog-product-item
    product_containers = soup.find_all('a', attrs={'data-partnumber': True})
    
    print(f"Contenedores de productos encontrados: {len(product_containers)}")
    
    for container in product_containers:
        try:
            # Extraer información desde los atributos
            product_code = container.get('data-partnumber', '')
            product_url = container.get('href', '')
            
            print(f"\nAnalizando producto: {product_code}")
            
            # Link completo del producto
            full_link = f"https://simple.ripley.cl{product_url}" if product_url.startswith('/') else product_url
            
            # Buscar marca
            brand_elem = container.select_one('.brand-logo span, .catalog-product-details__logo-container span')
            brand = brand_elem.get_text(strip=True) if brand_elem else ""
            
            # Buscar nombre del producto
            name_elem = container.select_one('.catalog-product-details__name')
            product_name = name_elem.get_text(strip=True) if name_elem else ""
            
            # Extraer precios
            normal_price_text = ""
            internet_price_text = ""
            ripley_price_text = ""
            normal_price_numeric = None
            internet_price_numeric = None
            ripley_price_numeric = None
            
            # Precio normal (tachado)
            normal_price_elem = container.select_one('.catalog-prices__list-price.catalog-prices__line_thru')
            if normal_price_elem:
                normal_price_text = normal_price_elem.get_text(strip=True)
                price_match = re.search(r'\$?([0-9.,]+)', normal_price_text.replace('.', ''))
                if price_match:
                    try:
                        normal_price_numeric = int(price_match.group(1).replace(',', ''))
                    except:
                        pass
            
            # Precio internet
            internet_price_elem = container.select_one('.catalog-prices__offer-price')
            if internet_price_elem:
                internet_price_text = internet_price_elem.get_text(strip=True)
                price_match = re.search(r'\$?([0-9.,]+)', internet_price_text.replace('.', ''))
                if price_match:
                    try:
                        internet_price_numeric = int(price_match.group(1).replace(',', ''))
                    except:
                        pass
            
            # Precio tarjeta Ripley
            ripley_price_elem = container.select_one('.catalog-prices__card-price')
            if ripley_price_elem:
                ripley_price_text = ripley_price_elem.get_text(strip=True).split('$')[1].split(' ')[0] if '$' in ripley_price_elem.get_text() else ""
                if ripley_price_text:
                    price_match = re.search(r'([0-9.,]+)', ripley_price_text.replace('.', ''))
                    if price_match:
                        try:
                            ripley_price_numeric = int(price_match.group(1).replace(',', ''))
                        except:
                            pass
            
            # Descuento
            discount_elem = container.select_one('.catalog-product-details__discount-tag')
            discount_percent = discount_elem.get_text(strip=True) if discount_elem else ""
            
            # Imagen principal
            img_elem = container.select_one('img')
            image_url = img_elem.get('src', '') if img_elem else ""
            image_alt = img_elem.get('alt', '') if img_elem else ""
            
            # Colores disponibles
            color_elements = container.select('.catalog-colors-option-outer')
            colors = []
            for color_elem in color_elements:
                color_title = color_elem.get('title', '')
                if color_title:
                    colors.append(color_title)
            
            # Emblemas/badges
            emblem_elements = container.select('.emblem')
            emblems = []
            for emblem in emblem_elements:
                emblem_text = emblem.get_text(strip=True)
                if emblem_text:
                    emblems.append(emblem_text)
            
            # Extraer especificaciones del nombre
            storage = ""
            ram = ""
            screen_size = ""
            camera = ""
            
            # Almacenamiento
            storage_match = re.search(r'(\d+)\s*gb(?!\s+ram)', product_name.lower())
            if storage_match:
                storage = f"{storage_match.group(1)}GB"
            
            # RAM
            ram_match = re.search(r'(\d+)\s*gb\s+ram', product_name.lower())
            if ram_match:
                ram = f"{ram_match.group(1)}GB"
            
            # Tamaño de pantalla
            screen_match = re.search(r'(\d+\.?\d*)"', product_name)
            if screen_match:
                screen_size = f"{screen_match.group(1)}\""
            
            # Cámara
            camera_match = re.search(r'(\d+)mp', product_name.lower())
            if camera_match:
                camera = f"{camera_match.group(1)}MP"
            
            # Solo agregar productos válidos
            if product_code and product_name:
                product_data = {
                    'product_code': product_code,
                    'brand': brand,
                    'name': product_name,
                    'screen_size': screen_size,
                    'storage': storage,
                    'ram': ram,
                    'camera': camera,
                    'colors': ', '.join(colors),
                    'normal_price_text': normal_price_text,
                    'normal_price': normal_price_numeric,
                    'internet_price_text': internet_price_text,
                    'internet_price': internet_price_numeric,
                    'ripley_price_text': ripley_price_text,
                    'ripley_price': ripley_price_numeric,
                    'discount_percent': discount_percent,
                    'emblems': ', '.join(emblems),
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'product_url': full_link,
                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                products.append(product_data)
                
                print(f"  [OK] Código: {product_code}")
                print(f"  [OK] Marca: {brand}")
                print(f"  [OK] Nombre: {product_name[:50]}...")
                print(f"  [OK] Precio Normal: {normal_price_text}")
                print(f"  [OK] Precio Internet: {internet_price_text}")
                print(f"  [OK] Precio Ripley: {ripley_price_text}")
                print(f"  [OK] Descuento: {discount_percent}")
                print(f"  [OK] Specs: {screen_size} | {storage} | {ram} | {camera}")
                if colors:
                    print(f"  [OK] Colores: {', '.join(colors)}")
                if emblems:
                    print(f"  [OK] Emblemas: {', '.join(emblems[:2])}...")  # Solo primeros 2 para no saturar
                
        except Exception as e:
            print(f"  [ERROR] procesando contenedor: {e}")
            continue
    
    return products

def scrape_ripley_smartphones():
    """Función principal de scraping"""
    URL = "https://simple.ripley.cl/tecno/celulares?source=menu&s=mdco&type=catalog"
    
    print(f"=== SCRAPER RIPLEY.CL - SMARTPHONES ===" )
    print(f"URL: {URL}")
    print(f"Inicio: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)
    
    driver = None
    try:
        print("Iniciando navegador...")
        driver = setup_driver()
        driver.get(URL)
        
        print("Esperando carga de productos...")
        time.sleep(10)
        
        # Hacer scroll para cargar más productos
        print("Haciendo scroll para cargar productos...")
        for i in range(3):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/3});")
            time.sleep(3)
        
        # Obtener HTML final
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Guardar HTML para debug
        with open("ripley_smartphones_debug.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print("HTML guardado en ripley_smartphones_debug.html")
        
        # Extraer productos
        products = extract_products(soup)
        
        print(f"\n=== RESULTADOS RIPLEY ===" )
        print(f"Total productos encontrados: {len(products)}")
        
        if products:
            # Guardar en Excel
            timestamp = int(time.time())
            filename = f"ripley_smartphones_{timestamp}.xlsx"
            
            df = pd.DataFrame(products)
            df.to_excel(filename, index=False)
            
            print(f"Datos guardados en: {filename}")
            print(f"\n=== MUESTRA DE PRODUCTOS ===" )
            
            for i, product in enumerate(products[:5], 1):
                internet_display = f"${product['internet_price']:,}" if product['internet_price'] else "N/A"
                ripley_display = f"${product['ripley_price']:,}" if product['ripley_price'] else "N/A"
                normal_display = f" (antes: ${product['normal_price']:,})" if product['normal_price'] else ""
                
                print(f"{i}. {product['name']}")
                print(f"   Marca: {product['brand']}")
                print(f"   Código: {product['product_code']}")
                print(f"   Precio Internet: {internet_display}")
                print(f"   Precio Ripley: {ripley_display}{normal_display}")
                print(f"   Descuento: {product['discount_percent']}")
                print(f"   Specs: {product['screen_size']} | {product['storage']} | {product['ram']} | {product['camera']}")
                if product['colors']:
                    print(f"   Colores: {product['colors']}")
                print()
            
            # Estadísticas
            print(f"=== ESTADÍSTICAS RIPLEY ===" )
            brands = [p['brand'] for p in products if p['brand']]
            brand_counts = {}
            for brand in brands:
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            print(f"Productos por marca:")
            for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {brand}: {count} productos")
            
            # Rangos de precio
            internet_prices = [p['internet_price'] for p in products if p['internet_price']]
            ripley_prices = [p['ripley_price'] for p in products if p['ripley_price']]
            
            if internet_prices:
                print(f"\nRangos de precio Internet:")
                print(f"  Mínimo: ${min(internet_prices):,}")
                print(f"  Máximo: ${max(internet_prices):,}")
                print(f"  Promedio: ${sum(internet_prices)//len(internet_prices):,}")
            
            if ripley_prices:
                print(f"\nRangos de precio Ripley:")
                print(f"  Mínimo: ${min(ripley_prices):,}")
                print(f"  Máximo: ${max(ripley_prices):,}")
                print(f"  Promedio: ${sum(ripley_prices)//len(ripley_prices):,}")
                
        else:
            print("No se encontraron productos")
            
            # Debug adicional
            print("\n=== DEBUG ===")
            print("Buscando elementos por patrones alternativos...")
            
            # Buscar cualquier contenedor que pueda ser un producto
            potential_products = soup.find_all('div', class_=re.compile(r'catalog|product'))
            print(f"Elementos con clases 'catalog' o 'product': {len(potential_products)}")
            
            # Buscar links que puedan ser productos
            product_links = soup.find_all('a', attrs={'data-partnumber': True})
            print(f"Links con data-partnumber: {len(product_links)}")
        
    except Exception as e:
        print(f"Error crítico: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("Navegador cerrado")
        
        print("Scraping Ripley completado")

if __name__ == "__main__":
    scrape_ripley_smartphones()