#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
💰 Price Manager - Sistema de Gestión de Precios Diarios e Históricos
======================================================================

Gestiona la lógica de precios con distinción clara entre precios
actuales (modificables durante el día) e históricos (inmutables).

Reglas de Negocio:
- 00:00 - 23:58: Precio del día actual (se actualiza si cambia)
- 23:59: Freeze period (no se actualiza, preparando histórico)
- 12:00: Cambio de día = nuevo registro en master_precios

Características:
- Detección automática de cambios de precio
- Cálculo de variaciones porcentuales
- Alertas de cambios significativos
- Histórico inmutable para análisis

Autor: Sistema Optimizado V5
Fecha: Diciembre 2024
"""

import logging
from datetime import datetime, date, timedelta, time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PriceStatus(Enum):
    """Estado del precio"""
    CURRENT = "current"      # Precio actual del día
    FROZEN = "frozen"        # Precio congelado (23:00-23:59)
    HISTORICAL = "historical" # Precio histórico (días pasados)


@dataclass
class PriceChange:
    """Representa un cambio de precio detectado"""
    sku: str
    fecha: date
    precio_anterior: int
    precio_nuevo: int
    tipo_precio: str  # 'normal', 'oferta', 'tarjeta'
    cambio_absoluto: int
    cambio_porcentaje: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def is_significant(self, threshold_percent: float = 5.0) -> bool:
        """Determina si el cambio es significativo"""
        return abs(self.cambio_porcentaje) >= threshold_percent


@dataclass
class PriceRecord:
    """Registro de precio completo"""
    sku: str
    fecha: date
    retailer: str
    precio_normal: int
    precio_oferta: int
    precio_tarjeta: int
    precio_min_dia: int
    status: PriceStatus
    timestamp_creacion: datetime
    timestamp_ultima_actualizacion: Optional[datetime] = None
    cambios_detectados: List[PriceChange] = field(default_factory=list)


class PriceManager:
    """💰 Gestor principal de precios con lógica diaria"""
    
    # Horarios de corte
    FREEZE_TIME = (23, 59)  # Freeze period: 23:59 (1 minuto antes del cambio)
    NEW_DAY_HOUR = 0  # Hora de cambio de día (00:00)
    
    def __init__(self, 
                 enable_alerts: bool = True,
                 alert_threshold: float = 5.0):
        """
        Inicializa el gestor de precios
        
        Args:
            enable_alerts: Habilitar alertas de cambios significativos
            alert_threshold: Umbral porcentual para alertas (default 5%)
        """
        self.enable_alerts = enable_alerts
        self.alert_threshold = alert_threshold
        
        # Cache de precios actuales para detección de cambios
        self.price_cache: Dict[str, PriceRecord] = {}
        
        # Estadísticas
        self.stats = {
            'prices_processed': 0,
            'changes_detected': 0,
            'significant_changes': 0,
            'alerts_triggered': 0
        }
        
        logger.info(f"💰 Price Manager inicializado (freeze: {self.FREEZE_TIME[0]}:{self.FREEZE_TIME[1]:02d})")
    
    def get_current_status(self) -> PriceStatus:
        """
        Obtiene el estado actual según la hora
        
        Returns:
            Estado actual del sistema de precios
        """
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        # Freeze period: exactamente 23:59
        if current_hour == self.FREEZE_TIME[0] and current_minute == self.FREEZE_TIME[1]:
            return PriceStatus.FROZEN
        else:
            return PriceStatus.CURRENT
    
    def should_update_price(self, fecha: date) -> bool:
        """
        Determina si se debe actualizar un precio
        
        Args:
            fecha: Fecha del precio a evaluar
            
        Returns:
            True si se debe actualizar, False si no
        """
        now = datetime.now()
        today = now.date()
        
        # Si es de un día pasado, nunca actualizar (histórico)
        if fecha < today:
            return False
        
        # Si es del futuro, no debería pasar pero no actualizar
        if fecha > today:
            logger.warning(f"⚠️ Fecha futura detectada: {fecha}")
            return False
        
        # Si es de hoy, verificar hora
        if fecha == today:
            status = self.get_current_status()
            return status == PriceStatus.CURRENT
        
        return False
    
    def get_price_record_date(self) -> date:
        """
        Obtiene la fecha correcta para el registro de precio
        
        Returns:
            Fecha para el registro (siempre fecha actual, cambio natural a 00:00)
        """
        now = datetime.now()
        
        # El cambio de día es natural a las 00:00
        return now.date()
    
    def detect_price_change(self,
                           sku: str,
                           fecha: date,
                           precio_actual: Dict[str, int],
                           precio_nuevo: Dict[str, int]) -> List[PriceChange]:
        """
        Detecta cambios entre precio actual y nuevo
        
        Args:
            sku: SKU del producto
            fecha: Fecha del precio
            precio_actual: Dict con precios actuales {normal, oferta, tarjeta}
            precio_nuevo: Dict con precios nuevos {normal, oferta, tarjeta}
            
        Returns:
            Lista de cambios detectados
        """
        changes = []
        
        for tipo in ['normal', 'oferta', 'tarjeta']:
            actual = precio_actual.get(tipo, 0)
            nuevo = precio_nuevo.get(tipo, 0)
            
            # Solo si ambos son válidos y diferentes
            if actual > 0 and nuevo > 0 and actual != nuevo:
                cambio_absoluto = nuevo - actual
                cambio_porcentaje = (cambio_absoluto / actual) * 100
                
                change = PriceChange(
                    sku=sku,
                    fecha=fecha,
                    precio_anterior=actual,
                    precio_nuevo=nuevo,
                    tipo_precio=tipo,
                    cambio_absoluto=cambio_absoluto,
                    cambio_porcentaje=cambio_porcentaje
                )
                
                changes.append(change)
                self.stats['changes_detected'] += 1
                
                # Verificar si es significativo
                if change.is_significant(self.alert_threshold):
                    self.stats['significant_changes'] += 1
                    
                    if self.enable_alerts:
                        self._trigger_alert(change)
        
        return changes
    
    def _trigger_alert(self, change: PriceChange):
        """
        Dispara alerta por cambio significativo
        
        Args:
            change: Cambio de precio detectado
        """
        emoji = "📈" if change.cambio_absoluto > 0 else "📉"
        
        alert_msg = (
            f"{emoji} ALERTA DE PRECIO: {change.sku}\n"
            f"Tipo: {change.tipo_precio}\n"
            f"Anterior: ${change.precio_anterior:,}\n"
            f"Nuevo: ${change.precio_nuevo:,}\n"
            f"Cambio: {change.cambio_porcentaje:+.1f}% (${change.cambio_absoluto:+,})"
        )
        
        logger.warning(alert_msg)
        self.stats['alerts_triggered'] += 1
        
        # Aquí se podría integrar con sistema de notificaciones
        # (Telegram, email, etc.)
    
    def create_price_record(self,
                           sku: str,
                           fecha: date,
                           retailer: str,
                           precios: Dict[str, int]) -> PriceRecord:
        """
        Crea un registro de precio completo
        
        Args:
            sku: SKU del producto
            fecha: Fecha del precio
            retailer: Nombre del retailer
            precios: Dict con precios {normal, oferta, tarjeta}
            
        Returns:
            Registro de precio creado
        """
        # Determinar estado
        now = datetime.now()
        today = now.date()
        
        if fecha < today:
            status = PriceStatus.HISTORICAL
        elif fecha == today:
            status = self.get_current_status()
        else:
            status = PriceStatus.CURRENT  # Futuro (raro)
        
        # Calcular precio mínimo
        precios_validos = [p for p in precios.values() if p > 0]
        precio_min = min(precios_validos) if precios_validos else 0
        
        record = PriceRecord(
            sku=sku,
            fecha=fecha,
            retailer=retailer,
            precio_normal=precios.get('normal', 0),
            precio_oferta=precios.get('oferta', 0),
            precio_tarjeta=precios.get('tarjeta', 0),
            precio_min_dia=precio_min,
            status=status,
            timestamp_creacion=now
        )
        
        self.stats['prices_processed'] += 1
        
        # Guardar en cache si es del día actual
        if fecha == today:
            cache_key = f"{sku}_{fecha}"
            self.price_cache[cache_key] = record
        
        return record
    
    def get_price_history(self, 
                         sku: str,
                         start_date: date,
                         end_date: date) -> List[PriceRecord]:
        """
        Obtiene histórico de precios (placeholder para futura implementación)
        
        Args:
            sku: SKU del producto
            start_date: Fecha inicio
            end_date: Fecha fin
            
        Returns:
            Lista de registros de precio
        """
        # TODO: Implementar consulta a DB
        logger.info(f"📊 Consultando histórico para {sku}: {start_date} a {end_date}")
        return []
    
    def calculate_price_metrics(self,
                               prices: List[PriceRecord]) -> Dict:
        """
        Calcula métricas sobre una lista de precios
        
        Args:
            prices: Lista de registros de precio
            
        Returns:
            Dict con métricas calculadas
        """
        if not prices:
            return {}
        
        # Extraer valores
        normales = [p.precio_normal for p in prices if p.precio_normal > 0]
        ofertas = [p.precio_oferta for p in prices if p.precio_oferta > 0]
        tarjetas = [p.precio_tarjeta for p in prices if p.precio_tarjeta > 0]
        minimos = [p.precio_min_dia for p in prices if p.precio_min_dia > 0]
        
        metrics = {
            'count': len(prices),
            'date_range': {
                'start': min(p.fecha for p in prices),
                'end': max(p.fecha for p in prices)
            }
        }
        
        # Calcular estadísticas por tipo
        for nombre, valores in [
            ('normal', normales),
            ('oferta', ofertas),
            ('tarjeta', tarjetas),
            ('minimo', minimos)
        ]:
            if valores:
                metrics[f'precio_{nombre}'] = {
                    'min': min(valores),
                    'max': max(valores),
                    'avg': sum(valores) / len(valores),
                    'last': valores[-1],
                    'variation': ((valores[-1] - valores[0]) / valores[0] * 100) if len(valores) > 1 and valores[0] > 0 else 0
                }
        
        return metrics
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del gestor
        
        Returns:
            Dict con estadísticas
        """
        stats = self.stats.copy()
        stats['cache_size'] = len(self.price_cache)
        stats['current_status'] = self.get_current_status().value
        
        # Calcular ratios
        if stats['prices_processed'] > 0:
            stats['change_rate'] = (stats['changes_detected'] / stats['prices_processed']) * 100
            stats['significant_change_rate'] = (stats['significant_changes'] / stats['prices_processed']) * 100
        else:
            stats['change_rate'] = 0
            stats['significant_change_rate'] = 0
        
        return stats
    
    def clear_cache(self):
        """Limpia el cache de precios"""
        self.price_cache.clear()
        logger.info("🧹 Cache de precios limpiado")


