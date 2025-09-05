# -*- coding: utf-8 -*-
"""
Diagnóstico Específico del Proxy Decodo
======================================

Test paso a paso para identificar el problema exacto:
1. Test de DNS resolution
2. Test de conectividad TCP 
3. Test de autenticación
4. Test con diferentes métodos HTTP
5. Comparación con herramientas externas
"""

import asyncio
import aiohttp
import socket
import requests
import time
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("proxy_diagnostic")

class ProxyDiagnostic:
    """Diagnóstico específico del proxy"""
    
    def __init__(self):
        # Configuración Decodo
        self.host = "cl.decodo.com"
        self.port = 30000
        self.username = "sprhxdrm60"
        self.password = "3IiejX9riaeNn+8u6E"
        self.proxy_url = f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        
        # URLs de test
        self.test_url = "http://httpbin.org/ip"  # HTTP simple
        self.test_url_https = "https://httpbin.org/ip"  # HTTPS
    
    def test_dns_resolution(self) -> Dict[str, Any]:
        """Test 1: Resolución DNS"""
        
        logger.info("1. Testing DNS resolution...")
        
        try:
            start_time = time.time()
            ip = socket.gethostbyname(self.host)
            duration_ms = (time.time() - start_time) * 1000
            
            result = {
                "success": True,
                "ip": ip,
                "duration_ms": duration_ms
            }
            logger.info(f"   DNS OK: {self.host} -> {ip} ({duration_ms:.1f}ms)")
            return result
            
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
            logger.error(f"   DNS FAIL: {e}")
            return result
    
    def test_tcp_connection(self) -> Dict[str, Any]:
        """Test 2: Conectividad TCP"""
        
        logger.info("2. Testing TCP connection...")
        
        try:
            start_time = time.time()
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # 10 segundos timeout
            
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            duration_ms = (time.time() - start_time) * 1000
            
            if result == 0:
                result_data = {
                    "success": True,
                    "duration_ms": duration_ms
                }
                logger.info(f"   TCP OK: {self.host}:{self.port} ({duration_ms:.1f}ms)")
            else:
                result_data = {
                    "success": False,
                    "error": f"Connection failed with code {result}",
                    "duration_ms": duration_ms
                }
                logger.error(f"   TCP FAIL: Connection failed with code {result}")
            
            return result_data
            
        except Exception as e:
            result_data = {
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
            logger.error(f"   TCP FAIL: {e}")
            return result_data
    
    def test_requests_library(self) -> Dict[str, Any]:
        """Test 3: Test con requests library"""
        
        logger.info("3. Testing with requests library...")
        
        try:
            start_time = time.time()
            
            proxies = {
                'http': self.proxy_url,
                'https': self.proxy_url
            }
            
            response = requests.get(
                self.test_url, 
                proxies=proxies, 
                timeout=10
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    "success": True,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "public_ip": data.get("origin"),
                    "response_size": len(response.content)
                }
                logger.info(f"   Requests OK: {response.status_code} ({duration_ms:.1f}ms) IP: {data.get('origin')}")
            else:
                result = {
                    "success": False,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "error": f"HTTP {response.status_code}"
                }
                logger.error(f"   Requests FAIL: HTTP {response.status_code}")
            
            return result
            
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
            logger.error(f"   Requests FAIL: {e}")
            return result
    
    async def test_aiohttp_methods(self) -> Dict[str, Any]:
        """Test 4: Diferentes métodos con aiohttp"""
        
        logger.info("4. Testing aiohttp methods...")
        
        results = {}
        
        # Método 1: Con proxy como parámetro
        logger.info("   4a. Testing proxy parameter...")
        try:
            start_time = time.time()
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.test_url,
                    proxy=self.proxy_url
                ) as response:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        results["proxy_parameter"] = {
                            "success": True,
                            "status_code": response.status,
                            "duration_ms": duration_ms,
                            "public_ip": data.get("origin")
                        }
                        logger.info(f"      Method 1 OK: {response.status} ({duration_ms:.1f}ms)")
                    else:
                        results["proxy_parameter"] = {
                            "success": False,
                            "status_code": response.status,
                            "duration_ms": duration_ms,
                            "error": f"HTTP {response.status}"
                        }
                        logger.error(f"      Method 1 FAIL: HTTP {response.status}")
                        
        except Exception as e:
            results["proxy_parameter"] = {
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
            logger.error(f"      Method 1 FAIL: {e}")
        
        # Método 2: Con BasicAuth separado
        logger.info("   4b. Testing separate auth...")
        try:
            start_time = time.time()
            
            proxy_auth = aiohttp.BasicAuth(self.username, self.password)
            proxy_simple = f"http://{self.host}:{self.port}"
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.test_url,
                    proxy=proxy_simple,
                    proxy_auth=proxy_auth
                ) as response:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        results["separate_auth"] = {
                            "success": True,
                            "status_code": response.status,
                            "duration_ms": duration_ms,
                            "public_ip": data.get("origin")
                        }
                        logger.info(f"      Method 2 OK: {response.status} ({duration_ms:.1f}ms)")
                    else:
                        results["separate_auth"] = {
                            "success": False,
                            "status_code": response.status,
                            "duration_ms": duration_ms,
                            "error": f"HTTP {response.status}"
                        }
                        logger.error(f"      Method 2 FAIL: HTTP {response.status}")
                        
        except Exception as e:
            results["separate_auth"] = {
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
            logger.error(f"      Method 2 FAIL: {e}")
        
        return results
    
    async def run_complete_diagnostic(self) -> Dict[str, Any]:
        """Ejecutar diagnóstico completo"""
        
        logger.info("DIAGNOSTICO COMPLETO PROXY DECODO")
        logger.info("=" * 50)
        logger.info(f"Host: {self.host}:{self.port}")
        logger.info(f"User: {self.username}")
        logger.info(f"Proxy URL: {self.proxy_url}")
        logger.info("")
        
        # Ejecutar todos los tests
        dns_result = self.test_dns_resolution()
        tcp_result = self.test_tcp_connection()
        requests_result = self.test_requests_library()
        aiohttp_results = await self.test_aiohttp_methods()
        
        # Compilar reporte
        report = {
            "timestamp": time.time(),
            "proxy_config": {
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "proxy_url": self.proxy_url
            },
            "tests": {
                "dns_resolution": dns_result,
                "tcp_connection": tcp_result,
                "requests_library": requests_result,
                "aiohttp_methods": aiohttp_results
            },
            "summary": self._generate_summary(dns_result, tcp_result, requests_result, aiohttp_results)
        }
        
        # Mostrar resumen
        self._show_summary(report)
        
        return report
    
    def _generate_summary(self, dns, tcp, requests_test, aiohttp) -> Dict[str, Any]:
        """Generar resumen diagnóstico"""
        
        # Contar éxitos
        dns_ok = dns["success"]
        tcp_ok = tcp["success"]
        requests_ok = requests_test["success"]
        aiohttp_ok = any(result["success"] for result in aiohttp.values())
        
        total_tests = 4
        passed_tests = sum([dns_ok, tcp_ok, requests_ok, aiohttp_ok])
        
        # Determinar diagnóstico
        if not dns_ok:
            diagnosis = "DNS_FAILURE"
            recommendation = "Verificar conexión a internet y DNS"
        elif not tcp_ok:
            diagnosis = "TCP_BLOCKED"
            recommendation = "Puerto 30000 bloqueado por firewall/antivirus"
        elif requests_ok and not aiohttp_ok:
            diagnosis = "AIOHTTP_ISSUE"
            recommendation = "Problema específico con aiohttp - usar requests"
        elif not requests_ok and not aiohttp_ok:
            diagnosis = "PROXY_AUTH_FAILURE"
            recommendation = "Verificar credenciales o configuración proxy"
        elif requests_ok or aiohttp_ok:
            diagnosis = "PARTIAL_SUCCESS"
            recommendation = "Al menos un método funciona - revisar implementación"
        else:
            diagnosis = "UNKNOWN_FAILURE"
            recommendation = "Error desconocido - contactar soporte"
        
        return {
            "tests_passed": passed_tests,
            "total_tests": total_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "diagnosis": diagnosis,
            "recommendation": recommendation,
            "working_methods": [method for method, result in aiohttp.items() if result.get("success")]
        }
    
    def _show_summary(self, report: Dict[str, Any]):
        """Mostrar resumen del diagnóstico"""
        
        logger.info("\n" + "="*50)
        logger.info("RESUMEN DIAGNÓSTICO")
        logger.info("="*50)
        
        summary = report["summary"]
        tests = report["tests"]
        
        # Estado por test
        logger.info("RESULTADOS POR TEST:")
        logger.info(f"  DNS Resolution: {'OK' if tests['dns_resolution']['success'] else 'FAIL'}")
        logger.info(f"  TCP Connection: {'OK' if tests['tcp_connection']['success'] else 'FAIL'}")
        logger.info(f"  Requests Library: {'OK' if tests['requests_library']['success'] else 'FAIL'}")
        logger.info(f"  Aiohttp Methods: {'OK' if any(r['success'] for r in tests['aiohttp_methods'].values()) else 'FAIL'}")
        
        # Resumen general
        logger.info(f"\nRESUMEN GENERAL:")
        logger.info(f"  Tests Passed: {summary['tests_passed']}/{summary['total_tests']}")
        logger.info(f"  Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"  Diagnosis: {summary['diagnosis']}")
        logger.info(f"  Recommendation: {summary['recommendation']}")
        
        if summary['working_methods']:
            logger.info(f"  Working Methods: {', '.join(summary['working_methods'])}")

async def main():
    """Ejecutar diagnóstico"""
    
    diagnostic = ProxyDiagnostic()
    report = await diagnostic.run_complete_diagnostic()
    
    # Guardar reporte
    import json
    from pathlib import Path
    
    output_dir = Path("proxy_reports")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"proxy_diagnostic_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nReporte guardado: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())