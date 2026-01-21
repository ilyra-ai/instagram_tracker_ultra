"""
Integration Tests 2025 - Testes de Integração Automatizados
Versão God Mode Ultimate - Validação de Todos os Endpoints

Funcionalidades:
- Testes de cada endpoint com dados reais
- Documentação de rate limits observados
- Validação de tratamento de erros edge cases
- Relatório de saúde do sistema
"""

import asyncio
import aiohttp
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sys

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationTests")


# =============================================================================
# ENUMS E DATACLASSES
# =============================================================================

class TestStatus(Enum):
    """Status do teste"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class EndpointCategory(Enum):
    """Categorias de endpoints"""
    INSTAGRAM = "instagram"
    INTELLIGENCE = "intelligence"
    ANALYTICS = "analytics"
    OSINT = "osint"
    SYSTEM = "system"
    HISTORY = "history"


@dataclass
class TestResult:
    """Resultado de um teste"""
    test_name: str
    endpoint: str
    method: str
    status: TestStatus
    response_time_ms: int
    status_code: Optional[int]
    error_message: Optional[str]
    response_sample: Optional[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class EndpointInfo:
    """Informações de um endpoint"""
    path: str
    method: str
    category: EndpointCategory
    description: str
    requires_auth: bool = False
    rate_limit_observed: Optional[int] = None
    avg_response_time_ms: Optional[float] = None
    test_params: Optional[Dict] = None


@dataclass
class RateLimitObservation:
    """Observação de rate limit"""
    endpoint: str
    requests_before_limit: int
    limit_header: Optional[str]
    reset_time_seconds: Optional[int]
    timestamp: str


# =============================================================================
# ENDPOINT REGISTRY
# =============================================================================

class EndpointRegistry:
    """
    Registro de todos os endpoints da API.
    """
    
    ENDPOINTS: List[EndpointInfo] = [
        # Instagram Core
        EndpointInfo(
            path="/api/instagram/status",
            method="GET",
            category=EndpointCategory.SYSTEM,
            description="Status do sistema"
        ),
        EndpointInfo(
            path="/api/instagram/user/{username}",
            method="GET",
            category=EndpointCategory.INSTAGRAM,
            description="Informações do perfil"
        ),
        EndpointInfo(
            path="/api/instagram/posts/{username}",
            method="GET",
            category=EndpointCategory.INSTAGRAM,
            description="Posts do usuário"
        ),
        EndpointInfo(
            path="/api/instagram/following/{username}",
            method="GET",
            category=EndpointCategory.INSTAGRAM,
            description="Lista de seguidos"
        ),
        EndpointInfo(
            path="/api/instagram/start",
            method="POST",
            category=EndpointCategory.INSTAGRAM,
            description="Iniciar rastreamento"
        ),
        EndpointInfo(
            path="/api/instagram/stop",
            method="POST",
            category=EndpointCategory.INSTAGRAM,
            description="Parar rastreamento"
        ),
        
        # Intelligence
        EndpointInfo(
            path="/api/intelligence/sentiment/{username}",
            method="GET",
            category=EndpointCategory.INTELLIGENCE,
            description="Análise de sentimento"
        ),
        EndpointInfo(
            path="/api/intelligence/sentiment/text",
            method="POST",
            category=EndpointCategory.INTELLIGENCE,
            description="Sentimento de texto"
        ),
        EndpointInfo(
            path="/api/intelligence/prediction/{username}",
            method="GET",
            category=EndpointCategory.INTELLIGENCE,
            description="Predição comportamental"
        ),
        EndpointInfo(
            path="/api/intelligence/visual/{username}",
            method="GET",
            category=EndpointCategory.INTELLIGENCE,
            description="Análise visual"
        ),
        EndpointInfo(
            path="/api/intelligence/network-graph/{username}",
            method="GET",
            category=EndpointCategory.INTELLIGENCE,
            description="Grafo de rede"
        ),
        
        # Analytics
        EndpointInfo(
            path="/api/analytics/engagement-rate/{username}",
            method="GET",
            category=EndpointCategory.ANALYTICS,
            description="Taxa de engajamento"
        ),
        EndpointInfo(
            path="/api/analytics/best-time/{username}",
            method="GET",
            category=EndpointCategory.ANALYTICS,
            description="Melhor horário"
        ),
        EndpointInfo(
            path="/api/analytics/hashtags/{username}",
            method="GET",
            category=EndpointCategory.ANALYTICS,
            description="Análise de hashtags"
        ),
        EndpointInfo(
            path="/api/analytics/audience-quality/{username}",
            method="GET",
            category=EndpointCategory.ANALYTICS,
            description="Qualidade da audiência"
        ),
        EndpointInfo(
            path="/api/analytics/content-calendar/{username}",
            method="GET",
            category=EndpointCategory.ANALYTICS,
            description="Calendário de conteúdo"
        ),
        EndpointInfo(
            path="/api/analytics/mentions/{username}",
            method="GET",
            category=EndpointCategory.ANALYTICS,
            description="Análise de menções"
        ),
        EndpointInfo(
            path="/api/analytics/collaborations/{username}",
            method="GET",
            category=EndpointCategory.ANALYTICS,
            description="Colaborações"
        ),
        EndpointInfo(
            path="/api/analytics/compare",
            method="POST",
            category=EndpointCategory.ANALYTICS,
            description="Comparar perfis"
        ),
        
        # OSINT
        EndpointInfo(
            path="/api/osint/account-health/{username}",
            method="GET",
            category=EndpointCategory.OSINT,
            description="Saúde da conta"
        ),
        EndpointInfo(
            path="/api/osint/breach-check/{identifier}",
            method="GET",
            category=EndpointCategory.OSINT,
            description="Verificação de breach"
        ),
        EndpointInfo(
            path="/api/osint/cross-platform/{username}",
            method="GET",
            category=EndpointCategory.OSINT,
            description="Resolução cross-platform"
        ),
        
        # History
        EndpointInfo(
            path="/api/history/bio/{username}",
            method="GET",
            category=EndpointCategory.HISTORY,
            description="Histórico de bio"
        ),
        EndpointInfo(
            path="/api/history/profile-snapshots/{username}",
            method="GET",
            category=EndpointCategory.HISTORY,
            description="Snapshots do perfil"
        ),
        
        # System
        EndpointInfo(
            path="/api/system/graphql-health",
            method="GET",
            category=EndpointCategory.SYSTEM,
            description="Saúde do GraphQL"
        ),
        EndpointInfo(
            path="/api/tasks/status/{task_id}",
            method="GET",
            category=EndpointCategory.SYSTEM,
            description="Status de task"
        ),
        EndpointInfo(
            path="/api/tasks/list",
            method="GET",
            category=EndpointCategory.SYSTEM,
            description="Listar tasks"
        ),
        EndpointInfo(
            path="/api/tasks/stats",
            method="GET",
            category=EndpointCategory.SYSTEM,
            description="Estatísticas de tasks"
        ),
        
        # Reels e Stories
        EndpointInfo(
            path="/api/instagram/stories/{username}",
            method="GET",
            category=EndpointCategory.INSTAGRAM,
            description="Stories do usuário"
        ),
        EndpointInfo(
            path="/api/instagram/reels-analytics/{username}",
            method="GET",
            category=EndpointCategory.INSTAGRAM,
            description="Analytics de Reels"
        ),
    ]
    
    @classmethod
    def get_by_category(cls, category: EndpointCategory) -> List[EndpointInfo]:
        """Obtém endpoints por categoria"""
        return [e for e in cls.ENDPOINTS if e.category == category]
    
    @classmethod
    def get_all(cls) -> List[EndpointInfo]:
        """Obtém todos os endpoints"""
        return cls.ENDPOINTS


# =============================================================================
# TEST RUNNER
# =============================================================================

class IntegrationTestRunner:
    """
    Runner de testes de integração.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:5000",
        test_username: str = "instagram"  # Perfil público de teste
    ):
        self.base_url = base_url.rstrip("/")
        self.test_username = test_username
        self.results: List[TestResult] = []
        self.rate_limit_observations: List[RateLimitObservation] = []
        
        logger.info(f"🧪 Test Runner inicializado: {base_url}")
    
    async def test_endpoint(
        self,
        endpoint: EndpointInfo,
        session: aiohttp.ClientSession,
        params: Optional[Dict] = None
    ) -> TestResult:
        """
        Testa um endpoint individual.
        
        Args:
            endpoint: Informações do endpoint
            session: Sessão HTTP
            params: Parâmetros extras
            
        Returns:
            TestResult
        """
        # Substituir placeholders
        path = endpoint.path.replace("{username}", self.test_username)
        path = path.replace("{identifier}", "test@example.com")
        path = path.replace("{task_id}", "test-task-id")
        
        url = f"{self.base_url}{path}"
        
        test_name = f"test_{endpoint.category.value}_{path.replace('/', '_').strip('_')}"
        
        start_time = time.time()
        status = TestStatus.PENDING
        status_code = None
        error_message = None
        response_sample = None
        
        try:
            if endpoint.method == "GET":
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    status_code = response.status
                    response_time = int((time.time() - start_time) * 1000)
                    
                    if response.status < 400:
                        status = TestStatus.PASSED
                        try:
                            data = await response.json()
                            response_sample = json.dumps(data, ensure_ascii=False)[:200]
                        except:
                            response_sample = await response.text()
                            response_sample = response_sample[:200]
                    elif response.status == 429:
                        status = TestStatus.FAILED
                        error_message = "Rate limited (429)"
                        # Observar rate limit
                        retry_after = response.headers.get("Retry-After")
                        self.rate_limit_observations.append(RateLimitObservation(
                            endpoint=path,
                            requests_before_limit=0,
                            limit_header=retry_after,
                            reset_time_seconds=int(retry_after) if retry_after else None,
                            timestamp=datetime.now().isoformat()
                        ))
                    elif response.status == 404:
                        status = TestStatus.SKIPPED
                        error_message = "Endpoint não implementado"
                    else:
                        status = TestStatus.FAILED
                        error_message = f"HTTP {response.status}"
                        
            elif endpoint.method == "POST":
                body = params or {}
                async with session.post(url, json=body, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    status_code = response.status
                    response_time = int((time.time() - start_time) * 1000)
                    
                    if response.status < 400:
                        status = TestStatus.PASSED
                        try:
                            data = await response.json()
                            response_sample = json.dumps(data, ensure_ascii=False)[:200]
                        except:
                            response_sample = await response.text()[:200]
                    else:
                        status = TestStatus.FAILED
                        error_message = f"HTTP {response.status}"
                        
        except asyncio.TimeoutError:
            response_time = int((time.time() - start_time) * 1000)
            status = TestStatus.ERROR
            error_message = "Timeout (30s)"
            
        except aiohttp.ClientConnectorError as e:
            response_time = int((time.time() - start_time) * 1000)
            status = TestStatus.ERROR
            error_message = f"Conexão falhou: {str(e)[:50]}"
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            status = TestStatus.ERROR
            error_message = str(e)[:100]
        
        result = TestResult(
            test_name=test_name,
            endpoint=path,
            method=endpoint.method,
            status=status,
            response_time_ms=response_time,
            status_code=status_code,
            error_message=error_message,
            response_sample=response_sample
        )
        
        self.results.append(result)
        
        # Log resultado
        icon = "✅" if status == TestStatus.PASSED else "❌" if status == TestStatus.FAILED else "⚠️"
        logger.info(f"{icon} {endpoint.method} {path} - {status_code or 'N/A'} ({response_time}ms)")
        
        return result
    
    async def run_all_tests(self, categories: Optional[List[EndpointCategory]] = None) -> Dict[str, Any]:
        """
        Executa todos os testes.
        
        Args:
            categories: Categorias para testar (None = todas)
            
        Returns:
            Relatório de testes
        """
        logger.info("🚀 Iniciando testes de integração...")
        
        endpoints = EndpointRegistry.get_all()
        if categories:
            endpoints = [e for e in endpoints if e.category in categories]
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                await self.test_endpoint(endpoint, session)
                # Delay entre testes para não triggerar rate limit
                await asyncio.sleep(0.5)
        
        total_time = time.time() - start_time
        
        # Gerar relatório
        passed = len([r for r in self.results if r.status == TestStatus.PASSED])
        failed = len([r for r in self.results if r.status == TestStatus.FAILED])
        skipped = len([r for r in self.results if r.status == TestStatus.SKIPPED])
        errors = len([r for r in self.results if r.status == TestStatus.ERROR])
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'test_username': self.test_username,
            'total_tests': len(self.results),
            'total_time_seconds': round(total_time, 2),
            'summary': {
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'errors': errors,
                'pass_rate': round(passed / len(self.results) * 100, 1) if self.results else 0
            },
            'avg_response_time_ms': round(
                sum(r.response_time_ms for r in self.results) / len(self.results), 2
            ) if self.results else 0,
            'rate_limit_observations': [
                {
                    'endpoint': o.endpoint,
                    'limit_header': o.limit_header,
                    'reset_seconds': o.reset_time_seconds
                }
                for o in self.rate_limit_observations
            ],
            'results': [
                {
                    'test': r.test_name,
                    'endpoint': r.endpoint,
                    'method': r.method,
                    'status': r.status.value,
                    'response_time_ms': r.response_time_ms,
                    'status_code': r.status_code,
                    'error': r.error_message
                }
                for r in self.results
            ]
        }
        
        logger.info(f"✅ Testes concluídos: {passed}/{len(self.results)} passaram ({report['summary']['pass_rate']}%)")
        
        return report
    
    async def test_rate_limits(
        self,
        endpoint_path: str,
        max_requests: int = 50,
        delay_between: float = 0.1
    ) -> Dict[str, Any]:
        """
        Testa rate limits de um endpoint.
        
        Args:
            endpoint_path: Caminho do endpoint
            max_requests: Máximo de requests para testar
            delay_between: Delay entre requests (segundos)
            
        Returns:
            Resultado do teste de rate limit
        """
        logger.info(f"🔥 Testando rate limit: {endpoint_path}")
        
        path = endpoint_path.replace("{username}", self.test_username)
        url = f"{self.base_url}{path}"
        
        requests_made = 0
        status_codes = []
        rate_limited_at = None
        
        async with aiohttp.ClientSession() as session:
            for i in range(max_requests):
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        requests_made += 1
                        status_codes.append(response.status)
                        
                        if response.status == 429:
                            rate_limited_at = requests_made
                            retry_after = response.headers.get("Retry-After")
                            
                            self.rate_limit_observations.append(RateLimitObservation(
                                endpoint=path,
                                requests_before_limit=requests_made,
                                limit_header=retry_after,
                                reset_time_seconds=int(retry_after) if retry_after else None,
                                timestamp=datetime.now().isoformat()
                            ))
                            
                            logger.warning(f"⚠️ Rate limited após {requests_made} requests")
                            break
                            
                except Exception as e:
                    logger.error(f"Erro na request {i}: {e}")
                
                await asyncio.sleep(delay_between)
        
        return {
            'endpoint': endpoint_path,
            'requests_made': requests_made,
            'rate_limited_at': rate_limited_at,
            'status_codes_summary': {
                str(code): status_codes.count(code)
                for code in set(status_codes)
            }
        }


