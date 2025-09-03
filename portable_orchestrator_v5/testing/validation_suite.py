#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Validation Suite (Placeholder)
------------------------------
Implementación mínima para evitar errores de import durante la fase
de integración del módulo v5. Se puede expandir con validaciones
formales más adelante.
"""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class ValidationResult:
    success: bool
    issues: List[str]
    metadata: Dict[str, Any]


class ValidationSuite:
    def __init__(self) -> None:
        self.checks = []

    def run_basic_checks(self, products: List[Dict[str, Any]]) -> ValidationResult:
        issues: List[str] = []
        if not products:
            issues.append('no_products_extracted')
        else:
            sample = products[0]
            for field in ('nombre', 'link', 'retailer'):
                if field not in sample:
                    issues.append(f'missing_field:{field}')
        return ValidationResult(success=len(issues) == 0, issues=issues, metadata={})

