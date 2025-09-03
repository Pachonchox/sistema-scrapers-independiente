#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exportador Excel (Scraper v5 Project)
-------------------------------------
Convierte resultados de scrapers v5 a Excel con el contrato mínimo
compatible con el proyecto principal.

Columnas:
- nombre, marca, sku, categoria, retailer, link
- precio_normal_num, precio_oferta_num, precio_tarjeta_num
- rating, reviews_count, storage, ram, screen, fecha_archivo

Nombre del archivo: <retailer>_YYYY_MM_DD_HHMMSS.xlsx
Ubicación por defecto: ../data/excel/
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd


CONTRACT_COLUMNS = [
    'nombre', 'marca', 'sku', 'categoria', 'retailer', 'link',
    'precio_normal_num', 'precio_oferta_num', 'precio_tarjeta_num',
    'rating', 'reviews_count', 'storage', 'ram', 'screen', 'fecha_archivo'
]


def _to_int(x: Any) -> int:
    try:
        if x is None:
            return 0
        if isinstance(x, str):
            x = x.replace('.', '').replace(',', '')
        v = int(float(x))
        return v if v > 0 else 0
    except Exception:
        return 0


def _to_record(item: Any) -> Dict[str, Any]:
    # Objetos ProductData con método to_record
    if hasattr(item, 'to_record') and callable(getattr(item, 'to_record')):
        base = item.to_record()
    elif isinstance(item, dict):
        base = item.copy()
    else:
        return {}

    nombre = base.get('nombre') or base.get('title') or ''
    marca = base.get('marca') or base.get('brand') or ''
    sku = base.get('sku') or ''
    categoria = base.get('categoria') or base.get('category') or ''
    retailer = base.get('retailer') or ''
    link = base.get('link') or base.get('product_url') or ''

    pn = base.get('precio_normal')
    po = base.get('precio_oferta', base.get('precio_final'))
    pt = base.get('precio_tarjeta')

    record = {
        'nombre': nombre,
        'marca': marca,
        'sku': sku,
        'categoria': categoria,
        'retailer': retailer,
        'link': link,
        'precio_normal_num': _to_int(pn),
        'precio_oferta_num': _to_int(po),
        'precio_tarjeta_num': _to_int(pt),
        'rating': base.get('rating', 0) or 0,
        'reviews_count': base.get('reviews_count', 0) or 0,
        'storage': base.get('storage', ''),
        'ram': base.get('ram', ''),
        'screen': base.get('screen') or base.get('screen_size') or '',
        'fecha_archivo': datetime.now().date().isoformat(),
    }

    return record


def export_excel(products: Iterable[Any], retailer: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y_%m_%d_%H%M%S')
    out_path = out_dir / f"{retailer.lower()}_{ts}.xlsx"

    rows = [_to_record(p) for p in products]
    rows = [r for r in rows if r]
    df = pd.DataFrame.from_records(rows, columns=CONTRACT_COLUMNS)

    tmp = out_path.with_suffix('.tmp.xlsx')
    df.to_excel(tmp, index=False)
    if out_path.exists():
        out_path.unlink()
    tmp.rename(out_path)
    return out_path