# =============================================================================
# TEST CASES ESPECÍFICOS
# =============================================================================

class EdgeCaseTests:
    """
    Testes de edge cases.
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results: List[TestResult] = []
    
    async def test_invalid_username(self, session: aiohttp.ClientSession) -> TestResult:
        """Testa username inválido"""
        url = f"{self.base_url}/api/instagram/user/____invalid____user____"
        
        start = time.time()
        try:
            async with session.get(url) as response:
                elapsed = int((time.time() - start) * 1000)
                
                # Deve retornar 404
                if response.status == 404:
                    status = TestStatus.PASSED
                    error = None
                else:
                    status = TestStatus.FAILED
                    error = f"Esperava 404, recebeu {response.status}"
                    
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            status = TestStatus.ERROR
            error = str(e)
        
        result = TestResult(
            test_name="test_invalid_username",
            endpoint="/api/instagram/user/invalid",
            method="GET",
            status=status,
            response_time_ms=elapsed,
            status_code=response.status if 'response' in dir() else None,
            error_message=error,
            response_sample=None
        )
        
        self.results.append(result)
        return result
    
    async def test_empty_body_post(self, session: aiohttp.ClientSession) -> TestResult:
        """Testa POST com body vazio"""
        url = f"{self.base_url}/api/intelligence/sentiment/text"
        
        start = time.time()
        try:
            async with session.post(url, json={}) as response:
                elapsed = int((time.time() - start) * 1000)
                
                # Deve retornar 400 Bad Request
                if response.status == 400:
                    status = TestStatus.PASSED
                    error = None
                elif response.status < 400:
                    status = TestStatus.FAILED
                    error = "Deveria rejeitar body vazio"
                else:
                    status = TestStatus.PASSED  # Qualquer erro é aceitável
                    error = None
                    
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            status = TestStatus.ERROR
            error = str(e)
        
        result = TestResult(
            test_name="test_empty_body_post",
            endpoint="/api/intelligence/sentiment/text",
            method="POST",
            status=status,
            response_time_ms=elapsed,
            status_code=response.status if 'response' in dir() else None,
            error_message=error,
            response_sample=None
        )
        
        self.results.append(result)
        return result
    
    async def test_special_characters_username(self, session: aiohttp.ClientSession) -> TestResult:
        """Testa username com caracteres especiais"""
        url = f"{self.base_url}/api/instagram/user/<script>alert(1)</script>"
        
        start = time.time()
        try:
            async with session.get(url) as response:
                elapsed = int((time.time() - start) * 1000)
                
                # Deve retornar 400 ou 404
                if response.status in [400, 404]:
                    status = TestStatus.PASSED
                    error = None
                else:
                    status = TestStatus.FAILED
                    error = f"Deveria rejeitar XSS, recebeu {response.status}"
                    
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            status = TestStatus.ERROR
            error = str(e)
        
        result = TestResult(
            test_name="test_special_characters_username",
            endpoint="/api/instagram/user/xss",
            method="GET",
            status=status,
            response_time_ms=elapsed,
            status_code=response.status if 'response' in dir() else None,
            error_message=error,
            response_sample=None
        )
        
        self.results.append(result)
        return result
    
    async def run_all(self) -> List[TestResult]:
        """Executa todos os testes de edge case"""
        logger.info("🔬 Executando testes de edge cases...")
        
        async with aiohttp.ClientSession() as session:
            await self.test_invalid_username(session)
            await self.test_empty_body_post(session)
            await self.test_special_characters_username(session)
        
        return self.results


# =============================================================================
# REPORT GENERATOR
# =============================================================================

class TestReportGenerator:
    """
    Gerador de relatórios de teste.
    """
    
    @staticmethod
    def generate_markdown_report(
        integration_results: Dict[str, Any],
        edge_case_results: List[TestResult]
    ) -> str:
        """
        Gera relatório em Markdown.
        
        Args:
            integration_results: Resultados dos testes de integração
            edge_case_results: Resultados dos testes de edge case
            
        Returns:
            Relatório em Markdown
        """
        lines = [
            "# Relatório de Testes de Integração",
            "",
            f"**Data:** {integration_results['timestamp']}",
            f"**Base URL:** {integration_results['base_url']}",
            f"**Tempo Total:** {integration_results['total_time_seconds']}s",
            "",
            "## Resumo",
            "",
            "| Métrica | Valor |",
            "|---------|-------|",
            f"| Total de Testes | {integration_results['total_tests']} |",
            f"| Passaram | {integration_results['summary']['passed']} |",
            f"| Falharam | {integration_results['summary']['failed']} |",
            f"| Erros | {integration_results['summary']['errors']} |",
            f"| Taxa de Sucesso | {integration_results['summary']['pass_rate']}% |",
            f"| Tempo Médio de Resposta | {integration_results['avg_response_time_ms']}ms |",
            "",
            "## Resultados por Endpoint",
            "",
            "| Endpoint | Método | Status | Tempo (ms) | HTTP Code |",
            "|----------|--------|--------|------------|-----------|"
        ]
        
        for result in integration_results['results']:
            status_icon = "✅" if result['status'] == 'passed' else "❌" if result['status'] == 'failed' else "⚠️"
            lines.append(
                f"| {result['endpoint']} | {result['method']} | {status_icon} | {result['response_time_ms']} | {result['status_code'] or 'N/A'} |"
            )
        
        lines.extend([
            "",
            "## Rate Limits Observados",
            ""
        ])
        
        if integration_results['rate_limit_observations']:
            lines.append("| Endpoint | Limite | Reset |")
            lines.append("|----------|--------|-------|")
            for obs in integration_results['rate_limit_observations']:
                lines.append(f"| {obs['endpoint']} | {obs['limit_header'] or 'N/A'} | {obs['reset_seconds'] or 'N/A'}s |")
        else:
            lines.append("*Nenhum rate limit observado durante os testes.*")
        
        lines.extend([
            "",
            "## Testes de Edge Cases",
            "",
            "| Teste | Status | Tempo (ms) |",
            "|-------|--------|------------|"
        ])
        
        for result in edge_case_results:
            status_icon = "✅" if result.status == TestStatus.PASSED else "❌"
            lines.append(f"| {result.test_name} | {status_icon} | {result.response_time_ms} |")
        
        return "\n".join(lines)
    
    @staticmethod
    def save_report(report: str, path: str = "test_report.md") -> None:
        """Salva relatório em arquivo"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"📄 Relatório salvo: {path}")


