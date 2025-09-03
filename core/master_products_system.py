# -*- coding: utf-8 -*-
"""
Master Products System
======================
Sistema de gestión del Master de Productos con TODOS los campos del scraping excepto precios.
Incluye generación de códigos internos amigables y gestión completa de metadata.

Arquitectura:
- Master de Productos: Todos los campos descriptivos/specs
- Master de Precios: Solo precios + referencias temporales  
- Código interno amigable: CL-[MARCA]-[MODELO]-[SPEC]-[RETAILER]-[SEQ]
"""

import hashlib
import re
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import pandas as pd
import duckdb
import json

logger = logging.getLogger(__name__)


@dataclass
class MasterProduct:
    """Estructura completa del Master de Productos con todos los campos del scraping"""
    
    # === IDENTIFICADORES ===
    codigo_interno: str = ""  # CL-SAMS-GAL-S24-128-RIP-001
    sku_hash: str = ""       # Hash del link como backup
    link: str = ""           # URL original (unique key real)
    
    # === INFORMACIÓN BÁSICA ===
    nombre: str = ""
    sku: str = ""            # SKU original del retailer
    marca: str = ""
    categoria: str = ""
    retailer: str = ""
    
    # === ESPECIFICACIONES TÉCNICAS ===
    # Smartphones/Tablets
    storage: str = ""        # "128GB", "256GB", "1TB"
    ram: str = ""           # "6GB", "8GB", "12GB"
    screen_size: str = ""   # "6.1", "6.7", "12.9"
    camera: str = ""        # "48MP", "108MP", "Triple 50MP+12MP+10MP"
    front_camera: str = ""  # "12MP", "32MP"
    internal_memory: str = ""
    network: str = ""       # "5G", "4G LTE"
    battery: str = ""       # "3279mAh", "4500mAh"
    processor: str = ""     # "A17 Pro", "Snapdragon 8 Gen 3"
    os: str = ""           # "iOS 17", "Android 14"
    
    # Laptops/Computadores
    cpu: str = ""          # "Intel Core i7", "Apple M3"
    gpu: str = ""          # "RTX 4060", "Integrated"
    display: str = ""      # "15.6 FHD", "13.3 Retina"
    connectivity: str = "" # "WiFi 6, Bluetooth 5.0"
    ports: str = ""        # "2xUSB-C, 1xUSB-A"
    
    # === VARIANTES Y PRESENTACIÓN ===
    color: str = ""        # "Negro", "Azul Pacífico", "Titanio Natural"
    colors: List[str] = field(default_factory=list)  # Todos los colores disponibles
    size: str = ""         # "S", "M", "L", "XL" para ropa/accesorios
    material: str = ""     # "Silicona", "Cuero", "Titanio"
    
    # === INFORMACIÓN COMERCIAL ===
    seller: str = ""           # Vendedor específico (MercadoLibre)
    is_sponsored: bool = False # Producto patrocinado
    is_promoted: bool = False  # Producto en promoción
    is_official_store: bool = False # Tienda oficial
    
    # === SOCIAL PROOF ===
    rating: float = 0.0       # 4.5, 3.8, etc.
    reviews_count: int = 0    # Número de reseñas
    badges: List[str] = field(default_factory=list)  # ["Más vendido", "Envío gratis"]
    emblems: List[str] = field(default_factory=list) # Emblemas específicos del retailer
    
    # === DISPONIBILIDAD Y ENVÍO ===
    out_of_stock: bool = False
    stock_quantity: int = 0   # Si está disponible
    shipping_options: List[str] = field(default_factory=list)  # ["Envío gratis", "Retiro en tienda"]
    delivery_time: str = ""   # "24-48 horas", "3-5 días hábiles"
    
    # === DESCUENTOS Y PROMOCIONES ===
    discount_percent: str = ""    # "15% OFF", "30% DCTO"
    discount_label: str = ""      # "Black Friday", "Cyber Monday"
    promotion_text: str = ""      # Texto promocional adicional
    installments: str = ""        # "12 cuotas sin interés"
    
    # === CAMPOS TÉCNICOS ADICIONALES ===
    model: str = ""              # Modelo específico
    part_number: str = ""        # Número de parte del fabricante
    warranty: str = ""           # "1 año", "2 años"
    included_accessories: List[str] = field(default_factory=list)  # Accesorios incluidos
    
    # === METADATOS DE GESTIÓN ===
    fecha_primera_captura: date = field(default_factory=date.today)
    fecha_ultima_actualizacion: date = field(default_factory=date.today)
    ultimo_visto: date = field(default_factory=date.today)
    activo: bool = True          # False si ya no se encuentra en scraping
    veces_visto: int = 1         # Contador de apariciones en scraping
    
    # === CAMPOS PROCESADOS ===
    nombre_normalizado: str = ""  # Nombre limpio para matching
    specs_hash: str = ""         # Hash de especificaciones para deduplicación
    categoria_inferida: str = "" # Categoría inferida por ML si falta
    marca_inferida: str = ""     # Marca inferida por ML si falta
    
    def __post_init__(self):
        """Procesamiento automático después de creación"""
        if not self.codigo_interno:
            self.codigo_interno = self._generate_codigo_interno()
        if not self.sku_hash:
            self.sku_hash = self._generate_sku_hash()
        if not self.nombre_normalizado:
            self.nombre_normalizado = self._normalize_nombre()
        if not self.specs_hash:
            self.specs_hash = self._generate_specs_hash()
    
    def _generate_codigo_interno(self) -> str:
        """Genera código interno amigable: CL-[MARCA]-[MODELO]-[SPEC]-[RETAILER]-[SEQ]"""
        try:
            # Limpiar y abreviar marca con mejor fallback
            if self.marca and not pd.isna(self.marca) and str(self.marca).strip():
                marca_clean = re.sub(r'[^A-Z0-9]', '', self.marca.upper())[:4]
            else:
                # Inferir marca del nombre si no existe
                marca_inferida = self._infer_brand_from_name()
                marca_clean = marca_inferida if marca_inferida else "UNK"
            
            # Extraer modelo del nombre
            modelo = self._extract_modelo()[:6]
            
            # Spec principal (storage, screen size, etc.) con mejor fallback
            spec = self._extract_main_spec()[:6]
            
            # Retailer abreviado con validación
            retailer_map = {
                'falabella': 'FAL', 'ripley': 'RIP', 'paris': 'PAR', 
                'mercadolibre': 'ML', 'hites': 'HIT', 'linio': 'LIN',
                'abcdin': 'ABC', 'lapolar': 'LP'
            }
            
            if self.retailer and not pd.isna(self.retailer) and str(self.retailer).strip():
                retailer_code = retailer_map.get(self.retailer.lower(), self.retailer.upper()[:3])
            else:
                # Inferir retailer del link si no existe
                retailer_code = self._infer_retailer_from_link()
            
            # Secuencial basado en hash del link (últimos 3 dígitos)
            link_str = str(self.link) if not pd.isna(self.link) and self.link is not None else ""
            if link_str:
                hash_int = int(hashlib.md5(link_str.encode()).hexdigest()[:8], 16)
                secuencial = f"{hash_int % 999 + 1:03d}"
            else:
                secuencial = "001"
            
            # Validar que ningún componente esté vacío
            components = [marca_clean, modelo, spec, retailer_code, secuencial]
            if any(not c or c == "" for c in components):
                logger.warning(f"Empty component in codigo_interno generation: {components}")
                # Usar fallback más robusto
                return self._generate_fallback_codigo()
            
            codigo = f"CL-{marca_clean}-{modelo}-{spec}-{retailer_code}-{secuencial}"
            
            # Validar longitud final (max 50 chars)
            if len(codigo) > 50:
                codigo = codigo[:50]
                logger.warning(f"Truncated long codigo_interno: {codigo}")
            
            return codigo
            
        except Exception as e:
            logger.warning(f"Error generating codigo_interno: {e}")
            return self._generate_fallback_codigo()
    
    def _infer_brand_from_name(self) -> str:
        """Inferir marca del nombre del producto"""
        if not self.nombre:
            return "UNK"
        
        # Marcas comunes para inferir
        brand_patterns = {
            'SAMSUNG': ['samsung', 'galaxy'],
            'APPL': ['apple', 'iphone', 'ipad', 'macbook', 'airpods'],
            'HUAW': ['huawei', 'mate', 'nova'],
            'XIAO': ['xiaomi', 'redmi', 'poco'],
            'OPPO': ['oppo', 'oneplus'],
            'MOTO': ['motorola', 'moto'],
            'LG': ['lg'],
            'SONY': ['sony', 'xperia'],
            'NOKI': ['nokia'],
            'HP': ['hp', 'hewlett'],
            'DELL': ['dell'],
            'LENO': ['lenovo', 'thinkpad'],
            'ACER': ['acer'],
            'ASUS': ['asus'],
            'MSI': ['msi']
        }
        
        nombre_lower = self.nombre.lower()
        for brand_code, keywords in brand_patterns.items():
            if any(keyword in nombre_lower for keyword in keywords):
                return brand_code
        
        return "UNK"
    
    def _infer_retailer_from_link(self) -> str:
        """Inferir retailer del link"""
        if not self.link:
            return "UNK"
        
        link_lower = self.link.lower()
        
        if 'falabella' in link_lower:
            return 'FAL'
        elif 'ripley' in link_lower:
            return 'RIP'
        elif 'paris' in link_lower:
            return 'PAR'
        elif 'mercadolibre' in link_lower or 'mercadolivre' in link_lower:
            return 'ML'
        elif 'hites' in link_lower:
            return 'HIT'
        elif 'linio' in link_lower:
            return 'LIN'
        elif 'abcdin' in link_lower:
            return 'ABC'
        elif 'lapolar' in link_lower:
            return 'LP'
        else:
            return 'UNK'
    
    def _generate_fallback_codigo(self) -> str:
        """Genera código fallback robusto cuando fallan los campos"""
        try:
            # Usar hash del link como base
            link_str = str(self.link) if not pd.isna(self.link) and self.link is not None else "unknown"
            link_hash = hashlib.md5(link_str.encode()).hexdigest()[:8].upper()
            
            # Intentar agregar retailer si está disponible
            retailer_suffix = ""
            if self.retailer:
                retailer_suffix = f"-{self.retailer.upper()[:3]}"
            
            # Código fallback con timestamp para garantizar unicidad
            timestamp_suffix = f"-{datetime.now().strftime('%m%d')}"  # MMDD
            
            return f"CL-{link_hash}{retailer_suffix}{timestamp_suffix}"
            
        except Exception:
            # Último recurso: timestamp + random
            import random
            return f"CL-FALLBACK-{datetime.now().strftime('%m%d%H%M')}-{random.randint(100, 999)}"
    
    def _extract_modelo(self) -> str:
        """Extrae modelo del nombre del producto"""
        nombre_upper = self.nombre.upper()
        
        # Patrones comunes de modelos
        patterns = [
            r'(IPHONE\s*\d+\s*PRO\s*MAX)', r'(IPHONE\s*\d+\s*PRO)', r'(IPHONE\s*\d+)',
            r'(GALAXY\s*S\d+\s*ULTRA)', r'(GALAXY\s*S\d+\s*PLUS)', r'(GALAXY\s*S\d+)',
            r'(MACBOOK\s*PRO)', r'(MACBOOK\s*AIR)', r'(IPAD\s*PRO)', r'(IPAD\s*AIR)',
            r'(\w+\s*\d+\s*PRO)', r'(\w+\s*\d+)', r'([A-Z]+\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, nombre_upper)
            if match:
                modelo = re.sub(r'[^A-Z0-9]', '', match.group(1))
                return modelo[:6]
        
        # Fallback: primeras palabras del nombre
        words = re.findall(r'[A-Z0-9]+', nombre_upper)
        return ''.join(words[:2])[:6] if words else "PROD"
    
    def _extract_main_spec(self) -> str:
        """Extrae especificación principal"""
        # Prioridad: storage > ram > screen_size > color
        if self.storage:
            return re.sub(r'[^A-Z0-9]', '', self.storage.upper())
        if self.ram:
            return re.sub(r'[^A-Z0-9]', '', self.ram.upper())
        if self.screen_size:
            return re.sub(r'[^A-Z0-9]', '', self.screen_size.upper()).replace('.', '')
        if self.color:
            return re.sub(r'[^A-Z0-9]', '', self.color.upper())[:4]
        
        return "STD"
    
    def _generate_sku_hash(self) -> str:
        """Genera hash del link como backup identifier"""
        link_str = str(self.link) if not pd.isna(self.link) and self.link is not None else "unknown"
        return hashlib.md5(link_str.encode()).hexdigest()[:16]
    
    def _normalize_nombre(self) -> str:
        """Normaliza nombre para matching"""
        # Remover caracteres especiales, normalizar espacios
        nombre_str = str(self.nombre) if not pd.isna(self.nombre) and self.nombre is not None else ""
        if not nombre_str:
            return ""
        nombre_clean = re.sub(r'[^\w\s]', ' ', nombre_str.lower())
        nombre_clean = re.sub(r'\s+', ' ', nombre_clean).strip()
        return nombre_clean
    
    def _generate_specs_hash(self) -> str:
        """Genera hash de especificaciones para deduplicación"""
        storage_str = str(self.storage) if not pd.isna(self.storage) and self.storage is not None else ""
        ram_str = str(self.ram) if not pd.isna(self.ram) and self.ram is not None else ""
        screen_str = str(self.screen_size) if not pd.isna(self.screen_size) and self.screen_size is not None else ""
        color_str = str(self.color) if not pd.isna(self.color) and self.color is not None else ""
        model_str = str(self.model) if not pd.isna(self.model) and self.model is not None else ""
        specs_str = f"{storage_str}|{ram_str}|{screen_str}|{color_str}|{model_str}"
        return hashlib.md5(specs_str.lower().encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para almacenamiento (solo campos definidos en schema)"""
        # Solo incluir campos que están en el schema de la tabla
        # Sanitizar valores None y float NaN antes de crear el diccionario
        def safe_str(value):
            """Convierte valores a string, manejando None y NaN"""
            if value is None or (hasattr(value, '__len__') and len(str(value)) == 0):
                return None
            if pd.isna(value):
                return None
            return str(value) if value != '' else None
        
        def safe_int(value):
            """Convierte valores a int, manejando None y NaN"""
            if value is None or pd.isna(value) or value == '' or value == 'null':
                return None
            try:
                return int(float(value)) if value != 0 else 0
            except (ValueError, TypeError):
                return None
        
        def safe_float(value):
            """Convierte valores a float, manejando None y NaN"""
            if value is None or pd.isna(value) or value == '' or value == 'null':
                return None
            try:
                return float(value) if value != 0 else 0.0
            except (ValueError, TypeError):
                return None
        
        def safe_date(value):
            """Convierte valores a date/datetime string"""
            if value is None:
                return None
            if isinstance(value, (date, datetime)):
                return value.isoformat() if hasattr(value, 'isoformat') else str(value)
            return None
        
        # Solo incluir columnas que existen en la tabla master_productos
        data = {
            # === IDENTIFICADORES ===
            'codigo_interno': safe_str(self.codigo_interno),
            'sku_hash': safe_str(self.sku_hash),
            'link': safe_str(self.link),
            
            # === INFORMACIÓN BÁSICA ===
            'nombre': safe_str(self.nombre),
            'sku': safe_str(self.sku),
            'marca': safe_str(self.marca),
            'categoria': safe_str(self.categoria),
            'retailer': safe_str(self.retailer),
            
            # === SPECS TÉCNICAS (solo las del esquema) ===
            'storage': safe_str(getattr(self, 'storage', None)),
            'ram': safe_str(getattr(self, 'ram', None)),
            'screen_size': safe_str(getattr(self, 'screen_size', None)),
            'camera': safe_str(getattr(self, 'camera', None)),
            'front_camera': safe_str(getattr(self, 'front_camera', None)),
            'color': safe_str(getattr(self, 'color', None)),
            'colors': str(getattr(self, 'colors', [])) if getattr(self, 'colors', None) else None,
            
            # === COMERCIAL (solo las del esquema) ===
            'rating': safe_float(getattr(self, 'rating', None)),
            'reviews_count': safe_int(getattr(self, 'reviews_count', None)),
            'badges': str(getattr(self, 'badges', [])) if getattr(self, 'badges', None) else None,
            'emblems': str(getattr(self, 'emblems', [])) if getattr(self, 'emblems', None) else None,
            'out_of_stock': bool(getattr(self, 'out_of_stock', False)),
            'discount_percent': safe_str(getattr(self, 'discount_percent', None)),
            'shipping_options': str(getattr(self, 'shipping_options', [])) if getattr(self, 'shipping_options', None) else None,
            'included_accessories': str(getattr(self, 'included_accessories', [])) if getattr(self, 'included_accessories', None) else None,
            
            # === METADATOS (solo las del esquema) ===
            'fecha_primera_captura': safe_date(self.fecha_primera_captura),
            'fecha_ultima_actualizacion': safe_date(self.fecha_ultima_actualizacion),
            'ultimo_visto': safe_date(self.ultimo_visto),
            'activo': self.activo,
            'veces_visto': safe_int(self.veces_visto),
            
            # === CAMPOS PROCESADOS ===
            'nombre_normalizado': safe_str(self.nombre_normalizado),
            'specs_hash': safe_str(self.specs_hash)
        }
        
        return data
    
    @classmethod
    def from_scraping_data(cls, scraping_data: Dict[str, Any]) -> 'MasterProduct':
        """Crea MasterProduct desde datos de scraping"""
        
        # Mapear todos los campos posibles del scraping
        product = cls(
            link=scraping_data.get('link', scraping_data.get('product_url', '')),
            nombre=scraping_data.get('nombre', scraping_data.get('name', '')),
            sku=str(scraping_data.get('sku', scraping_data.get('product_id', scraping_data.get('product_code', '')) or '')),
            marca=scraping_data.get('marca', scraping_data.get('brand', '')),
            categoria=scraping_data.get('categoria', scraping_data.get('category', '')),
            retailer=scraping_data.get('retailer', ''),
            
            # Especificaciones técnicas
            storage=scraping_data.get('storage', ''),
            ram=scraping_data.get('ram', ''),
            screen_size=scraping_data.get('screen_size', ''),
            camera=scraping_data.get('camera', scraping_data.get('camera_info', '')),
            front_camera=scraping_data.get('front_camera', ''),
            internal_memory=scraping_data.get('internal_memory', ''),
            network=scraping_data.get('network', ''),
            battery=scraping_data.get('battery', ''),
            processor=scraping_data.get('processor', ''),
            os=scraping_data.get('os', ''),
            
            # Laptop specs
            cpu=scraping_data.get('cpu', ''),
            gpu=scraping_data.get('gpu', ''),
            display=scraping_data.get('display', ''),
            connectivity=scraping_data.get('connectivity', ''),
            ports=scraping_data.get('ports', ''),
            
            # Variantes
            color=scraping_data.get('color', ''),
            colors=scraping_data.get('colors', []),
            size=scraping_data.get('size', ''),
            material=scraping_data.get('material', ''),
            
            # Información comercial
            seller=scraping_data.get('seller', ''),
            is_sponsored=scraping_data.get('is_sponsored', False),
            is_promoted=scraping_data.get('is_promoted', False),
            is_official_store=scraping_data.get('is_official_store', False),
            
            # Social proof
            rating=float(scraping_data.get('rating', 0) or 0),
            reviews_count=int(scraping_data.get('reviews_count', 0) or 0),
            badges=scraping_data.get('badges', []),
            emblems=scraping_data.get('emblems', []),
            
            # Disponibilidad
            out_of_stock=scraping_data.get('out_of_stock', False),
            stock_quantity=int(scraping_data.get('stock_quantity', 0) or 0),
            shipping_options=scraping_data.get('shipping_options', []),
            delivery_time=scraping_data.get('delivery_time', ''),
            
            # Descuentos
            discount_percent=scraping_data.get('discount_percent', ''),
            discount_label=scraping_data.get('discount_label', ''),
            promotion_text=scraping_data.get('promotion_text', ''),
            installments=scraping_data.get('installments', ''),
            
            # Técnicos adicionales
            model=scraping_data.get('model', ''),
            part_number=scraping_data.get('part_number', ''),
            warranty=scraping_data.get('warranty', ''),
            included_accessories=scraping_data.get('included_accessories', []),
        )
        
        return product


class MasterProductsManager:
    """Gestor del Master de Productos con storage en Parquet + DuckDB"""
    
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.parquet_path = self.base_path / "master" / "productos.parquet"
        self.duckdb_path = self.base_path / "warehouse_master.duckdb"
        
        # Asegurar directorios
        self.parquet_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Cache en memoria para productos activos
        self._products_cache: Dict[str, MasterProduct] = {}
        self._cache_loaded = False
    
    def _ensure_table_exists(self):
        """Asegurar que la tabla existe en DuckDB"""
        try:
            conn = duckdb.connect(str(self.duckdb_path))
            
            # Crear tabla master_productos con esquema limpio
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS master_productos (
                codigo_interno VARCHAR PRIMARY KEY,
                sku_hash VARCHAR,
                link VARCHAR UNIQUE,
                nombre VARCHAR,
                sku VARCHAR,
                marca VARCHAR,
                categoria VARCHAR,
                retailer VARCHAR,
                
                -- Specs técnicas básicas
                storage VARCHAR,
                ram VARCHAR,
                screen_size VARCHAR,
                camera VARCHAR,
                front_camera VARCHAR,
                color VARCHAR,
                colors VARCHAR,  -- JSON as string
                
                -- Comercial básico
                rating DOUBLE,
                reviews_count INTEGER,
                badges VARCHAR,  -- JSON as string
                emblems VARCHAR,  -- JSON as string
                out_of_stock BOOLEAN DEFAULT FALSE,
                discount_percent VARCHAR,
                shipping_options VARCHAR,  -- JSON as string
                included_accessories VARCHAR,  -- JSON as string
                
                -- Metadatos simples
                fecha_primera_captura DATE,
                fecha_ultima_actualizacion DATE,
                ultimo_visto DATE,
                activo BOOLEAN DEFAULT TRUE,
                veces_visto INTEGER DEFAULT 1,
                
                -- Procesados
                nombre_normalizado VARCHAR,
                specs_hash VARCHAR
            )
            """
            
            conn.execute(create_table_sql)
            
            # Índices optimizados
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_productos_link ON master_productos(link)",
                "CREATE INDEX IF NOT EXISTS idx_productos_categoria ON master_productos(categoria)",
                "CREATE INDEX IF NOT EXISTS idx_productos_retailer ON master_productos(retailer)",
                "CREATE INDEX IF NOT EXISTS idx_productos_marca ON master_productos(marca)",
                "CREATE INDEX IF NOT EXISTS idx_productos_activo ON master_productos(activo)",
                "CREATE INDEX IF NOT EXISTS idx_productos_ultimo_visto ON master_productos(ultimo_visto)"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Could not create index: {e}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error ensuring table exists: {e}")
    
    def _load_cache(self):
        """Cargar productos activos en cache"""
        if self._cache_loaded:
            return
        
        try:
            if self.parquet_path.exists():
                df = pd.read_parquet(self.parquet_path)
                
                for _, row in df.iterrows():
                    if row.get('activo', True):
                        product_dict = row.to_dict()
                        
                        # Convertir strings de fechas a date objects
                        for date_field in ['fecha_primera_captura', 'fecha_ultima_actualizacion', 'ultimo_visto']:
                            if date_field in product_dict and isinstance(product_dict[date_field], str):
                                try:
                                    product_dict[date_field] = datetime.fromisoformat(product_dict[date_field]).date()
                                except:
                                    product_dict[date_field] = date.today()
                        
                        # Convertir JSON strings a listas
                        for list_field in ['colors', 'badges', 'emblems', 'shipping_options', 'included_accessories']:
                            if list_field in product_dict and isinstance(product_dict[list_field], str):
                                try:
                                    product_dict[list_field] = json.loads(product_dict[list_field]) if product_dict[list_field] else []
                                except:
                                    product_dict[list_field] = []
                        
                        product = MasterProduct(**product_dict)
                        self._products_cache[product.link] = product
                
                logger.info(f"Loaded {len(self._products_cache)} products into cache")
            
            self._cache_loaded = True
            
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self._cache_loaded = True
    
    def get_product_by_link(self, link: str) -> Optional[MasterProduct]:
        """Obtener producto por link"""
        self._load_cache()
        return self._products_cache.get(link)
    
    def get_product_by_codigo(self, codigo_interno: str) -> Optional[MasterProduct]:
        """Obtener producto por código interno"""
        self._load_cache()
        for product in self._products_cache.values():
            if product.codigo_interno == codigo_interno:
                return product
        return None
    
    def upsert_product(self, scraping_data: Dict[str, Any]) -> Tuple[MasterProduct, bool]:
        """
        Insertar o actualizar producto desde datos de scraping
        
        Returns:
            (product, is_new): Producto y si es nuevo o actualizado
        """
        self._load_cache()
        
        link = scraping_data.get('link', scraping_data.get('product_url', ''))
        if not link:
            raise ValueError("Link is required for product upsert")
        
        existing_product = self.get_product_by_link(link)
        
        if existing_product:
            # Actualizar producto existente
            is_new = False
            existing_product.ultimo_visto = date.today()
            existing_product.veces_visto += 1
            
            # Actualizar campos que pueden cambiar
            existing_product.nombre = scraping_data.get('nombre', scraping_data.get('name', existing_product.nombre))
            existing_product.rating = float(scraping_data.get('rating', existing_product.rating) or existing_product.rating)
            existing_product.reviews_count = int(scraping_data.get('reviews_count', existing_product.reviews_count) or existing_product.reviews_count)
            existing_product.out_of_stock = scraping_data.get('out_of_stock', existing_product.out_of_stock)
            existing_product.discount_percent = scraping_data.get('discount_percent', existing_product.discount_percent)
            existing_product.badges = scraping_data.get('badges', existing_product.badges)
            existing_product.emblems = scraping_data.get('emblems', existing_product.emblems)
            existing_product.fecha_ultima_actualizacion = date.today()
            
            product = existing_product
            
        else:
            # Crear nuevo producto
            is_new = True
            product = MasterProduct.from_scraping_data(scraping_data)
            self._products_cache[link] = product
        
        return product, is_new
    
    def save_to_storage(self):
        """Guardar cache a Parquet y DuckDB"""
        try:
            if not self._products_cache:
                logger.info("No products to save")
                return
            
            # Preparar DataFrame
            products_data = []
            for product in self._products_cache.values():
                product_dict = product.to_dict()
                
                # Convertir listas a JSON strings para Parquet
                for list_field in ['colors', 'badges', 'emblems', 'shipping_options', 'included_accessories']:
                    if isinstance(product_dict[list_field], list):
                        product_dict[list_field] = json.dumps(product_dict[list_field])
                
                products_data.append(product_dict)
            
            df = pd.DataFrame(products_data)
            
            # Guardar a Parquet
            df.to_parquet(self.parquet_path, compression='snappy')
            logger.info(f"Saved {len(products_data)} products to Parquet")
            
            # Guardar a DuckDB
            self._ensure_table_exists()
            conn = duckdb.connect(str(self.duckdb_path))
            
            # Truncate y reload para simplicidad (en producción usar UPSERT)
            try:
                conn.register('df', df)
            except Exception:
                pass
            conn.execute("BEGIN")
            conn.execute("DELETE FROM master_productos WHERE codigo_interno IN (SELECT codigo_interno FROM df)")
            conn.execute("INSERT INTO master_productos SELECT * FROM df")
            conn.execute("COMMIT")
            
            conn.close()
            logger.info(f"Saved {len(products_data)} products to DuckDB (upsert)")
            
        except Exception as e:
            logger.error(f"Error saving products: {e}")
    
    def get_products_by_retailer(self, retailer: str) -> List[MasterProduct]:
        """Obtener productos por retailer"""
        self._load_cache()
        return [p for p in self._products_cache.values() if p.retailer == retailer and p.activo]
    
    def get_products_by_categoria(self, categoria: str) -> List[MasterProduct]:
        """Obtener productos por categoría"""  
        self._load_cache()
        return [p for p in self._products_cache.values() if p.categoria == categoria and p.activo]
    
    def mark_products_as_inactive(self, links_to_deactivate: List[str]):
        """Marcar productos como inactivos (ya no aparecen en scraping)"""
        self._load_cache()
        count = 0
        
        for link in links_to_deactivate:
            if link in self._products_cache:
                self._products_cache[link].activo = False
                count += 1
        
        if count > 0:
            logger.info(f"Marked {count} products as inactive")
            self.save_to_storage()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del master de productos"""
        self._load_cache()
        
        total_products = len(self._products_cache)
        active_products = sum(1 for p in self._products_cache.values() if p.activo)
        
        # Por retailer
        by_retailer = {}
        for product in self._products_cache.values():
            if product.activo:
                retailer = product.retailer
                if retailer not in by_retailer:
                    by_retailer[retailer] = 0
                by_retailer[retailer] += 1
        
        # Por categoría
        by_categoria = {}
        for product in self._products_cache.values():
            if product.activo:
                categoria = product.categoria
                if categoria not in by_categoria:
                    by_categoria[categoria] = 0
                by_categoria[categoria] += 1
        
        return {
            'total_products': total_products,
            'active_products': active_products,
            'inactive_products': total_products - active_products,
            'by_retailer': by_retailer,
            'by_categoria': by_categoria,
            'cache_loaded': self._cache_loaded,
            'parquet_exists': self.parquet_path.exists()
        }


# Función helper para integración
def process_scraping_batch(scraping_results: List[Dict[str, Any]], 
                         products_manager: MasterProductsManager) -> Dict[str, Any]:
    """Procesar lote de resultados de scraping en Master de Productos"""
    
    results = {
        'products_processed': 0,
        'products_new': 0,
        'products_updated': 0,
        'errors': []
    }
    
    for scraping_data in scraping_results:
        try:
            product, is_new = products_manager.upsert_product(scraping_data)
            
            results['products_processed'] += 1
            if is_new:
                results['products_new'] += 1
            else:
                results['products_updated'] += 1
                
        except Exception as e:
            logger.error(f"Error processing product {scraping_data.get('link', 'unknown')}: {e}")
            results['errors'].append(str(e))
    
    # Guardar cambios
    products_manager.save_to_storage()
    
    return results
