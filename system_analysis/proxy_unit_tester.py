# -*- coding: utf-8 -*-
"""
🧪 Test Unitarios para Proxy Decodo - 10 Canales Disponibles
===========================================================

Sistema de validación completa para proxy Decodo con 10 canales:
✅ Test de conectividad básica
✅ Test de cada canal individual  
✅ Test de velocidad por canal
✅ Test de IP pública por canal
✅ Selección automática del mejor canal
✅ Diagnóstico completo

CONFIGURACIÓN DECODO:
- Host: cl.decodo.com:30000
- User: sprhxdrm60  
- Pass: 3IiejX9riaeNn+8u6E
- Canales: 10 disponibles
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("proxy_tester")

@dataclass
class ProxyChannel:
    """Configuración de canal de proxy"""
    channel_id: int
    host: str = "cl.decodo.com"
    port: int = None
    username: str = "sprhxdrm60"
    password: str = "3IiejX9riaeNn+8u6E"
    
    def __post_init__(self):
        """Calcular puerto basado en channel_id"""
        if self.port is None:
            self.port = 30000 + self.channel_id  # 30001-30010
    
    @property
    def proxy_url(self) -> str:
        return f"http://{self.username}:{self.password}@{self.host}:{self.port}"

@dataclass
class ChannelTestResult:
    """Resultado de test por canal"""
    channel_id: int
    success: bool
    response_time_ms: float
    public_ip: Optional[str] = None
    error: Optional[str] = None
    test_url: Optional[str] = None
    status_code: Optional[int] = None
    
class ProxyUnitTester:
    """Tester unitario completo para proxy Decodo"""
    
    def __init__(self):
        # CONFIGURACIÓN DECODO - 10 CANALES
        self.channels = [ProxyChannel(i) for i in range(1, 11)]  # Canales 1-10
        
        # URLs de test
        self.test_urls = [
            "https://httpbin.org/ip",  # Para verificar IP
            "https://www.falabella.com/falabella-cl/",  # Test Falabella
            "https://simple.ripley.cl/",  # Test Ripley
            "https://www.google.com",  # Test básico
        ]
        
        # Configuración de test
        self.timeout_seconds = 30
        self.max_concurrent_tests = 5
        
        # Resultados
        self.test_results = {}
        self.best_channels = []
        
    async def test_direct_connection(self) -> Dict[str, Any]:
        """Test de conexión directa (sin proxy)"""
        
        logger.info("🔍 Testing conexión directa...")
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)) as session:
                async with session.get("https://httpbin.org/ip") as response:
                    if response.status == 200:
                        data = await response.json()
                        duration_ms = (time.time() - start_time) * 1000
                        
                        result = {
                            "success": True,
                            "response_time_ms": duration_ms,
                            "public_ip": data.get("origin"),
                            "status_code": response.status
                        }
                        
                        logger.info(f"✅ Conexión directa OK - {duration_ms:.1f}ms - IP: {result['public_ip']}")
                        return result
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            result = {
                "success": False,
                "response_time_ms": duration_ms,
                "error": str(e)
            }
            logger.error(f"❌ Conexión directa falló: {e}")
            
        return result
    
    async def test_single_channel(self, channel: ProxyChannel, test_url: str = None) -> ChannelTestResult:
        """Test individual de un canal de proxy"""
        
        if test_url is None:
            test_url = "https://httpbin.org/ip"
        
        start_time = time.time()
        
        try:
            # Configurar proxy para el canal
            proxy_auth = aiohttp.BasicAuth(channel.username, channel.password)
            connector = aiohttp.TCPConnector()
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                
                async with session.get(
                    test_url,
                    proxy=channel.proxy_url,
                    proxy_auth=proxy_auth
                ) as response:
                    
                    duration_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        # Extraer IP si es httpbin
                        public_ip = None
                        if "httpbin.org/ip" in test_url:
                            try:
                                data = await response.json()
                                public_ip = data.get("origin")
                            except:
                                pass
                        
                        return ChannelTestResult(
                            channel_id=channel.channel_id,
                            success=True,
                            response_time_ms=duration_ms,
                            public_ip=public_ip,
                            test_url=test_url,
                            status_code=response.status
                        )
                    else:
                        return ChannelTestResult(
                            channel_id=channel.channel_id,
                            success=False,
                            response_time_ms=duration_ms,
                            error=f"HTTP {response.status}",
                            test_url=test_url,
                            status_code=response.status
                        )
                        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ChannelTestResult(
                channel_id=channel.channel_id,
                success=False,
                response_time_ms=duration_ms,
                error=str(e),
                test_url=test_url
            )
    
    async def test_all_channels_basic(self) -> Dict[int, ChannelTestResult]:
        """Test básico de todos los 10 canales"""
        
        logger.info("🧪 Testing 10 canales Decodo...")
        
        # Crear semáforo para controlar concurrencia
        semaphore = asyncio.Semaphore(self.max_concurrent_tests)
        
        async def test_with_semaphore(channel):
            async with semaphore:
                return await self.test_single_channel(channel)
        
        # Ejecutar tests concurrentes
        tasks = [test_with_semaphore(channel) for channel in self.channels]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        channel_results = {}
        for i, result in enumerate(results):
            if isinstance(result, ChannelTestResult):
                channel_results[result.channel_id] = result
                status = "✅ OK" if result.success else "❌ FAIL"
                logger.info(f"Canal {result.channel_id}: {status} - {result.response_time_ms:.1f}ms")
            else:
                logger.error(f"Canal {i+1}: Error inesperado - {result}")
        
        return channel_results
    
    async def test_channels_with_retailers(self) -> Dict[str, Dict[int, ChannelTestResult]]:
        """Test de canales con URLs de retailers específicos"""
        
        logger.info("🏪 Testing canales con retailers...")
        
        retailer_results = {}
        
        for test_url in self.test_urls[1:]:  # Skip httpbin, ya lo probamos
            retailer_name = self._extract_retailer_name(test_url)
            logger.info(f"\n--- Testing {retailer_name} ---")
            
            # Test solo los primeros 3 canales para retailers (más rápido)
            semaphore = asyncio.Semaphore(3)
            
            async def test_retailer_channel(channel):
                async with semaphore:
                    return await self.test_single_channel(channel, test_url)
            
            tasks = [test_retailer_channel(channel) for channel in self.channels[:3]]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados por retailer
            channel_results = {}
            for result in results:
                if isinstance(result, ChannelTestResult):
                    channel_results[result.channel_id] = result
                    status = "✅ OK" if result.success else "❌ FAIL"
                    logger.info(f"  Canal {result.channel_id}: {status} - {result.response_time_ms:.1f}ms")
            
            retailer_results[retailer_name] = channel_results
        
        return retailer_results
    
    def _extract_retailer_name(self, url: str) -> str:
        """Extraer nombre del retailer de la URL"""
        if "falabella" in url:
            return "falabella"
        elif "ripley" in url:
            return "ripley"
        elif "google" in url:
            return "google"
        else:
            return url.split("//")[1].split("/")[0]
    
    async def find_best_channels(self, min_channels: int = 3) -> List[int]:
        """Encontrar los mejores canales basado en velocidad y éxito"""
        
        logger.info(f"🔍 Buscando {min_channels} mejores canales...")
        
        # Test básico de todos los canales
        basic_results = await self.test_all_channels_basic()
        
        # Filtrar solo exitosos
        successful_channels = [
            result for result in basic_results.values() 
            if result.success
        ]
        
        if len(successful_channels) == 0:
            logger.error("❌ Ningún canal funciona!")
            return []
        
        # Ordenar por velocidad (menor tiempo = mejor)
        successful_channels.sort(key=lambda x: x.response_time_ms)
        
        # Tomar los mejores
        best_channels = successful_channels[:min_channels]
        best_channel_ids = [ch.channel_id for ch in best_channels]
        
        logger.info("🏆 MEJORES CANALES:")
        for i, channel in enumerate(best_channels):
            logger.info(f"  #{i+1}: Canal {channel.channel_id} - {channel.response_time_ms:.1f}ms - IP: {channel.public_ip}")
        
        self.best_channels = best_channel_ids
        return best_channel_ids
    
    async def run_complete_diagnosis(self) -> Dict[str, Any]:
        """Ejecutar diagnóstico completo del sistema de proxy"""
        
        logger.info("🩺 DIAGNÓSTICO COMPLETO DE PROXY")
        logger.info("=" * 50)
        
        diagnosis_start = time.time()
        
        # 1. Test conexión directa
        logger.info("\n1️⃣ Conexión Directa:")
        direct_result = await self.test_direct_connection()
        
        # 2. Test básico de todos los canales
        logger.info("\n2️⃣ Test de 10 Canales Decodo:")
        basic_results = await self.test_all_channels_basic()
        
        # 3. Encontrar mejores canales
        logger.info("\n3️⃣ Selección de Mejores Canales:")
        best_channels = await self.find_best_channels()
        
        # 4. Test con retailers (opcional, solo si hay buenos canales)
        retailer_results = {}
        if len(best_channels) >= 2:
            logger.info("\n4️⃣ Test con Retailers:")
            retailer_results = await self.test_channels_with_retailers()
        
        # 5. Generar reporte final
        total_duration = time.time() - diagnosis_start
        
        report = {
            "diagnosis_date": datetime.now().isoformat(),
            "total_duration_seconds": total_duration,
            "direct_connection": direct_result,
            "proxy_channels": {
                "total_channels": len(self.channels),
                "working_channels": len([r for r in basic_results.values() if r.success]),
                "best_channels": best_channels,
                "channel_details": {ch_id: asdict(result) for ch_id, result in basic_results.items()}
            },
            "retailer_tests": retailer_results,
            "recommendations": self._generate_recommendations(direct_result, basic_results, best_channels),
            "configuration": {
                "proxy_host": self.channels[0].host,
                "proxy_port": self.channels[0].port,
                "username": self.channels[0].username,
                "total_channels_available": 10
            }
        }
        
        # Mostrar resumen
        self._show_diagnosis_summary(report)
        
        return report
    
    def _generate_recommendations(self, direct_result: Dict, basic_results: Dict, best_channels: List[int]) -> List[str]:
        """Generar recomendaciones basadas en resultados"""
        
        recommendations = []
        
        working_channels = len([r for r in basic_results.values() if r.success])
        
        if working_channels == 0:
            recommendations.append("❌ CRÍTICO: Ningún canal proxy funciona - Verificar credenciales")
            recommendations.append("🔧 Revisar configuración: cl.decodo.com:30000")
            
        elif working_channels < 3:
            recommendations.append(f"⚠️ Solo {working_channels} canales funcionan - Contactar soporte Decodo")
            
        elif working_channels >= 7:
            recommendations.append(f"✅ EXCELENTE: {working_channels}/10 canales operativos")
            recommendations.append("🚀 Sistema listo para producción con alta disponibilidad")
        
        if len(best_channels) >= 3:
            fastest_ms = min([r.response_time_ms for r in basic_results.values() if r.success])
            if fastest_ms < 1000:
                recommendations.append(f"⚡ Velocidad excelente: {fastest_ms:.1f}ms canal más rápido")
            elif fastest_ms < 3000:
                recommendations.append(f"✅ Velocidad buena: {fastest_ms:.1f}ms canal más rápido")
            else:
                recommendations.append(f"⚠️ Velocidad lenta: {fastest_ms:.1f}ms - Verificar red")
        
        # Comparación con directo
        if direct_result["success"] and len(best_channels) > 0:
            direct_speed = direct_result["response_time_ms"]
            proxy_speed = min([r.response_time_ms for r in basic_results.values() if r.success])
            overhead = ((proxy_speed - direct_speed) / direct_speed) * 100
            
            recommendations.append(f"📊 Overhead proxy: +{overhead:.1f}% vs directo")
        
        return recommendations
    
    def _show_diagnosis_summary(self, report: Dict[str, Any]):
        """Mostrar resumen del diagnóstico"""
        
        logger.info("\n" + "="*60)
        logger.info("📋 RESUMEN DEL DIAGNÓSTICO")
        logger.info("="*60)
        
        # Conexión directa
        direct = report["direct_connection"]
        direct_status = "✅ OK" if direct["success"] else "❌ FAIL"
        logger.info(f"🔗 Conexión Directa: {direct_status}")
        if direct["success"]:
            logger.info(f"   IP Pública: {direct.get('public_ip', 'N/A')}")
            logger.info(f"   Velocidad: {direct['response_time_ms']:.1f}ms")
        
        # Canales proxy
        proxy = report["proxy_channels"]
        logger.info(f"\n🔄 Proxy Decodo:")
        logger.info(f"   Canales Trabajando: {proxy['working_channels']}/10")
        logger.info(f"   Mejores Canales: {', '.join(map(str, proxy['best_channels']))}")
        
        # Velocidades
        if proxy['working_channels'] > 0:
            working_results = [r for r in proxy['channel_details'].values() if r['success']]
            speeds = [r['response_time_ms'] for r in working_results]
            logger.info(f"   Velocidad Promedio: {sum(speeds)/len(speeds):.1f}ms")
            logger.info(f"   Canal Más Rápido: {min(speeds):.1f}ms")
        
        # Recomendaciones
        logger.info(f"\n💡 RECOMENDACIONES:")
        for rec in report["recommendations"]:
            logger.info(f"   {rec}")
        
        logger.info(f"\n⏱️ Diagnóstico completado en {report['total_duration_seconds']:.1f}s")
    
    async def save_report(self, report: Dict[str, Any], filename: str = None) -> Path:
        """Guardar reporte de diagnóstico"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"proxy_diagnosis_{timestamp}.json"
        
        output_dir = Path("proxy_reports")
        output_dir.mkdir(exist_ok=True)
        
        file_path = output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Reporte guardado: {file_path}")
        return file_path

