"""
Scraper para Hites.com - Smartphones
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
    """Extrae productos de Hites basado en la estructura identificada"""
    products = []
    
    print("=== BUSCANDO PRODUCTOS HITES ===")
    
    # Buscar contenedores de productos con clase product-tile-body
    product_containers = soup.find_all('div', class_='product-tile-body')
    
    print(f"Contenedores de productos encontrados: {len(product_containers)}")
    
    for container in product_containers:
        try:
            # Extraer marca
            brand_elem = container.select_one('.product-brand')
            brand = brand_elem.get_text(strip=True) if brand_elem else ""
            
            # Extraer nombre del producto
            name_elem = container.select_one('.product-name--bundle')
            product_name = ""
            product_url = ""
            if name_elem:
                product_name = name_elem.get_text(strip=True)
                product_url = name_elem.get('href', '')
                if product_url.startswith('/'):
                    product_url = f"https://www.hites.com{product_url}"
            
            print(f"\nAnalizando producto: {product_name[:50]}...")
            
            # Extraer SKU
            sku_elem = container.select_one('.product-sku')
            sku = ""
            if sku_elem:
                sku_text = sku_elem.get_text(strip=True)
                sku = sku_text.replace("SKU: ", "")
            
            # Extraer vendedor (marketplace)
            seller_elem = container.select_one('.marketplace-info-plp b')
            seller = seller_elem.get_text(strip=True) if seller_elem else "Hites"
            
            # Extraer atributos principales
            storage = ""
            screen_size = ""
            front_camera = ""
            
            attribute_items = container.select('.attribute-values')
            for attr in attribute_items:
                attr_text = attr.get_text(strip=True)
                if "Almacenamiento:" in attr_text:
                    storage = attr_text.replace("Almacenamiento:", "").strip()
                elif "Tamaño De Pantalla:" in attr_text:
                    screen_size = attr_text.replace("Tamaño De Pantalla:", "").strip()
                elif "Cámara Frontal:" in attr_text:
                    front_camera = attr_text.replace("Cámara Frontal:", "").strip()
            
            # Extraer precios
            current_price_text = ""
            original_price_text = ""
            discount_percent = ""
            current_price_numeric = None
            original_price_numeric = None
            
            # Precio actual (sales)
            current_price_elem = container.select_one('.price-item.sales .value')
            if current_price_elem:
                current_price_text = current_price_elem.get_text(strip=True)
                price_content = current_price_elem.get('content', '')
                if price_content:
                    try:
                        current_price_numeric = int(price_content)
                    except:
                        pass
                else:
                    price_match = re.search(r'\$?([0-9.,]+)', current_price_text.replace('.', ''))
                    if price_match:
                        try:
                            current_price_numeric = int(price_match.group(1).replace(',', ''))
                        except:
                            pass
            
            # Precio original (tachado)
            original_price_elem = container.select_one('.price-item.list .value')
            if original_price_elem:
                original_price_text = original_price_elem.get_text(strip=True)
                price_content = original_price_elem.get('content', '')
                if price_content:
                    try:
                        original_price_numeric = int(price_content)
                    except:
                        pass
                else:
                    price_match = re.search(r'\$?([0-9.,]+)', original_price_text.replace('.', ''))
                    if price_match:
                        try:
                            original_price_numeric = int(price_match.group(1).replace(',', ''))
                        except:
                            pass
            
            # Descuento
            discount_elem = container.select_one('.discount-badge')
            if discount_elem:
                discount_percent = discount_elem.get_text(strip=True)
            
            # Rating y reviews
            rating = 0
            reviews_count = ""
            
            # Contar estrellas llenas
            star_elements = container.select('.yotpo-icon-star.rating-star')
            rating = len(star_elements)
            
            # Número de reviews
            reviews_elem = container.select_one('.yotpo-total-reviews')
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                reviews_match = re.search(r'\((\d+)\)', reviews_text)
                if reviews_match:
                    reviews_count = reviews_match.group(1)
            
            # Opciones de envío
            shipping_options = []
            shipping_elements = container.select('.shipping-method .method-description span:first-child')
            for shipping in shipping_elements:
                shipping_text = shipping.get_text(strip=True)
                if shipping_text:
                    shipping_options.append(shipping_text)
            
            # Verificar si está sin stock
            out_of_stock = bool(container.select_one('.outofstock'))
            
            # Extraer color del nombre del producto
            color = ""
            color_keywords = ['light blue', 'blue', 'azul', 'negro', 'black', 'white', 'blanco', 
                             'red', 'rojo', 'green', 'verde', 'gray', 'gris', 'gold', 'dorado', 
                             'silver', 'plateado', 'purple', 'morado', 'pink', 'rosa']
            product_name_lower = product_name.lower()
            for keyword in color_keywords:
                if keyword in product_name_lower:
                    color = keyword.title()
                    break
            
            # Solo agregar productos válidos
            if product_name and sku:
                product_data = {
                    'sku': sku,
                    'brand': brand,
                    'name': product_name,
                    'seller': seller,
                    'storage': storage,
                    'screen_size': screen_size,
                    'front_camera': front_camera,
                    'color': color,
                    'current_price_text': current_price_text,
                    'current_price': current_price_numeric,
                    'original_price_text': original_price_text,
                    'original_price': original_price_numeric,
                    'discount_percent': discount_percent,
                    'rating': rating,
                    'reviews_count': reviews_count,
                    'shipping_options': ', '.join(shipping_options),
                    'out_of_stock': out_of_stock,
                    'product_url': product_url,
                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                products.append(product_data)
                
                print(f"  [OK] SKU: {sku}")
                print(f"  [OK] Marca: {brand}")
                print(f"  [OK] Nombre: {product_name[:50]}...")
                print(f"  [OK] Vendedor: {seller}")
                print(f"  [OK] Precio Actual: {current_price_text}")
                print(f"  [OK] Precio Original: {original_price_text}")
                print(f"  [OK] Descuento: {discount_percent}")
                print(f"  [OK] Rating: {rating} estrellas ({reviews_count} reviews)")
                print(f"  [OK] Specs: {storage} | {screen_size} | {front_camera}")
                if color:
                    print(f"  [OK] Color: {color}")
                if shipping_options:
                    print(f"  [OK] Envíos: {', '.join(shipping_options[:2])}...")
                if out_of_stock:
                    print(f"  [OK] Sin Stock: Sí")
                
        except Exception as e:
            print(f"  [ERROR] procesando contenedor: {e}")
            continue
    
    return products

def scrape_hites_smartphones():
    """Función principal de scraping"""
    URL = "https://www.hites.com/celulares/smartphones/"
    
    print(f"=== SCRAPER HITES.COM - SMARTPHONES ===")
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
        with open("hites_smartphones_debug.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print("HTML guardado en hites_smartphones_debug.html")
        
        # Extraer productos
        products = extract_products(soup)
        
        print(f"\n=== RESULTADOS HITES ===")
        print(f"Total productos encontrados: {len(products)}")
        
        if products:
            # Guardar en Excel
            timestamp = int(time.time())
            filename = f"hites_smartphones_{timestamp}.xlsx"
            
            df = pd.DataFrame(products)
            df.to_excel(filename, index=False)
            
            print(f"Datos guardados en: {filename}")
            print(f"\n=== MUESTRA DE PRODUCTOS ===")
            
            for i, product in enumerate(products[:5], 1):
                current_display = f"${product['current_price']:,}" if product['current_price'] else "N/A"
                original_display = f" (antes: ${product['original_price']:,})" if product['original_price'] else ""
                stock_text = " [SIN STOCK]" if product['out_of_stock'] else ""
                
                print(f"{i}. {product['name']}{stock_text}")
                print(f"   Marca: {product['brand']}")
                print(f"   SKU: {product['sku']}")
                print(f"   Vendedor: {product['seller']}")
                print(f"   Precio: {current_display}{original_display}")
                print(f"   Descuento: {product['discount_percent']}")
                print(f"   Rating: {product['rating']} estrellas ({product['reviews_count']} reviews)")
                print(f"   Specs: {product['storage']} | {product['screen_size']} | {product['front_camera']}")
                if product['color']:
                    print(f"   Color: {product['color']}")
                if product['shipping_options']:
                    print(f"   Envíos: {product['shipping_options']}")
                print()
            
            # Estadísticas
            print(f"=== ESTADÍSTICAS HITES ===")
            brands = [p['brand'] for p in products if p['brand']]
            brand_counts = {}
            for brand in brands:
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            print(f"Productos por marca:")
            for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {brand}: {count} productos")
            
            # Vendedores
            sellers = [p['seller'] for p in products if p['seller']]
            seller_counts = {}
            for seller in sellers:
                seller_counts[seller] = seller_counts.get(seller, 0) + 1
            
            print(f"\nProductos por vendedor:")
            for seller, count in sorted(seller_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {seller}: {count} productos")
            
            # Stock
            out_of_stock_count = sum(1 for p in products if p['out_of_stock'])
            in_stock_count = len(products) - out_of_stock_count
            print(f"\nDisponibilidad:")
            print(f"  Con stock: {in_stock_count} productos")
            print(f"  Sin stock: {out_of_stock_count} productos")
            
            # Rangos de precio
            current_prices = [p['current_price'] for p in products if p['current_price']]
            if current_prices:
                print(f"\nRangos de precio actual:")
                print(f"  Mínimo: ${min(current_prices):,}")
                print(f"  Máximo: ${max(current_prices):,}")
                print(f"  Promedio: ${sum(current_prices)//len(current_prices):,}")
            
            # Rating promedio
            ratings = [p['rating'] for p in products if p['rating'] > 0]
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
        
        print("Scraping Hites completado")

if __name__ == "__main__":
    scrape_hites_smartphones()