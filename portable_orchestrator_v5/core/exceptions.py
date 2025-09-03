#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚨 Scraper v5 Custom Exceptions - Sistema de Excepciones Personalizado
=====================================================================

Sistema robusto de excepciones personalizadas para manejo granular de errores
en el scraping. Incluye categorización de errores, auto-recovery y logging
inteligente con emojis para facilitar debugging.

Features:
- 🎯 Excepciones específicas por tipo de error
- 📊 Categorización automática de severidad
- 🔄 Sugerencias de recovery automático
- 📝 Logging contextual mejorado
- 🩺 Integración con sistema de diagnóstico

Author: Portable Orchestrator Team  
Version: 5.0.0
"""

import sys
import io
from typing import Dict, List, Optional, Any
from enum import Enum

# Forzar soporte UTF-8 y emojis
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class ErrorSeverity(Enum):
    """📊 Niveles de severidad de errores"""
    LOW = "low"           # Error menor, continuable
    MEDIUM = "medium"     # Error importante, requiere atención
    HIGH = "high"         # Error grave, afecta funcionalidad
    CRITICAL = "critical" # Error crítico, requiere intervención inmediata

class ErrorCategory(Enum):
    """📂 Categorías de errores"""
    NETWORK = "network"         # Problemas de red/conectividad
    PARSING = "parsing"         # Errores de parsing HTML/CSS
    TIMEOUT = "timeout"         # Timeouts diversos
    BLOCKED = "blocked"         # Bloqueos/detección de bot
    CONFIGURATION = "config"    # Errores de configuración
    RESOURCE = "resource"       # Problemas de recursos (memoria, CPU)
    DATA = "data"              # Problemas con datos/formato
    SYSTEM = "system"          # Errores de sistema general

class ScraperV5Exception(Exception):
    """
    🚨 Excepción base del sistema Scraper v5
    
    Clase base para todas las excepciones personalizadas del sistema.
    Incluye contexto adicional, severidad y sugerencias de recovery.
    """
    
    def __init__(self, 
                 message: str,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = ErrorCategory.SYSTEM,
                 context: Optional[Dict[str, Any]] = None,
                 recovery_suggestions: Optional[List[str]] = None,
                 original_exception: Optional[Exception] = None):
        """
        🚨 Inicializar excepción personalizada
        
        Args:
            message: Mensaje descriptivo del error
            severity: Nivel de severidad del error
            category: Categoría del error
            context: Contexto adicional (retailer, URL, etc.)
            recovery_suggestions: Lista de sugerencias para resolver el error
            original_exception: Excepción original si es wrapper
        """
        super().__init__(message)
        
        self.message = message
        self.severity = severity
        self.category = category
        self.context = context or {}
        self.recovery_suggestions = recovery_suggestions or []
        self.original_exception = original_exception
        
        # Emoji basado en severidad para logging
        self.emoji = {
            ErrorSeverity.LOW: "🟡",
            ErrorSeverity.MEDIUM: "🟠", 
            ErrorSeverity.HIGH: "🔴",
            ErrorSeverity.CRITICAL: "💀"
        }.get(severity, "⚠️")
    
    def __str__(self) -> str:
        """Representación string mejorada con emoji"""
        context_str = ""
        if self.context:
            context_items = [f"{k}={v}" for k, v in self.context.items()]
            context_str = f" [{', '.join(context_items)}]"
        
        return f"{self.emoji} {self.message}{context_str}"
    
    def get_detailed_info(self) -> Dict[str, Any]:
        """
        📊 Obtener información detallada de la excepción
        
        Returns:
            Dict con toda la información contextual
        """
        return {
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'context': self.context,
            'recovery_suggestions': self.recovery_suggestions,
            'has_original_exception': self.original_exception is not None,
            'emoji': self.emoji
        }
    
    def suggest_recovery(self) -> List[str]:
        """
        💡 Obtener sugerencias de recovery específicas
        
        Returns:
            Lista de sugerencias para resolver el error
        """
        base_suggestions = self.recovery_suggestions.copy()
        
        # Sugerencias automáticas basadas en categoría
        category_suggestions = {
            ErrorCategory.NETWORK: [
                "Verificar conexión a internet",
                "Revisar configuración de proxy",
                "Intentar con diferentes DNS"
            ],
            ErrorCategory.TIMEOUT: [
                "Aumentar timeout en configuración",
                "Verificar velocidad de conexión",
                "Reducir concurrencia"
            ],
            ErrorCategory.BLOCKED: [
                "Rotar user agents",
                "Cambiar proxy o IP",
                "Implementar delays más largos",
                "Revisar patrones de comportamiento bot-like"
            ],
            ErrorCategory.PARSING: [
                "Actualizar selectores CSS",
                "Verificar estructura HTML del sitio",
                "Revisar cambios en la página objetivo"
            ]
        }
        
        auto_suggestions = category_suggestions.get(self.category, [])
        return base_suggestions + auto_suggestions

# ==========================================
# EXCEPCIONES DE CONECTIVIDAD Y RED
# ==========================================

class NetworkException(ScraperV5Exception):
    """🌐 Excepción para problemas de red y conectividad"""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 status_code: Optional[int] = None, **kwargs):
        context = kwargs.get('context', {})
        if url:
            context['url'] = url
        if status_code:
            context['status_code'] = status_code
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.NETWORK,
            context=context,
            **kwargs
        )

class TimeoutException(ScraperV5Exception):
    """⏰ Excepción para timeouts diversos"""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None,
                 operation: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if timeout_seconds:
            context['timeout_seconds'] = timeout_seconds
        if operation:
            context['operation'] = operation
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.TIMEOUT,
            recovery_suggestions=[
                f"Aumentar timeout (actual: {timeout_seconds}s)" if timeout_seconds else "Aumentar timeout",
                "Verificar estabilidad de conexión",
                "Reducir complejidad de la operación"
            ],
            context=context,
            **kwargs
        )

class RetailerBlockedException(ScraperV5Exception):
    """🚫 Excepción cuando el retailer bloquea/detecta el bot"""
    
    def __init__(self, retailer: str, url: Optional[str] = None, 
                 detection_indicators: Optional[List[str]] = None, **kwargs):
        context = kwargs.get('context', {})
        context['retailer'] = retailer
        if url:
            context['blocked_url'] = url
        if detection_indicators:
            context['detection_indicators'] = detection_indicators
            
        message = f"Retailer '{retailer}' bloqueó el acceso"
        if detection_indicators:
            message += f". Indicadores: {', '.join(detection_indicators)}"
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.BLOCKED,
            recovery_suggestions=[
                "Cambiar user agent inmediatamente",
                "Rotar proxy o IP",
                "Implementar delays más largos entre requests",
                "Revisar patrones de navegación",
                "Considerar usar navegador real (no headless)"
            ],
            context=context,
            **kwargs
        )

class ProxyFailureException(ScraperV5Exception):
    """🌐 Excepción para fallos de proxy"""
    
    def __init__(self, proxy_url: str, failure_reason: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        context['proxy_url'] = proxy_url
        if failure_reason:
            context['failure_reason'] = failure_reason
            
        message = f"Proxy falló: {proxy_url}"
        if failure_reason:
            message += f" - {failure_reason}"
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.NETWORK,
            recovery_suggestions=[
                "Cambiar a proxy diferente",
                "Verificar credenciales del proxy",
                "Probar conexión directa sin proxy",
                "Revisar configuración de proxy"
            ],
            context=context,
            **kwargs
        )

# ==========================================
# EXCEPCIONES DE PARSING Y SELECTORES
# ==========================================

class SelectorNotFoundException(ScraperV5Exception):
    """🎯 Excepción cuando un selector CSS no encuentra elementos"""
    
    def __init__(self, selector: str, url: Optional[str] = None,
                 expected_elements: Optional[int] = None, **kwargs):
        context = kwargs.get('context', {})
        context['selector'] = selector
        if url:
            context['url'] = url
        if expected_elements:
            context['expected_elements'] = expected_elements
            
        message = f"Selector no encontró elementos: '{selector}'"
        if expected_elements:
            message += f" (esperados: {expected_elements})"
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.PARSING,
            recovery_suggestions=[
                "Verificar que el selector CSS sea correcto",
                "Revisar si la estructura HTML del sitio cambió",
                "Capturar screenshot de la página para análisis",
                "Probar selectores alternativos",
                "Verificar que la página cargó completamente"
            ],
            context=context,
            **kwargs
        )

class DataParsingException(ScraperV5Exception):
    """📊 Excepción para errores de parsing de datos"""
    
    def __init__(self, field_name: str, raw_data: Optional[str] = None,
                 expected_format: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        context['field_name'] = field_name
        if raw_data:
            context['raw_data'] = raw_data[:100]  # Truncar para logging
        if expected_format:
            context['expected_format'] = expected_format
            
        message = f"Error parseando campo '{field_name}'"
        if expected_format:
            message += f" (formato esperado: {expected_format})"
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.PARSING,
            recovery_suggestions=[
                "Revisar expresiones regulares de parsing",
                "Validar formato de datos en el sitio",
                "Implementar parsing alternativo",
                "Agregar validación de datos más robusta"
            ],
            context=context,
            **kwargs
        )

class CategoryEmptyException(ScraperV5Exception):
    """📂 Excepción cuando una categoría no tiene productos"""
    
    def __init__(self, category: str, retailer: Optional[str] = None,
                 url: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        context['category'] = category
        if retailer:
            context['retailer'] = retailer
        if url:
            context['category_url'] = url
            
        message = f"Categoría '{category}' sin productos"
        if retailer:
            message += f" en {retailer}"
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.LOW,  # Puede ser temporal
            category=ErrorCategory.DATA,
            recovery_suggestions=[
                "Verificar que la URL de categoría sea correcta",
                "Revisar si hay filtros aplicados que oculten productos",
                "Confirmar que la categoría existe en el sitio",
                "Probar en horarios diferentes (puede ser temporal)"
            ],
            context=context,
            **kwargs
        )

# ==========================================
# EXCEPCIONES DE CONFIGURACIÓN
# ==========================================

class ConfigurationException(ScraperV5Exception):
    """⚙️ Excepción para errores de configuración"""
    
    def __init__(self, config_key: str, config_value: Optional[Any] = None,
                 expected_type: Optional[type] = None, **kwargs):
        context = kwargs.get('context', {})
        context['config_key'] = config_key
        if config_value is not None:
            context['config_value'] = str(config_value)
        if expected_type:
            context['expected_type'] = expected_type.__name__
            
        message = f"Error en configuración: '{config_key}'"
        if expected_type and config_value is not None:
            message += f" (esperado: {expected_type.__name__}, actual: {type(config_value).__name__})"
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.CONFIGURATION,
            recovery_suggestions=[
                "Revisar archivo de configuración",
                "Validar formato y tipos de datos",
                "Consultar documentación de configuración",
                "Restaurar configuración por defecto si es necesario"
            ],
            context=context,
            **kwargs
        )

class RetailerNotConfiguredException(ScraperV5Exception):
    """🏪 Excepción cuando un retailer no está configurado"""
    
    def __init__(self, retailer: str, available_retailers: Optional[List[str]] = None, **kwargs):
        context = kwargs.get('context', {})
        context['retailer'] = retailer
        if available_retailers:
            context['available_retailers'] = available_retailers
            
        message = f"Retailer '{retailer}' no está configurado"
        if available_retailers:
            message += f". Disponibles: {', '.join(available_retailers)}"
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.CONFIGURATION,
            recovery_suggestions=[
                f"Agregar configuración para retailer '{retailer}'",
                "Verificar nombre del retailer (sensible a mayúsculas)",
                "Revisar lista de retailers disponibles",
                "Consultar documentación de configuración"
            ],
            context=context,
            **kwargs
        )

# ==========================================
# EXCEPCIONES DE RECURSOS
# ==========================================

class ResourceExhaustedException(ScraperV5Exception):
    """💾 Excepción cuando se agotan recursos (memoria, CPU, etc.)"""
    
    def __init__(self, resource_type: str, current_usage: Optional[float] = None,
                 limit: Optional[float] = None, **kwargs):
        context = kwargs.get('context', {})
        context['resource_type'] = resource_type
        if current_usage is not None:
            context['current_usage'] = current_usage
        if limit is not None:
            context['limit'] = limit
            
        message = f"Recurso agotado: {resource_type}"
        if current_usage is not None and limit is not None:
            message += f" ({current_usage:.1f}/{limit:.1f})"
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.RESOURCE,
            recovery_suggestions=[
                "Reducir número de tareas concurrentes",
                "Optimizar uso de memoria",
                "Implementar garbage collection manual",
                "Revisar memory leaks en el código",
                "Considerar aumentar límites de recursos"
            ],
            context=context,
            **kwargs
        )

class RateLimitExceededException(ScraperV5Exception):
    """🚦 Excepción cuando se excede rate limit"""
    
    def __init__(self, retailer: str, current_rate: Optional[float] = None,
                 limit: Optional[float] = None, retry_after: Optional[int] = None, **kwargs):
        context = kwargs.get('context', {})
        context['retailer'] = retailer
        if current_rate is not None:
            context['current_rate'] = current_rate
        if limit is not None:
            context['rate_limit'] = limit
        if retry_after is not None:
            context['retry_after_seconds'] = retry_after
            
        message = f"Rate limit excedido para {retailer}"
        if retry_after:
            message += f". Reintentar en {retry_after}s"
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.NETWORK,
            recovery_suggestions=[
                f"Esperar {retry_after} segundos antes de reintentar" if retry_after else "Implementar delay entre requests",
                "Reducir rate de requests",
                "Distribuir carga entre múltiples IPs/proxies",
                "Revisar configuración de rate limiting"
            ],
            context=context,
            **kwargs
        )

# ==========================================
# EXCEPCIONES DE SISTEMA Y ML
# ==========================================

class MLModelException(ScraperV5Exception):
    """🤖 Excepción para errores en modelos ML"""
    
    def __init__(self, model_name: str, operation: Optional[str] = None,
                 model_path: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        context['model_name'] = model_name
        if operation:
            context['operation'] = operation
        if model_path:
            context['model_path'] = model_path
            
        message = f"Error en modelo ML: {model_name}"
        if operation:
            message += f" durante operación: {operation}"
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            recovery_suggestions=[
                "Verificar que el modelo existe y está accesible",
                "Reentrenar modelo si está corrupto",
                "Usar modelo fallback si está disponible",
                "Revisar logs de entrenamiento del modelo"
            ],
            context=context,
            **kwargs
        )

class DatabaseException(ScraperV5Exception):
    """🗄️ Excepción para errores de base de datos"""
    
    def __init__(self, operation: str, table: Optional[str] = None,
                 db_error: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        context['operation'] = operation
        if table:
            context['table'] = table
        if db_error:
            context['db_error'] = db_error
            
        message = f"Error de base de datos en operación: {operation}"
        if table:
            message += f" (tabla: {table})"
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            recovery_suggestions=[
                "Verificar conexión a base de datos",
                "Revisar permisos de acceso",
                "Validar estructura de tabla",
                "Probar con operación más simple",
                "Revisar logs de base de datos"
            ],
            context=context,
            **kwargs
        )

# ==========================================
# FUNCIONES DE UTILIDAD
# ==========================================

def create_exception_from_error(error: Exception, 
                               context: Optional[Dict[str, Any]] = None) -> ScraperV5Exception:
    """
    🔄 Crear excepción personalizada a partir de error genérico
    
    Args:
        error: Excepción original
        context: Contexto adicional
        
    Returns:
        ScraperV5Exception: Excepción personalizada apropiada
    """
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # Mapeo inteligente de errores comunes
    if 'timeout' in error_str or 'timed out' in error_str:
        return TimeoutException(
            message=str(error),
            context=context,
            original_exception=error
        )
    elif 'connection' in error_str or 'network' in error_str:
        return NetworkException(
            message=str(error),
            context=context,
            original_exception=error
        )
    elif 'blocked' in error_str or '403' in error_str or 'forbidden' in error_str:
        retailer = context.get('retailer', 'unknown') if context else 'unknown'
        return RetailerBlockedException(
            retailer=retailer,
            detection_indicators=[error_str],
            context=context,
            original_exception=error
        )
    elif 'selector' in error_str or 'css' in error_str:
        return SelectorNotFoundException(
            selector=context.get('selector', 'unknown') if context else 'unknown',
            context=context,
            original_exception=error
        )
    else:
        # Excepción genérica con categorización automática
        category = ErrorCategory.SYSTEM
        if 'parse' in error_str:
            category = ErrorCategory.PARSING
        elif 'config' in error_str:
            category = ErrorCategory.CONFIGURATION
        
        return ScraperV5Exception(
            message=str(error),
            category=category,
            context=context,
            original_exception=error
        )

def log_exception(exception: ScraperV5Exception, 
                 logger_instance=None) -> None:
    """
    📝 Log excepción con formato mejorado
    
    Args:
        exception: Excepción a loggear
        logger_instance: Logger a usar (opcional)
    """
    import logging
    
    if logger_instance is None:
        logger_instance = logging.getLogger(__name__)
    
    # Determinar nivel de log basado en severidad
    log_level = {
        ErrorSeverity.LOW: logging.INFO,
        ErrorSeverity.MEDIUM: logging.WARNING,
        ErrorSeverity.HIGH: logging.ERROR,
        ErrorSeverity.CRITICAL: logging.CRITICAL
    }.get(exception.severity, logging.ERROR)
    
    # Log principal
    logger_instance.log(log_level, str(exception))
    
    # Log de contexto si existe
    if exception.context:
        context_items = [f"{k}={v}" for k, v in exception.context.items()]
        logger_instance.log(log_level, f"   📊 Contexto: {', '.join(context_items)}")
    
    # Log de sugerencias de recovery
    suggestions = exception.suggest_recovery()
    if suggestions:
        logger_instance.log(log_level, f"   💡 Sugerencias de recovery:")
        for suggestion in suggestions[:3]:  # Máximo 3 sugerencias
            logger_instance.log(log_level, f"      - {suggestion}")

# ==========================================
# DECORADOR PARA MANEJO AUTOMÁTICO DE ERRORES  
# ==========================================

def handle_scraper_exceptions(retailer: Optional[str] = None,
                             operation: Optional[str] = None):
    """
    🔄 Decorador para manejo automático de excepciones
    
    Args:
        retailer: Nombre del retailer (para contexto)
        operation: Nombre de la operación (para contexto)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ScraperV5Exception:
                # Re-raise excepciones propias
                raise
            except Exception as e:
                # Convertir a excepción personalizada
                context = {}
                if retailer:
                    context['retailer'] = retailer
                if operation:
                    context['operation'] = operation
                
                custom_exception = create_exception_from_error(e, context)
                log_exception(custom_exception)
                raise custom_exception
        
        return wrapper
    return decorator

# Ejemplo de uso del decorador:
# @handle_scraper_exceptions(retailer="ripley", operation="parse_products")
# def parse_products(html_content):
#     # Código que puede fallar
#     pass