async def main():
    """Función principal - Diagnóstico completo"""
    
    print("PROXY UNIT TESTER - DECODO 10 CANALES")
    print("=" * 50)
    print("Configuración:")
    print("  Host: cl.decodo.com:30000")
    print("  User: sprhxdrm60")
    print("  Canales: 10 disponibles")
    print()
    
    # Inicializar tester
    tester = ProxyUnitTester()
    
    try:
        # Ejecutar diagnóstico completo
        report = await tester.run_complete_diagnosis()
        
        # Guardar reporte
        report_file = await tester.save_report(report)
        
        # Status final
        working_channels = report["proxy_channels"]["working_channels"]
        
        if working_channels >= 7:
            print(f"\nSISTEMA PROXY EXCELENTE")
            print(f"   {working_channels}/10 canales operativos")
            print(f"   Mejores: {', '.join(map(str, report['proxy_channels']['best_channels']))}")
            print(f"   Listo para producción")
        elif working_channels >= 3:
            print(f"\nSISTEMA PROXY FUNCIONAL")
            print(f"   {working_channels}/10 canales operativos") 
            print(f"   Suficiente para uso normal")
        else:
            print(f"\nPROBLEMAS CON PROXY")
            print(f"   Solo {working_channels}/10 canales funcionan")
            print(f"   Verificar configuración")
        
    except Exception as e:
        logger.error(f"❌ Error en diagnóstico: {e}")
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    # Ejecutar tests
    asyncio.run(main())