# Testing
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    print("=" * 70)
    print("💰 TESTING PRICE MANAGER")
    print("=" * 70)
    
    # Crear manager
    manager = PriceManager(enable_alerts=True, alert_threshold=5.0)
    
    # Test 1: Estado actual
    print("\n📅 Estado Actual:")
    status = manager.get_current_status()
    print(f"  Status: {status.value}")
    print(f"  Fecha para registro: {manager.get_price_record_date()}")
    print(f"  Debe actualizar hoy?: {manager.should_update_price(date.today())}")
    
    # Test 2: Detección de cambios
    print("\n🔍 Detección de Cambios:")
    
    sku = "FAL12345678"
    fecha = date.today()
    
    precio_actual = {
        'normal': 1000000,
        'oferta': 900000,
        'tarjeta': 850000
    }
    
    precio_nuevo = {
        'normal': 1000000,  # Sin cambio
        'oferta': 850000,   # -5.5% cambio significativo
        'tarjeta': 800000   # -5.9% cambio significativo
    }
    
    cambios = manager.detect_price_change(sku, fecha, precio_actual, precio_nuevo)
    
    for cambio in cambios:
        print(f"\n  Cambio detectado en precio {cambio.tipo_precio}:")
        print(f"    Anterior: ${cambio.precio_anterior:,}")
        print(f"    Nuevo: ${cambio.precio_nuevo:,}")
        print(f"    Variación: {cambio.cambio_porcentaje:+.1f}%")
        print(f"    Significativo: {'Sí' if cambio.is_significant() else 'No'}")
    
    # Test 3: Crear registros
    print("\n📝 Creación de Registros:")
    
    registros = []
    retailers = ['falabella', 'ripley', 'paris']
    
    for i, retailer in enumerate(retailers):
        precios = {
            'normal': 1000000 + (i * 50000),
            'oferta': 900000 + (i * 40000),
            'tarjeta': 850000 + (i * 30000)
        }
        
        record = manager.create_price_record(
            sku=f"{retailer[:3].upper()}{i:08d}",
            fecha=date.today(),
            retailer=retailer,
            precios=precios
        )
        
        registros.append(record)
        print(f"  {retailer}: SKU={record.sku}, Min=${record.precio_min_dia:,}")
    
    # Test 4: Métricas
    print("\n📊 Cálculo de Métricas:")
    
    # Simular histórico
    historico = []
    for i in range(7):
        fecha_hist = date.today() - timedelta(days=6-i)
        record = manager.create_price_record(
            sku="TEST001",
            fecha=fecha_hist,
            retailer="test",
            precios={
                'normal': 1000000 + (i * 10000),
                'oferta': 950000 + (i * 8000),
                'tarjeta': 900000 + (i * 7000)
            }
        )
        historico.append(record)
    
    metrics = manager.calculate_price_metrics(historico)
    
    print(f"  Período: {metrics['date_range']['start']} a {metrics['date_range']['end']}")
    print(f"  Registros: {metrics['count']}")
    
    for tipo in ['normal', 'oferta', 'tarjeta', 'minimo']:
        key = f'precio_{tipo}'
        if key in metrics:
            m = metrics[key]
            print(f"\n  Precio {tipo}:")
            print(f"    Min: ${m['min']:,}")
            print(f"    Max: ${m['max']:,}")
            print(f"    Promedio: ${m['avg']:,.0f}")
            print(f"    Último: ${m['last']:,}")
            print(f"    Variación: {m['variation']:+.1f}%")
    
    # Test 5: Estadísticas finales
    print("\n" + "=" * 70)
    print("📈 Estadísticas Finales:")
    stats = manager.get_stats()
    
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Testing completado")