"""
Scraper para ABC.cl - Smartphones
Extrae productos con precios, descuentos, ratings y especificaciones
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
    """Extrae productos de ABC basado en la estructura identificada"""
    products = []
    
    print("=== BUSCANDO PRODUCTOS ABC ===")
    
    # Buscar contenedores de productos con clase lp-product-tile
    product_containers = soup.find_all('div', class_='lp-product-tile js-lp-product-tile')
    
    print(f"Contenedores de productos encontrados: {len(product_containers)}")
    
    for container in product_containers:
        try:
            # Extraer ID del producto desde data-gtm
            product_id = ""
            gtm_click = container.get('data-gtm-click', '')
            if gtm_click:
                import json
                try:
                    gtm_data = json.loads(gtm_click)
                    products_data = gtm_data.get('ecommerce', {}).get('click', {}).get('products', [])
                    if products_data:
                        product_id = products_data[0].get('id', '')
                except:
                    pass
            
            # Extraer marca
            brand_elem = container.select_one('.brand-name')
            brand = brand_elem.get_text(strip=True) if brand_elem else ""
            
            # Extraer nombre del producto
            name_elem = container.select_one('.pdp-link a')
            product_name = ""
            product_url = ""
            if name_elem:
                product_name = name_elem.get_text(strip=True)
                product_url = name_elem.get('href', '')
                if product_url.startswith('/'):
                    product_url = f"https://www.abc.cl{product_url}"
            
            print(f"\nAnalizando producto: {product_name[:50]}...")
            
            # Extraer imagen
            img_elem = container.select_one('.tile-image')
            image_url = img_elem.get('src', '') if img_elem else ""
            image_alt = img_elem.get('alt', '') if img_elem else ""
            
            # Extraer precios
            la_polar_price_text = ""
            internet_price_text = ""
            normal_price_text = ""
            la_polar_price_numeric = None
            internet_price_numeric = None
            normal_price_numeric = None
            
            # Precio La Polar (con tarjeta)
            la_polar_elem = container.select_one('.la-polar.price .price-value')
            if la_polar_elem:
                la_polar_price_text = la_polar_elem.get_text(strip=True)
                price_value = la_polar_elem.get('data-value', '')
                if price_value:
                    try:
                        la_polar_price_numeric = int(float(price_value))
                    except:
                        pass
            
            # Precio Internet
            internet_elem = container.select_one('.internet.price .price-value')
            if internet_elem:
                internet_price_text = internet_elem.get_text(strip=True)
                price_value = internet_elem.get('data-value', '')
                if price_value:
                    try:
                        internet_price_numeric = int(float(price_value))
                    except:
                        pass
            
            # Precio Normal
            normal_elem = container.select_one('.normal.price .price-value')
            if normal_elem:
                normal_price_text = normal_elem.get_text(strip=True)
                price_value = normal_elem.get('data-value', '')
                if price_value:
                    try:
                        normal_price_numeric = int(float(price_value))
                    except:
                        pass
            
            # Extraer descuento
            discount_elem = container.select_one('.promotion-badge')
            discount_percent = discount_elem.get_text(strip=True) if discount_elem else ""
            
            # Extraer especificaciones destacadas
            screen_size = ""
            internal_memory = ""
            camera_info = ""
            
            spec_items = container.select('.prices-actions__destacados__items li span')
            for spec in spec_items:
                spec_text = spec.get_text(strip=True)
                if "Tamaño de la pantalla:" in spec_text:
                    screen_size = spec_text.replace("Tamaño de la pantalla:", "").strip()
                elif "Memoria interna:" in spec_text:
                    internal_memory = spec_text.replace("Memoria interna:", "").strip()
                elif "Cámara posterior:" in spec_text:
                    camera_info = spec_text.replace("Cámara posterior:", "").strip()
            
            # Extraer rating y reviews
            rating = ""
            reviews_count = ""
            
            # Rating desde Power Reviews
            rating_elem = container.select_one('.pr-snippet-rating-decimal')
            if rating_elem:
                rating = rating_elem.get_text(strip=True)
            
            reviews_elem = container.select_one('.pr-category-snippet__total')
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                reviews_match = re.search(r'(\d+)', reviews_text)
                if reviews_match:
                    reviews_count = reviews_match.group(1)
            
            # Extraer badges flotantes
            floating_badges = []
            badge_elements = container.select('.floating-badge img, .outstanding-container img')
            for badge in badge_elements:
                badge_alt = badge.get('alt', '').strip()
                badge_title = badge.get('title', '').strip()
                if badge_alt and badge_alt not in ['', 'Rosen']:
                    floating_badges.append(badge_alt)
                elif badge_title:
                    floating_badges.append(badge_title)
            
            # Extraer color del nombre del producto
            color = ""
            if "medianoche" in product_name.lower():
                color = "Medianoche"
            elif "negro" in product_name.lower() or "black" in product_name.lower():
                color = "Negro"
            elif "blanco" in product_name.lower() or "white" in product_name.lower():
                color = "Blanco"
            elif "azul" in product_name.lower() or "blue" in product_name.lower():
                color = "Azul"
            elif "rojo" in product_name.lower() or "red" in product_name.lower():
                color = "Rojo"
            elif "verde" in product_name.lower() or "green" in product_name.lower():
                color = "Verde"
            elif "dorado" in product_name.lower() or "gold" in product_name.lower():
                color = "Dorado"
            elif "plateado" in product_name.lower() or "silver" in product_name.lower():
                color = "Plateado"
            
            # Solo agregar productos válidos
            if product_name and product_id:
                product_data = {
                    'product_id': product_id,
                    'brand': brand,
                    'name': product_name,
                    'color': color,
                    'screen_size': screen_size,
                    'internal_memory': internal_memory,
                    'camera_info': camera_info,
                    'la_polar_price_text': la_polar_price_text,
                    'la_polar_price': la_polar_price_numeric,
                    'internet_price_text': internet_price_text,
                    'internet_price': internet_price_numeric,
                    'normal_price_text': normal_price_text,
                    'normal_price': normal_price_numeric,
                    'discount_percent': discount_percent,
                    'rating': rating,
                    'reviews_count': reviews_count,
                    'floating_badges': ', '.join(floating_badges) if floating_badges else "",
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'product_url': product_url,
                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                products.append(product_data)
                
                print(f"  [OK] ID: {product_id}")
                print(f"  [OK] Marca: {brand}")
                print(f"  [OK] Nombre: {product_name[:50]}...")
                print(f"  [OK] Precio La Polar: {la_polar_price_text}")
                print(f"  [OK] Precio Internet: {internet_price_text}")
                print(f"  [OK] Precio Normal: {normal_price_text}")
                print(f"  [OK] Descuento: {discount_percent}")
                print(f"  [OK] Rating: {rating} ({reviews_count} reseñas)")
                print(f"  [OK] Specs: {screen_size} | {internal_memory} | {camera_info[:30]}...")
                if color:
                    print(f"  [OK] Color: {color}")
                if floating_badges:
                    print(f"  [OK] Badges: {', '.join(floating_badges[:2])}...")
                
        except Exception as e:
            print(f"  [ERROR] procesando contenedor: {e}")
            continue
    
    return products

def scrape_abc_smartphones():
    """Función principal de scraping"""
    URL = "https://www.abc.cl/tecnologia/celulares/smartphones/"
    
    print(f"=== SCRAPER ABC.CL - SMARTPHONES ===")
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
        with open("abc_smartphones_debug.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print("HTML guardado en abc_smartphones_debug.html")
        
        # Extraer productos
        products = extract_products(soup)
        
        print(f"\n=== RESULTADOS ABC ===")
        print(f"Total productos encontrados: {len(products)}")
        
        if products:
            # Guardar en Excel
            timestamp = int(time.time())
            filename = f"abc_smartphones_{timestamp}.xlsx"
            
            df = pd.DataFrame(products)
            df.to_excel(filename, index=False)
            
            print(f"Datos guardados en: {filename}")
            print(f"\n=== MUESTRA DE PRODUCTOS ===")
            
            for i, product in enumerate(products[:5], 1):
                la_polar_display = f"${product['la_polar_price']:,}" if product['la_polar_price'] else "N/A"
                internet_display = f"${product['internet_price']:,}" if product['internet_price'] else "N/A"
                normal_display = f"${product['normal_price']:,}" if product['normal_price'] else "N/A"
                
                print(f"{i}. {product['name']}")
                print(f"   Marca: {product['brand']}")
                print(f"   ID: {product['product_id']}")
                print(f"   Precio La Polar: {la_polar_display}")
                print(f"   Precio Internet: {internet_display}")
                print(f"   Precio Normal: {normal_display}")
                print(f"   Descuento: {product['discount_percent']}")
                print(f"   Rating: {product['rating']} ({product['reviews_count']} reseñas)")
                print(f"   Specs: {product['screen_size']} | {product['internal_memory']}")
                if product['color']:
                    print(f"   Color: {product['color']}")
                if product['floating_badges']:
                    print(f"   Badges: {product['floating_badges']}")
                print()
            
            # Estadísticas
            print(f"=== ESTADÍSTICAS ABC ===")
            brands = [p['brand'] for p in products if p['brand']]
            brand_counts = {}
            for brand in brands:
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            print(f"Productos por marca:")
            for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {brand}: {count} productos")
            
            # Rangos de precio La Polar
            la_polar_prices = [p['la_polar_price'] for p in products if p['la_polar_price']]
            if la_polar_prices:
                print(f"\nRangos de precio La Polar (con tarjeta):")
                print(f"  Mínimo: ${min(la_polar_prices):,}")
                print(f"  Máximo: ${max(la_polar_prices):,}")
                print(f"  Promedio: ${sum(la_polar_prices)//len(la_polar_prices):,}")
            
            # Rangos de precio Internet
            internet_prices = [p['internet_price'] for p in products if p['internet_price']]
            if internet_prices:
                print(f"\nRangos de precio Internet:")
                print(f"  Mínimo: ${min(internet_prices):,}")
                print(f"  Máximo: ${max(internet_prices):,}")
                print(f"  Promedio: ${sum(internet_prices)//len(internet_prices):,}")
            
            # Rating promedio
            ratings = [float(p['rating']) for p in products if p['rating'] and p['rating'].replace('.', '').isdigit()]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                print(f"\nRating promedio: {avg_rating:.1f} estrellas")
                
        else:
            print("No se encontraron productos")
            
            # Debug adicional
            print("\n=== DEBUG ===")
            print("Buscando elementos por patrones alternativos...")
            
            # Buscar cualquier contenedor que pueda ser un producto
            potential_products = soup.find_all('div', class_=re.compile(r'product|tile'))
            print(f"Elementos con clases 'product' o 'tile': {len(potential_products)}")
        
    except Exception as e:
        print(f"Error crítico: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("Navegador cerrado")
        
        print("Scraping ABC completado")

if __name__ == "__main__":
    scrape_abc_smartphones()