# =============================================================================
# MAIN
# =============================================================================

async def run_full_test_suite(base_url: str = "http://localhost:5000") -> Dict[str, Any]:
    """
    Executa suite completa de testes.
    
    Args:
        base_url: URL base da API
        
    Returns:
        Resultados completos
    """
    print("=" * 60)
    print("   Integration Tests 2025 - God Mode Ultimate")
    print("   Validação de Todos os Endpoints")
    print("=" * 60)
    
    # Testes de integração
    runner = IntegrationTestRunner(base_url)
    integration_results = await runner.run_all_tests()
    
    # Testes de edge cases
    edge_tester = EdgeCaseTests(base_url)
    edge_results = await edge_tester.run_all()
    
    # Gerar relatório
    report = TestReportGenerator.generate_markdown_report(integration_results, edge_results)
    TestReportGenerator.save_report(report)
    
    print("\n" + "=" * 60)
    print("   RESUMO FINAL")
    print("=" * 60)
    print(f"   ✅ Passaram: {integration_results['summary']['passed']}")
    print(f"   ❌ Falharam: {integration_results['summary']['failed']}")
    print(f"   ⚠️ Erros: {integration_results['summary']['errors']}")
    print(f"   📊 Taxa de Sucesso: {integration_results['summary']['pass_rate']}%")
    print("=" * 60)
    
    return {
        'integration': integration_results,
        'edge_cases': [
            {
                'test': r.test_name,
                'status': r.status.value,
                'error': r.error_message
            }
            for r in edge_results
        ]
    }


if __name__ == "__main__":
    # Verificar se servidor está rodando
    import argparse
    
    parser = argparse.ArgumentParser(description="Integration Tests")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL da API")
    parser.add_argument("--username", default="instagram", help="Username de teste")
    args = parser.parse_args()
    
    print(f"\n🌐 Testando API em: {args.url}")
    print(f"👤 Username de teste: {args.username}\n")
    
    asyncio.run(run_full_test_suite(args.url))
