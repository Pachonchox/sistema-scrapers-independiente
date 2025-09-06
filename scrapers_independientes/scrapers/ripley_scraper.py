#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ripley Scraper V5 - Integrado con el nuevo sistema de orquestación.
"""

import asyncio
import re
from typing import Optional, List, Dict, Any
from core.base_scraper import BaseScraperV5, ScrapingConfig, RetailerSelectors, ProductData, ScrapingResult

class RipleyScraper(BaseScraperV5):
    """
    Scraper para Ripley.cl, versión 5.
    """
    def __init__(self):
        config = ScrapingConfig(
            retailer="ripley",
            base_url="https://simple.ripley.cl",
            headless=True,
            selectors=self.get_selectors()
        )
        super().__init__(config)

    def get_selectors(self) -> RetailerSelectors:
        """
        Define los selectores CSS para Ripley.
        """
        return RetailerSelectors(
            product_cards=['a.catalog-product-item'],
            product_name=['div.catalog-product-details__name'],
            price_normal=['span.catalog-prices__list-price'],
            price_offer=['li.catalog-prices__offer-price'],
            price_card=['li.catalog-prices__card-price'],
            brand=['div.brand-logo > span'],
            sku=['div.catalog-product-item'], # Se obtiene del atributo 'data-partnumber'
            product_url=['a.catalog-product-item'], # Es el link principal
            image_url=['div.catalog-product-image-container img'],
        )

    async def _extract_product_from_card(self, card: Any, selectors: RetailerSelectors) -> Optional[ProductData]:
        """
        Extrae la información de un único producto desde su tarjeta.
        """
        try:
            title_element = await card.query_selector(selectors.product_name[0])
            title = await title_element.inner_text() if title_element else ''

            if not title:
                return None

            # Precios
            normal_price_elem = await card.query_selector(selectors.price_normal[0])
            normal_price_text = await normal_price_elem.inner_text() if normal_price_elem else '0'
            
            offer_price_elem = await card.query_selector(selectors.price_offer[0])
            offer_price_text = await offer_price_elem.inner_text() if offer_price_elem else '0'

            card_price_elem = await card.query_selector(selectors.price_card[0])
            card_price_text = await card_price_elem.inner_text() if card_price_elem else '0'

            # Limpieza de precios
            original_price = self._clean_price(normal_price_text)
            current_price = self._clean_price(offer_price_text)
            card_price = self._clean_price(card_price_text)

            # Si el precio de oferta es 0, usar el precio normal
            if current_price == 0 and original_price > 0:
                current_price = original_price
                original_price = 0 # No hay precio original si no hay oferta

            # Si el precio normal es 0 y el de oferta no, el de oferta es el normal
            if original_price == 0 and current_price > 0:
                original_price = current_price

            # Calcular descuento
            discount = 0
            if original_price > 0 and current_price > 0 and original_price > current_price:
                discount = round(((original_price - current_price) / original_price) * 100)

            # SKU
            sku = await card.get_attribute('data-partnumber') or ''

            # URL del producto
            product_url = await card.get_attribute('href') or ''
            if product_url and not product_url.startswith('http'):
                product_url = self.config.base_url + product_url

            # Imagen
            image_elem = await card.query_selector(selectors.image_url[0])
            image_url = await image_elem.get_attribute('src') if image_elem else ''

            # Marca
            brand_elem = await card.query_selector(selectors.brand[0])
            brand = await brand_elem.inner_text() if brand_elem else ''
            
            # Specs desde el título
            specs = self._extract_specs_from_title(title)

            product = ProductData(
                title=title.strip(),
                current_price=current_price,
                original_price=original_price,
                discount_percentage=discount,
                card_price=card_price,
                brand=brand.strip(),
                sku=sku.strip(),
                product_url=product_url,
                image_urls=[image_url],
                retailer=self.retailer,
                additional_info=specs
            )
            return product

        except Exception as e:
            self.logger.error(f"Error extrayendo producto: {e}")
            return None

    def _clean_price(self, price_str: str) -> float:
        """Limpia y convierte un string de precio a float."""
        if not price_str:
            return 0.0
        # Remueve 'Normal: ', '$', '.' y espacios
        cleaned_price = re.sub(r'[^\d]', '', price_str)
        try:
            return float(cleaned_price)
        except (ValueError, TypeError):
            return 0.0

    def _extract_specs_from_title(self, title: str) -> Dict[str, str]:
        """Extrae especificaciones como almacenamiento, RAM, etc., del título."""
        specs = {}
        title_lower = title.lower()

        # Almacenamiento (ej. 128GB, 1TB)
        storage_match = re.search(r'(\d+)\s*(gb|tb)', title_lower)
        if storage_match:
            specs['storage'] = f"{storage_match.group(1)}{storage_match.group(2).upper()}"

        # RAM (ej. 8GB RAM)
        ram_match = re.search(r'(\d+)\s*gb\s*ram', title_lower)
        if ram_match:
            specs['ram'] = f"{ram_match.group(1)}GB"

        # Tamaño de pantalla (ej. 6.7")
        screen_match = re.search(r'(\d[\.,]\d+)"', title)
        if not screen_match:
            screen_match = re.search(r'(\d+)"', title) # para pulgadas enteras
        if screen_match:
            specs['screen_size'] = f'{screen_match.group(1).replace(",", ".")}"'

        return specs

    async def scrape_category(self, category_url: str, max_products: Optional[int] = None) -> ScrapingResult:
        """
        Realiza el scraping de una categoría de productos en Ripley.
        """
        result = ScrapingResult(
            retailer=self.retailer,
            source_url=category_url,
            session_id=self.session_id
        )
        
        if not self.page:
            await self.initialize()

        try:
            await self._navigate_to_page(category_url)
            await self._intelligent_scroll(max_scrolls=5)

            # Extraer productos
            product_cards = await self._find_product_cards(self.get_selectors().product_cards)
            self.logger.info(f"Encontradas {len(product_cards)} tarjetas de producto.")

            tasks = []
            for i, card in enumerate(product_cards):
                if max_products and len(result.products) >= max_products:
                    self.logger.info(f"Alcanzado límite de {max_products} productos.")
                    break
                tasks.append(self._extract_product_from_card(card, self.get_selectors()))

            extracted_products = await asyncio.gather(*tasks)
            
            for product in extracted_products:
                if product:
                    result.products.append(product)

            result.total_found = len(result.products)
            result.success = result.total_found > 0

        except Exception as e:
            result.add_error(f"Error general en scrape_category: {e}")
            self.logger.error(f"Error en scrape_category para {category_url}: {e}")
            await self._capture_error_screenshot("scrape_category_error")
        
        return result

if __name__ == '__main__':
    # Ejemplo de uso
    async def main():
        scraper = RipleyScraper()
        await scraper.initialize()
        # URL de celulares en Ripley
        url = "https://simple.ripley.cl/tecno/celulares/ver-todo-celulares"
        result = await scraper.scrape_category(url, max_products=20)
        
        if result.success:
            print(f"Se encontraron {result.total_found} productos.")
            for i, product in enumerate(result.products[:5]):
                print(f"  {i+1}. {product.title} - {product.current_price} (SKU: {product.sku})")
        else:
            print("No se pudieron extraer productos.")
            if result.errors:
                print("Errores:", result.errors)

        await scraper.cleanup()

    asyncio.run(main())
