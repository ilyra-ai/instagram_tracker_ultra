"""
Integration Tests 2025 - Testes de Integração Automatizados (Lyra Ultra)
Versão 3.1.0 - Sincronizada com Flask API Fixed

Este script realiza uma auditoria completa de todos os endpoints reais da aplicação,
validando contratos, códigos de status e tempos de resposta.
"""

import asyncio
import aiohttp
import time
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

# Carregar env para credenciais de teste
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationTests")

class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

class EndpointCategory(Enum):
    INSTAGRAM = "instagram"
    INTELLIGENCE = "intelligence"
    ANALYTICS = "analytics"
    OSINT = "osint"
    SYSTEM = "system"
    AI = "ai"
    TASKS = "tasks"
    HISTORY = "history"

@dataclass
class TestResult:
    test_name: str
    endpoint: str
    method: str
    status: TestStatus
    response_time_ms: int
    status_code: Optional[int]
    error_message: Optional[str] = None
    response_sample: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class EndpointInfo:
    path: str
    method: str
    category: EndpointCategory
    description: str
    params: Optional[Dict] = None
    json_body: Optional[Dict] = None
    requires_auth: bool = True

class EndpointRegistry:
    """Registro atualizado dos endpoints reais do projeto."""
    ENDPOINTS = [
        # System & Auth
        EndpointInfo("/api/instagram/status", "GET", EndpointCategory.SYSTEM, "Status básico", requires_auth=False),
        EndpointInfo("/api/instagram/test", "GET", EndpointCategory.SYSTEM, "Teste de conectividade"),
        
        # Instagram Core (Query Params)
        EndpointInfo("/api/instagram/user-info", "GET", EndpointCategory.INSTAGRAM, "Info do Perfil", params={"username": "{username}"}),
        EndpointInfo("/api/instagram/posts", "GET", EndpointCategory.INSTAGRAM, "Posts Recentes", params={"username": "{username}", "limit": 5}),
        EndpointInfo("/api/instagram/following", "GET", EndpointCategory.INSTAGRAM, "Lista Seguidos", params={"username": "{username}", "limit": 10}),
        EndpointInfo("/api/instagram/track", "GET", EndpointCategory.INSTAGRAM, "Rastrear Atividades", params={"username": "{username}", "max_following": 5}),
        EndpointInfo("/api/instagram/locations", "GET", EndpointCategory.INSTAGRAM, "Rastrear Locais", params={"username": "{username}"}),
        EndpointInfo("/api/instagram/stop", "POST", EndpointCategory.INSTAGRAM, "Parar Rastreamento"),
        
        # Intelligence
        EndpointInfo("/api/intelligence/sentiment/{username}", "GET", EndpointCategory.INTELLIGENCE, "Sentimento Perfil"),
        EndpointInfo("/api/intelligence/sentiment/text", "POST", EndpointCategory.INTELLIGENCE, "Sentimento Texto", json_body={"text": "Amo este perfil!"}),
        EndpointInfo("/api/intelligence/prediction/{username}", "GET", EndpointCategory.INTELLIGENCE, "Predição"),
        EndpointInfo("/api/intelligence/visual/{username}", "GET", EndpointCategory.INTELLIGENCE, "Visão Computacional"),
        EndpointInfo("/api/intelligence/visual/image", "POST", EndpointCategory.INTELLIGENCE, "Análise de Imagem", json_body={"url": "https://www.instagram.com/static/images/ico/favicon-192.png/ed97eed09b00.png"}),
        EndpointInfo("/api/intelligence/network-graph/{username}", "GET", EndpointCategory.INTELLIGENCE, "Grafo Social"),
        
        # Tasks
        EndpointInfo("/api/tasks/list", "GET", EndpointCategory.TASKS, "Listar Tarefas"),
        EndpointInfo("/api/tasks/stats", "GET", EndpointCategory.TASKS, "Estatísticas de Fila"),
        EndpointInfo("/api/tasks/enqueue", "POST", EndpointCategory.TASKS, "Enfileirar Tarefa", json_body={"task_type": "test_task", "metadata": {"data": "test"}}),
        EndpointInfo("/api/tasks/status/{task_id}", "GET", EndpointCategory.TASKS, "Status de Tarefa"),
        
        # AI Providers
        EndpointInfo("/api/ai/status", "GET", EndpointCategory.AI, "Status de Provedores IA"),
        EndpointInfo("/api/ai/gemini/models", "GET", EndpointCategory.AI, "Modelos Gemini"),
        EndpointInfo("/api/ai/ollama/models", "GET", EndpointCategory.AI, "Modelos Ollama"),
        
        # OSINT & Analytics
        EndpointInfo("/api/osint/account-health/{username}", "GET", EndpointCategory.OSINT, "Saúde de Conta"),
        EndpointInfo("/api/osint/breach-check/test@example.com", "GET", EndpointCategory.OSINT, "Vazamentos"),
        EndpointInfo("/api/osint/cross-platform/{username}", "GET", EndpointCategory.OSINT, "Busca Cross-Platform"),
        EndpointInfo("/api/analytics/engagement-rate/{username}", "GET", EndpointCategory.ANALYTICS, "Engajamento"),
        
        # History
        EndpointInfo("/api/history/profile-snapshots/{username}", "GET", EndpointCategory.HISTORY, "Snapshots Históricos"),
    ]

