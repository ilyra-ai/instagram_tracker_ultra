"""
Tests Module - Testes de integração

Exporta:
- IntegrationTestRunner: Runner de testes
- run_full_test_suite: Executa suite completa
"""

from .integration_tests import IntegrationTestRunner, run_full_test_suite, EdgeCaseTests

__all__ = [
    'IntegrationTestRunner',
    'run_full_test_suite',
    'EdgeCaseTests'
]
