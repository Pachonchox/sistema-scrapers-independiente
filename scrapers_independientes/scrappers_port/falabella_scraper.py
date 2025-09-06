"""
Scraper para Falabella.com - Smartphones
Extrae productos con precios, ratings y especificaciones
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
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_products(soup):
    """Extrae productos de Falabella basado en la estructura identificada"""
    products = []
    
    print("=== BUSCANDO PRODUCTOS FALABELLA ===")
    
    # Buscar contenedores de productos
    product_containers = soup.find_all('div', class_=re.compile(r'search-results.*grid-pod'))
    
    print(f"Contenedores de productos encontrados: {len(product_containers)}")
    
    for container in product_containers:
        try:
            # Buscar el link principal del producto
            main_link = container.find('a', attrs={'data-key': True})
            if not main_link:
                continue
                
            product_id = main_link.get('data-key', '')
            product_url = main_link.get('href', '')
            
            print(f"\nAnalizando producto ID: {product_id}")
            
            # Extraer marca
            brand_elem = container.find('b', class_=re.compile(r'pod-title'))
            brand = brand_elem.get_text(strip=True) if brand_elem else ""
            
            # Extraer nombre/descripción del producto
            name_elem = container.find('b', class_=re.compile(r'pod-subTitle'))
            product_name = name_elem.get_text(strip=True) if name_elem else ""
            
            # Extraer vendedor
            seller_elem = container.find('b', class_=re.compile(r'pod-sellerText'))
            seller = seller_elem.get_text(strip=True) if seller_elem else ""
            
            # Extraer imagen
            img_elem = container.find('img')
            image_url = ""
            image_alt = ""
            if img_elem:
                image_url = img_elem.get('src', '')
                image_alt = img_elem.get('alt', '')
            
            # Extraer precios
            cmr_price = ""
            internet_price = ""
            cmr_price_numeric = None
            internet_price_numeric = None
            
            # Precio CMR (con tarjeta)
            cmr_price_elem = container.find('li', attrs={'data-cmr-price': True})
            if cmr_price_elem:
                cmr_price = cmr_price_elem.get('data-cmr-price', '')
                try:
                    cmr_price_numeric = int(float(cmr_price.replace(',', '')))
                except:
                    pass
            
            # Precio internet (sin tarjeta)
            internet_price_elem = container.find('li', attrs={'data-internet-price': True})
            if internet_price_elem:
                internet_price = internet_price_elem.get('data-internet-price', '')
                try:
                    internet_price_numeric = int(float(internet_price.replace(',', '')))
                except:
                    pass
            
            # Extraer rating
            rating_elem = container.find('div', attrs={'data-rating': True})
            rating = rating_elem.get('data-rating', '0') if rating_elem else '0'
            
            # Extraer número de reviews
            reviews_elem = container.find('span', class_=re.compile(r'reviewCount'))
            reviews_text = reviews_elem.get_text(strip=True) if reviews_elem else '(0)'
            reviews_count = re.search(r'\((\d+)\)', reviews_text)
            reviews = reviews_count.group(1) if reviews_count else '0'
            
            # Buscar badges/stickers (envío gratis, descuentos, etc.)
            badges = []
            badge_elems = container.find_all('span', class_=re.compile(r'pod-badges-item'))
            for badge in badge_elems:
                badge_text = badge.get_text(strip=True)
                if badge_text:
                    badges.append(badge_text)
            
            # Verificar si es patrocinado
            is_sponsored = bool(container.find('div', class_=re.compile(r'patrocinado')))
            
            # Extraer especificaciones del nombre del producto
            storage = ""
            ram = ""
            color = ""
            
            # Storage
            storage_match = re.search(r'(\d+)gb', product_name.lower())
            if storage_match:
                storage = f"{storage_match.group(1)}GB"
            
            # RAM (si está mencionado)
            ram_match = re.search(r'(\d+)\+(\d+)gb', product_name.lower())
            if ram_match:
                ram = f"{ram_match.group(1)}GB"
                if not storage:  # Si no encontramos storage antes, usar el segundo número
                    storage = f"{ram_match.group(2)}GB"
            
            # Color
            colors = ['negro', 'blanco', 'azul', 'rojo', 'verde', 'gris', 'dorado', 'plateado', 'purple', 'rosa']
            for color_name in colors:
                if color_name in product_name.lower():
                    color = color_name.title()
                    break
            
            # Solo agregar productos válidos
            if product_id and product_name:
                product_data = {
                    'product_id': product_id,
                    'brand': brand,
                    'name': product_name,
                    'seller': seller,
                    'storage': storage,
                    'ram': ram,
                    'color': color,
                    'cmr_price': cmr_price,
                    'cmr_price_numeric': cmr_price_numeric,
                    'internet_price': internet_price,
                    'internet_price_numeric': internet_price_numeric,
                    'rating': rating,
                    'reviews_count': reviews,
                    'is_sponsored': is_sponsored,
                    'badges': ', '.join(badges),
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'product_url': product_url,
                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                products.append(product_data)
                
                print(f"  [OK] ID: {product_id}")
                print(f"  [OK] Marca: {brand}")
                print(f"  [OK] Nombre: {product_name[:50]}...")
                print(f"  [OK] Precio CMR: ${cmr_price}")
                print(f"  [OK] Precio Internet: ${internet_price}")
                print(f"  [OK] Rating: {rating} ({reviews} reviews)")
                print(f"  [OK] Patrocinado: {is_sponsored}")
                if badges:
                    print(f"  [OK] Badges: {', '.join(badges)}")
                
        except Exception as e:
            print(f"  [ERROR] procesando contenedor: {e}")
            continue
    
    return products

def scrape_falabella_smartphones():
    """Función principal de scraping"""
    URL = "https://www.falabella.com/falabella-cl/category/cat720161/Smartphones"
    
    print(f"=== SCRAPER FALABELLA.COM - SMARTPHONES ===")
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
        with open("falabella_smartphones_debug.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print("HTML guardado en falabella_smartphones_debug.html")
        
        # Extraer productos
        products = extract_products(soup)
        
        print(f"\n=== RESULTADOS FALABELLA ===")
        print(f"Total productos encontrados: {len(products)}")
        
        if products:
            # Guardar en Excel
            timestamp = int(time.time())
            filename = f"falabella_smartphones_{timestamp}.xlsx"
            
            df = pd.DataFrame(products)
            df.to_excel(filename, index=False)
            
            print(f"Datos guardados en: {filename}")
            print(f"\n=== MUESTRA DE PRODUCTOS ===")
            
            for i, product in enumerate(products[:5], 1):
                cmr_display = f"${product['cmr_price_numeric']:,}" if product['cmr_price_numeric'] else "N/A"
                internet_display = f"${product['internet_price_numeric']:,}" if product['internet_price_numeric'] else "N/A"
                sponsored_text = " [PATROCINADO]" if product['is_sponsored'] else ""
                
                print(f"{i}. {product['name']}{sponsored_text}")
                print(f"   Marca: {product['brand']}")
                print(f"   ID: {product['product_id']}")
                print(f"   Precio CMR: {cmr_display}")
                print(f"   Precio Internet: {internet_display}")
                print(f"   Rating: {product['rating']} ({product['reviews_count']} reviews)")
                print(f"   Vendedor: {product['seller']}")
                print(f"   Specs: {product['storage']} | {product['ram']} | {product['color']}")
                if product['badges']:
                    print(f"   Badges: {product['badges']}")
                print()
            
            # Estadísticas
            print(f"=== ESTADÍSTICAS FALABELLA ===")
            brands = [p['brand'] for p in products if p['brand']]
            brand_counts = {}
            for brand in brands:
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            print(f"Productos por marca:")
            for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {brand}: {count} productos")
            
            # Productos patrocinados
            sponsored_count = sum(1 for p in products if p['is_sponsored'])
            print(f"\nProductos patrocinados: {sponsored_count} de {len(products)}")
            
            # Rangos de precio
            cmr_prices = [p['cmr_price_numeric'] for p in products if p['cmr_price_numeric']]
            internet_prices = [p['internet_price_numeric'] for p in products if p['internet_price_numeric']]
            
            if cmr_prices:
                print(f"\nRangos de precio CMR:")
                print(f"  Mínimo: ${min(cmr_prices):,}")
                print(f"  Máximo: ${max(cmr_prices):,}")
                print(f"  Promedio: ${sum(cmr_prices)//len(cmr_prices):,}")
            
            if internet_prices:
                print(f"\nRangos de precio Internet:")
                print(f"  Mínimo: ${min(internet_prices):,}")
                print(f"  Máximo: ${max(internet_prices):,}")
                print(f"  Promedio: ${sum(internet_prices)//len(internet_prices):,}")
                
        else:
            print("No se encontraron productos")
            
            # Debug adicional
            print("\n=== DEBUG ===")
            print("Buscando elementos por patrones alternativos...")
            
            # Buscar cualquier contenedor que pueda ser un producto
            potential_products = soup.find_all('div', class_=re.compile(r'pod|product'))
            print(f"Elementos con clases 'pod' o 'product': {len(potential_products)}")
            
            # Buscar links que puedan ser productos
            product_links = soup.find_all('a', attrs={'data-key': True})
            print(f"Links con data-key: {len(product_links)}")
        
    except Exception as e:
        print(f"Error crítico: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("Navegador cerrado")
        
        print("Scraping Falabella completado")

if __name__ == "__main__":
    scrape_falabella_smartphones()