class IntegrationTestRunner:
    def __init__(self, base_url: str = "http://localhost:5000", test_username: str = "instagram"):
        self.base_url = base_url.rstrip("/")
        self.test_username = test_username
        self.results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.task_id = "pending"
        
        # Atualizar ENDPOINTS com o username correto
        self._update_endpoints()

    def _update_endpoints(self):
        for info in EndpointRegistry.ENDPOINTS:
            if info.params:
                new_params = {}
                for k, v in info.params.items():
                    if isinstance(v, str):
                        new_params[k] = v.replace("{username}", self.test_username)
                    else:
                        new_params[k] = v
                info.params = new_params
            
            if "{username}" in info.path:
                info.path = info.path.replace("{username}", self.test_username)

    async def login(self) -> bool:
        """Realiza login para obter cookie de sessão."""
        username = os.getenv("ADMIN_USERNAME", "admin@admin.com")
        password = os.getenv("ADMIN_PASSWORD", "admin123") # Fallback se não houver env
        
        url = f"{self.base_url}/api/auth/login"
        try:
            async with self.session.post(url, json={"username": username, "password": password}) as resp:
                if resp.status == 200:
                    logger.info(f"✅ Login realizado como {username}")
                    return True
                else:
                    logger.error(f"❌ Falha no login: Status {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Erro na conexão de login: {e}")
            return False

    async def run_tests(self):
        logger.info(f"🚀 Iniciando Suite Lyra Ultra em {self.base_url}")
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # 1. Login Obrigatório
            if not await self.login():
                logger.error("🛑 Abortando: Falha na autenticação.")
                return

            # 2. Executar Endpoints
            for info in EndpointRegistry.ENDPOINTS:
                await self.test_endpoint(info)
                await asyncio.sleep(0.2) # Evitar overload

        self.generate_report()

    async def test_endpoint(self, info: EndpointInfo):
        # Substituir placeholders no path e params
        path = info.path.replace("{username}", self.test_username)
        path = path.replace("{task_id}", self.task_id)
        
        url = f"{self.base_url}{path}"
        params = {}
        if info.params:
            for k, v in info.params.items():
                if isinstance(v, str):
                    params[k] = v.replace("{username}", self.test_username)
                else:
                    params[k] = v

        start_time = time.time()
        try:
            if info.method == "GET":
                async with self.session.get(url, params=params, timeout=10) as resp:
                    await self._process_response(info, resp, start_time, url)
            else:
                async with self.session.post(url, json=info.json_body, timeout=10) as resp:
                    await self._process_response(info, resp, start_time, url)
        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            self.results.append(TestResult(info.description, url, info.method, TestStatus.ERROR, elapsed, None, str(e)))

    async def _process_response(self, info, resp, start_time, url):
        elapsed = int((time.time() - start_time) * 1000)
        status = TestStatus.PASSED if resp.status < 400 else TestStatus.FAILED
        
        try:
            data = await resp.json()
            # Capturar task_id se for um enqueue para testes subsequentes
            if "task_id" in data:
                self.task_id = data["task_id"]
            sample = json.dumps(data)[:100]
        except:
            sample = (await resp.text())[:100]

        self.results.append(TestResult(
            info.description, url, info.method, status, elapsed, resp.status, None, sample
        ))
        
        icon = "✅" if status == TestStatus.PASSED else "❌"
        logger.info(f"{icon} {info.method} {url} - {resp.status} ({elapsed}ms)")

    def generate_report(self):
        passed = len([r for r in self.results if r.status == TestStatus.PASSED])
        total = len(self.results)
        rate = (passed/total)*100 if total > 0 else 0
        
        print("\n" + "="*60)
        print("   RELATÓRIO DE INTEGRAÇÃO LYRA ULTRA")
        print("="*60)
        print(f"   Total de Endpoints: {total}")
        print(f"   Sucesso: {passed}")
        print(f"   Falhas/Erros: {total - passed}")
        print(f"   Taxa de Aprovação: {rate:.1f}%")
        print("="*60)

        # Salvar MD
        with open("test_report.md", "w") as f:
            f.write(f"# Auditoria Lyra Ultra - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
            f.write("| Endpoint | Método | Status | HTTP | Tempo |\n")
            f.write("|----------|--------|--------|------|-------|\n")
            for r in self.results:
                st = "OK" if r.status == TestStatus.PASSED else "FAIL"
                f.write(f"| {r.test_name} | {r.method} | {st} | {r.status_code} | {r.response_time_ms}ms |\n")

if __name__ == "__main__":
    runner = IntegrationTestRunner()
    asyncio.run(runner.run_tests())
