"""
Scraper final para París.cl - Celulares
Extrae productos completos con precios, descuentos y especificaciones técnicas
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
    """Extrae productos basado en la estructura identificada de París.cl"""
    products = []
    
    print("=== BUSCANDO PRODUCTOS CON NUEVA ESTRUCTURA ===")
    
    # Buscar contenedores de productos con data-cnstrc-item-id
    product_containers = soup.find_all('div', attrs={'data-cnstrc-item-id': True})
    
    print(f"Contenedores con data-cnstrc-item-id encontrados: {len(product_containers)}")
    
    for container in product_containers:
        try:
            # Extraer información desde los data attributes
            product_code = container.get('data-cnstrc-item-id', '')
            product_name = container.get('data-cnstrc-item-name', '').strip()
            price_from_data = container.get('data-cnstrc-item-price', '')
            
            print(f"\nAnalizando producto: {product_code}")
            print(f"  Nombre desde data: {product_name}")
            print(f"  Precio desde data: {price_from_data}")
            
            # Filtro MK removido - capturar todos los productos
            # if not product_code.startswith('MK'):
            #     print(f"  - Saltando, código no válido: {product_code}")
            #     continue
            
            # Buscar el link del producto (elemento <a> dentro del contenedor)
            link_element = container.find('a', href=True)
            product_link = ""
            if link_element:
                href = link_element.get('href', '')
                if href.startswith('/'):
                    product_link = f"https://www.paris.cl{href}"
                elif href.startswith('http'):
                    product_link = href
            
            # Buscar precios en el HTML (más preciso que data attribute)
            current_price_text = ""
            current_price_numeric = None
            old_price_text = ""
            old_price_numeric = None
            discount_percent = ""
            
            # Precio actual (span con clases específicas)
            current_price_elem = container.select_one('span.ui-text-\\[13px\\].ui-leading-\\[15px\\].desktop\\:ui-text-lg, span[class*="ui-font-semibold"][class*="desktop:ui-font-medium"]')
            if current_price_elem:
                current_price_text = current_price_elem.get_text(strip=True)
                price_match = re.search(r'\$?([\d.,]+)', current_price_text.replace('.', ''))
                if price_match:
                    try:
                        current_price_numeric = int(price_match.group(1).replace(',', ''))
                    except:
                        pass
            
            # Precio anterior (span con line-through)
            old_price_elem = container.select_one('span.ui-line-through.ui-font-semibold')
            if old_price_elem:
                old_price_text = old_price_elem.get_text(strip=True)
                price_match = re.search(r'\$?([\d.,]+)', old_price_text.replace('.', ''))
                if price_match:
                    try:
                        old_price_numeric = int(price_match.group(1).replace(',', ''))
                    except:
                        pass
            
            # Descuento (div con data-testid="paris-label")
            discount_elem = container.select_one('div[data-testid="paris-label"][aria-label*="%"]')
            if discount_elem:
                discount_percent = discount_elem.get('aria-label', '')
            
            # Marca (span con ui-font-semibold más corto - generalmente la primera línea)
            brand = ""
            brand_elem = container.select_one('span.ui-font-semibold.ui-line-clamp-2.ui-text-\\[11px\\]')
            if brand_elem:
                brand = brand_elem.get_text(strip=True)
            
            # Imagen principal
            img_element = container.find('img', alt="Imagen de producto")
            img_src = ""
            if img_element:
                # Obtener la imagen de mayor resolución del srcset
                srcset = img_element.get('srcset', '')
                if srcset:
                    # Tomar la última URL (mayor resolución)
                    urls = re.findall(r'(https://[^\s]+)', srcset)
                    img_src = urls[-1] if urls else img_element.get('src', '')
                else:
                    img_src = img_element.get('src', '')
            
            # Rating
            rating_elem = container.select_one('button[data-testid="star-rating-rating-value"]')
            rating = rating_elem.get_text(strip=True) if rating_elem else "0"
            
            # Número de reviews
            reviews_elem = container.select_one('button[data-testid="star-rating-total-rating"]')
            reviews = reviews_elem.get_text(strip=True).replace('(', '').replace(')', '') if reviews_elem else "0"
            
            # Extraer especificaciones del nombre
            storage = ""
            ram = ""
            network = ""
            color = ""
            
            # Storage (primer número seguido de GB que no sea RAM)
            storage_match = re.search(r'(\d+)gb(?!\s+ram)', product_name.lower())
            if storage_match:
                storage = f"{storage_match.group(1)}GB"
            
            # RAM
            ram_match = re.search(r'(\d+)gb\s+ram', product_name.lower())
            if ram_match:
                ram = f"{ram_match.group(1)}GB"
            
            # Red (4G/5G)
            network_match = re.search(r'(4g|5g)', product_name.lower())
            if network_match:
                network = network_match.group(1).upper()
            
            # Color (última palabra después de especificaciones)
            color_match = re.search(r'(negro|blanco|azul|rojo|verde|gris|dorado|plateado|purpura|rosa)$', product_name.lower())
            if color_match:
                color = color_match.group(1).title()
            
            # Solo agregar si tiene información válida
            if product_code and product_name:
                product_data = {
                    'product_code': product_code,
                    'name': product_name,
                    'brand': brand,
                    'storage': storage,
                    'ram': ram,
                    'network': network,
                    'color': color,
                    'current_price_text': current_price_text,
                    'current_price': current_price_numeric,
                    'old_price_text': old_price_text,
                    'old_price': old_price_numeric,
                    'discount_percent': discount_percent,
                    'rating': rating,
                    'reviews_count': reviews,
                    'image_url': img_src,
                    'product_link': product_link,
                    'price_from_data': price_from_data,
                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                products.append(product_data)
                
                print(f"  [OK] Código: {product_code}")
                print(f"  [OK] Nombre: {product_name}")
                print(f"  [OK] Marca: {brand}")
                print(f"  [OK] Precio actual: {current_price_text}")
                print(f"  [OK] Precio anterior: {old_price_text}")
                print(f"  [OK] Descuento: {discount_percent}")
                print(f"  [OK] Storage: {storage} | RAM: {ram} | Red: {network}")
                
        except Exception as e:
            print(f"  [ERROR] procesando contenedor: {e}")
            continue
    
    return products

def scrape_paris_celulares():
    """Función principal de scraping"""
    URL = "https://www.paris.cl/tecnologia/celulares/"
    
    print(f"=== SCRAPER PARÍS.CL - CELULARES FINAL ===")
    print(f"URL: {URL}")
    print(f"Inicio: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)
    
    driver = None
    try:
        print("Iniciando navegador...")
        driver = setup_driver()
        driver.get(URL)
        
        print("Esperando carga de productos...")
        # Esperar más tiempo para que carguen los productos dinámicamente
        time.sleep(10)
        
        # Hacer scroll para cargar más productos
        print("Haciendo scroll para cargar productos...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(3)
        
        # Obtener HTML final
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Guardar HTML para debug
        with open("paris_celulares_final_debug.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print("HTML guardado en paris_celulares_final_debug.html")
        
        # Extraer productos
        products = extract_products(soup)
        
        print(f"\n=== RESULTADOS FINALES ===")
        print(f"Total productos encontrados: {len(products)}")
        
        if products:
            # Guardar en Excel
            timestamp = int(time.time())
            filename = f"paris_celulares_final_{timestamp}.xlsx"
            
            df = pd.DataFrame(products)
            df.to_excel(filename, index=False)
            
            print(f"Datos guardados en: {filename}")
            print(f"\n=== MUESTRA DE PRODUCTOS ===")
            
            for i, product in enumerate(products[:5], 1):
                price_display = f"${product['current_price']:,}" if product['current_price'] else "N/A"
                old_price_display = f" (antes: ${product['old_price']:,})" if product['old_price'] else ""
                print(f"{i}. {product['name']}")
                print(f"   Marca: {product['brand']}")
                print(f"   Código: {product['product_code']}")
                print(f"   Precio: {price_display}{old_price_display}")
                print(f"   Descuento: {product['discount_percent']}")
                print(f"   Specs: {product['storage']} | {product['ram']} | {product['network']} | {product['color']}")
                print()
            
            # Estadísticas
            print(f"=== ESTADÍSTICAS ===")
            brands = [p['brand'] for p in products if p['brand']]
            brand_counts = {}
            for brand in brands:
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            print(f"Productos por marca:")
            for brand, count in brand_counts.items():
                print(f"  {brand}: {count} productos")
            
            # Rangos de precio
            prices = [p['current_price'] for p in products if p['current_price']]
            if prices:
                print(f"\nRangos de precio:")
                print(f"  Mínimo: ${min(prices):,}")
                print(f"  Máximo: ${max(prices):,}")
                print(f"  Promedio: ${sum(prices)//len(prices):,}")
                
        else:
            print("No se encontraron productos")
        
    except Exception as e:
        print(f"Error crítico: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("Navegador cerrado")
        
        print("Scraping París.cl completado")

if __name__ == "__main__":
    scrape_paris_celulares()