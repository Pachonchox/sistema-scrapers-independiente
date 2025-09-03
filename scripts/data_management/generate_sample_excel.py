#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Excel de Muestra - Simula output de scrapers v5
============================================================

Genera archivos Excel simulando el output real de los scrapers,
siguiendo el formato que esperaría el sistema master.
"""

import pandas as pd
from datetime import datetime
import os
from pathlib import Path

def generate_sample_data():
    """
    Generar datos de muestra similares a lo que generarían los scrapers reales
    """
    
    # Crear directorio data si no existe
    data_dir = Path("data/excel")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Datos de muestra para Ripley
    ripley_data = [
        {
            'nombre': 'Notebook HP Pavilion 15-eg3001la Intel Core i5 16GB RAM 512GB SSD',
            'precio_normal': 899990,
            'precio_oferta': 799990, 
            'precio_tarjeta': 749990,
            'marca': 'HP',
            'categoria': 'Informatica',
            'sku': 'MPM00000849944',
            'link': 'https://simple.ripley.cl/notebook-hp-pavilion-15-eg3001la',
            'rating': 4.3,
            'reviews_count': 127,
            'storage': '512GB',
            'ram': '16GB',
            'screen': '15.6"',
            'disponible': True,
            'retailer': 'ripley',
            'timestamp': datetime.now().isoformat()
        },
        {
            'nombre': 'MacBook Air M2 13" 256GB Space Gray',
            'precio_normal': 1299990,
            'precio_oferta': None,
            'precio_tarjeta': 1199990,
            'marca': 'Apple', 
            'categoria': 'Informatica',
            'sku': 'MPM00000850123',
            'link': 'https://simple.ripley.cl/macbook-air-m2-13-256gb-space-gray',
            'rating': 4.8,
            'reviews_count': 89,
            'storage': '256GB',
            'ram': '8GB',
            'screen': '13.3"',
            'disponible': True,
            'retailer': 'ripley',
            'timestamp': datetime.now().isoformat()
        },
        {
            'nombre': 'Notebook ASUS VivoBook S14 Intel Core i7 16GB RAM 1TB SSD',
            'precio_normal': 1099990,
            'precio_oferta': 999990,
            'precio_tarjeta': 949990,
            'marca': 'ASUS',
            'categoria': 'Informatica', 
            'sku': 'MPM00000850456',
            'link': 'https://simple.ripley.cl/notebook-asus-vivobook-s14',
            'rating': 4.5,
            'reviews_count': 203,
            'storage': '1TB',
            'ram': '16GB',
            'screen': '14"',
            'disponible': True,
            'retailer': 'ripley',
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    # Datos de muestra para Falabella
    falabella_data = [
        {
            'nombre': 'Notebook Lenovo IdeaPad 3 AMD Ryzen 5 8GB RAM 256GB SSD',
            'precio': 649990,
            'precio_descuento': 599990,
            'marca': 'Lenovo',
            'categoria': 'Tecnología',
            'sku': 'FAL123456789',
            'link': 'https://www.falabella.com/falabella-cl/product/lenovo-ideapad-3',
            'rating': 4.2,
            'reviews_count': 156,
            'storage': '256GB',
            'ram': '8GB',
            'screen': '15.6"',
            'disponible': True,
            'retailer': 'falabella',
            'timestamp': datetime.now().isoformat()
        },
        {
            'nombre': 'Samsung Galaxy Book3 Intel Core i5 16GB RAM 512GB SSD',
            'precio': 999990,
            'precio_descuento': None,
            'marca': 'Samsung',
            'categoria': 'Tecnología',
            'sku': 'FAL789123456', 
            'link': 'https://www.falabella.com/falabella-cl/product/samsung-galaxy-book3',
            'rating': 4.6,
            'reviews_count': 87,
            'storage': '512GB',
            'ram': '16GB',
            'screen': '15.6"',
            'disponible': True,
            'retailer': 'falabella',
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    # Generar archivos Excel con timestamp
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    
    # Excel para Ripley
    ripley_df = pd.DataFrame(ripley_data)
    ripley_file = data_dir / f"ripley_{timestamp}.xlsx"
    ripley_df.to_excel(ripley_file, index=False)
    print(f"Generado: {ripley_file}")
    
    # Excel para Falabella
    falabella_df = pd.DataFrame(falabella_data)
    falabella_file = data_dir / f"falabella_{timestamp}.xlsx"
    falabella_df.to_excel(falabella_file, index=False)
    print(f"Generado: {falabella_file}")
    
    return [ripley_file, falabella_file]

if __name__ == "__main__":
    print("Generando datos de muestra...")
    files = generate_sample_data()
    print(f"\n{len(files)} archivos Excel generados exitosamente")
    print("Ubicacion: data/excel/")