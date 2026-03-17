"""
Instagram Scraper 2025 - God Mode (No Selenium)
Usa Nodriver (Chrome CDP) para automação e curl_cffi para requests TLS-fingerprinted.
Com rotação de fingerprints TLS (JA3 Spoofing) e Self-Healing.
"""

import asyncio
import json
import re
import random
import logging
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from curl_cffi import requests
from bs4 import BeautifulSoup
try:
    from core.browser_manager import NodriverManager as BrowserManager
except ImportError:
    from browser_manager import NodriverManager as BrowserManager

# Import cache manager para decorators
try:
    try:
        import core.cache_manager  # noqa: F401
    except ImportError:
        import cache_manager  # noqa: F401
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


class TLSFingerprintRotator:
    """
    Gerenciador de rotação de fingerprints TLS (JA3 Spoofing)
    
    Alterna entre diferentes fingerprints de navegadores para evitar detecção.
    Cada fingerprint representa uma combinação Browser + OS realista.
    """
    
    # Pool de fingerprints com impersonates suportados pelo curl_cffi
    FINGERPRINT_POOL = [
        # Chrome Windows
        {"impersonate": "chrome110", "os": "Windows", "browser": "Chrome 110"},
        {"impersonate": "chrome116", "os": "Windows", "browser": "Chrome 116"},
        {"impersonate": "chrome119", "os": "Windows", "browser": "Chrome 119"},
        {"impersonate": "chrome120", "os": "Windows", "browser": "Chrome 120"},
        # Chrome macOS
        {"impersonate": "chrome110", "os": "macOS", "browser": "Chrome 110"},
        {"impersonate": "chrome120", "os": "macOS", "browser": "Chrome 120"},
        # Safari
        {"impersonate": "safari15_3", "os": "macOS", "browser": "Safari 15.3"},
        {"impersonate": "safari15_5", "os": "macOS", "browser": "Safari 15.5"},
        # Edge
        {"impersonate": "edge99", "os": "Windows", "browser": "Edge 99"},
        {"impersonate": "edge101", "os": "Windows", "browser": "Edge 101"},
    ]
    
    # User-Agents correspondentes aos fingerprints
    USER_AGENTS = {
        "chrome110_Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "chrome116_Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "chrome119_Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "chrome120_Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "chrome110_macOS": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "chrome120_macOS": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "safari15_3_macOS": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
        "safari15_5_macOS": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
        "edge99_Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.30",
        "edge101_Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53",
    }
    
    # Accept-Encoding variações
    ACCEPT_ENCODINGS = [
        "gzip, deflate, br",
        "gzip, deflate, br, zstd",
        "gzip, deflate",
        "br, gzip, deflate",
    ]
    
    # Accept-Language variações
    ACCEPT_LANGUAGES = [
        "en-US,en;q=0.9",
        "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
        "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "en-GB,en;q=0.9,en-US;q=0.8",
    ]
    
    def __init__(self, rotate_every_n: int = 10):
        """
        Inicializa o rotador de fingerprints
        
        Args:
            rotate_every_n: Rotacionar após N requisições
        """
        self.rotate_every_n = rotate_every_n
        self.request_count = 0
        self.current_fingerprint = None
        self.current_session = None
        self.logger = logging.getLogger(__name__)
        
        # Selecionar fingerprint inicial aleatório
        self._rotate_fingerprint()
    
    def _rotate_fingerprint(self) -> None:
        """Seleciona um novo fingerprint aleatório do pool"""
        self.current_fingerprint = random.choice(self.FINGERPRINT_POOL)
        self.logger.info(
            f"🔄 Fingerprint rotacionado: {self.current_fingerprint['browser']} "
            f"({self.current_fingerprint['os']})"
        )
    
    def get_current_impersonate(self) -> str:
        """Retorna o impersonate atual"""
        return self.current_fingerprint["impersonate"]
    
    def get_randomized_headers(self) -> Dict[str, str]:
        """
        Gera headers HTTP randomizados baseados no fingerprint atual
        
        Returns:
            Dict com headers HTTP2 variados
        """
        fp = self.current_fingerprint
        ua_key = f"{fp['impersonate']}_{fp['os']}"
        
        headers = {
            'User-Agent': self.USER_AGENTS.get(ua_key, self.USER_AGENTS["chrome120_Windows"]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice(self.ACCEPT_LANGUAGES),
            'Accept-Encoding': random.choice(self.ACCEPT_ENCODINGS),
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            # Headers específicos para parecer mais real
            'sec-ch-ua': f'"Chromium";v="{fp["impersonate"][-3:]}", "Not(A:Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': f'"{fp["os"]}"',
        }
        
        return headers
    
    def should_rotate(self) -> bool:
        """Verifica se deve rotacionar o fingerprint"""
        self.request_count += 1
        return self.request_count >= self.rotate_every_n
    
    def maybe_rotate(self) -> bool:
        """Rotaciona se necessário e retorna True se rotacionou"""
        if self.should_rotate():
            self._rotate_fingerprint()
            self.request_count = 0
            return True
        return False
    
    def create_session(self) -> requests.AsyncSession:
        """
        Cria uma nova AsyncSession com o fingerprint atual
        
        Returns:
            Nova sessão curl_cffi configurada
        """
        self.current_session = requests.AsyncSession(
            impersonate=self.get_current_impersonate()
        )
        self.current_session.headers.update(self.get_randomized_headers())
        return self.current_session
    
    def get_session(self) -> requests.AsyncSession:
        """Retorna a sessão atual, criando se necessário"""
        if self.current_session is None:
            return self.create_session()
        
        # Rotacionar se necessário
        if self.maybe_rotate():
            # Criar nova sessão com novo fingerprint
            return self.create_session()
        
        return self.current_session


# =============================================================================
# SELF-HEALING SCRAPER - PADRÃO STRATEGY
# =============================================================================

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable
import hashlib


class ScrapingStrategy(Enum):
    """Enum das estratégias de scraping disponíveis"""
    GRAPHQL = "graphql"
    API_V1 = "api_v1"
    HTML_PARSING = "html_parsing"
    NODRIVER = "nodriver"


@dataclass
class StrategyResult:
    """Resultado de uma tentativa de scraping"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    strategy_used: Optional[ScrapingStrategy] = None
    response_schema_hash: Optional[str] = None


@dataclass
class APISchemaRegistry:
    """
    Registra schemas de resposta da API para detectar mudanças.
    Permite identificar quando a estrutura de resposta muda.
    """
    known_schemas: Dict[str, str] = field(default_factory=dict)
    schema_change_callbacks: List[Callable] = field(default_factory=list)
    
    def compute_schema_hash(self, data: Dict) -> str:
        """Calcula um hash baseado na estrutura (chaves) do JSON"""
        def extract_keys(obj, prefix=""):
            keys = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    full_key = f"{prefix}.{k}" if prefix else k
                    keys.append(full_key)
                    keys.extend(extract_keys(v, full_key))
            elif isinstance(obj, list) and obj:
                keys.extend(extract_keys(obj[0], f"{prefix}[]"))
            return keys
        
        key_structure = sorted(extract_keys(data))
        return hashlib.md5(str(key_structure).encode()).hexdigest()[:16]
    
    def register_schema(self, endpoint: str, data: Dict) -> bool:
        """
        Registra o schema de um endpoint e retorna True se mudou.
        
        Args:
            endpoint: Nome do endpoint (ex: 'profile_info')
            data: Dados de resposta da API
            
        Returns:
            True se o schema mudou, False se é o mesmo
        """
        new_hash = self.compute_schema_hash(data)
        
        if endpoint in self.known_schemas:
            if self.known_schemas[endpoint] != new_hash:
                # Schema mudou!
                old_hash = self.known_schemas[endpoint]
                self.known_schemas[endpoint] = new_hash
                
                # Notificar callbacks
                for callback in self.schema_change_callbacks:
                    try:
                        callback(endpoint, old_hash, new_hash)
                    except Exception:
                        pass
                
                return True
        else:
            self.known_schemas[endpoint] = new_hash
        
        return False
    
    def on_schema_change(self, callback: Callable) -> None:
        """Registra callback para ser chamado quando schema mudar"""
        self.schema_change_callbacks.append(callback)


class BaseScrapingStrategy(ABC):
    """Classe base abstrata para estratégias de scraping"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.name: ScrapingStrategy = ScrapingStrategy.API_V1
    
    @abstractmethod
    async def execute(self, session, username: str, **kwargs) -> StrategyResult:
        """Executa a estratégia de scraping"""
        pass
    
    def can_handle(self, error: Exception) -> bool:
        """Verifica se esta estratégia pode lidar com o erro anterior"""
        return True


class GraphQLStrategy(BaseScrapingStrategy):
    """Estratégia usando GraphQL API do Instagram"""
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.name = ScrapingStrategy.GRAPHQL
        
        # Query hashes conhecidos (podem mudar)
        self.query_hashes = {
            'user_info': 'c9100bf9110dd6361671f113dd02e7d6',
            'user_posts': 'e769aa130647d2354c40ea6a439bfc08',
            'user_followers': 'd04b0a864b4b54837c0d870b0e77e076',
        }
    
    async def execute(self, session, username: str, **kwargs) -> StrategyResult:
        try:
            # Primeiro obter user_id via web_profile_info
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            headers = kwargs.get('headers', {})
            
            response = await session.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('data', {}).get('user', {})
                
                if user_data:
                    # Calcular hash do schema para detecção de mudanças
                    schema_hash = hashlib.md5(str(sorted(user_data.keys())).encode()).hexdigest()[:16]
                    
                    return StrategyResult(
                        success=True,
                        data=user_data,
                        strategy_used=self.name,
                        response_schema_hash=schema_hash
                    )
            
            return StrategyResult(
                success=False,
                error=f"Status code: {response.status_code}",
                strategy_used=self.name
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                error=str(e),
                strategy_used=self.name
            )


class APIV1Strategy(BaseScrapingStrategy):
    """Estratégia usando API v1 interna do Instagram"""
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.name = ScrapingStrategy.API_V1
    
    async def execute(self, session, username: str, **kwargs) -> StrategyResult:
        try:
            # Endpoint da API v1
            url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
            headers = kwargs.get('headers', {})
            
            # Headers específicos para API v1
            headers.update({
                'X-IG-App-ID': '936619743392459',
                'X-ASBD-ID': '129477',
            })
            
            response = await session.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('data', {}).get('user', {})
                
                if user_data:
                    schema_hash = hashlib.md5(str(sorted(user_data.keys())).encode()).hexdigest()[:16]
                    
                    return StrategyResult(
                        success=True,
                        data=user_data,
                        strategy_used=self.name,
                        response_schema_hash=schema_hash
                    )
            
            return StrategyResult(
                success=False,
                error=f"API v1 status: {response.status_code}",
                strategy_used=self.name
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                error=str(e),
                strategy_used=self.name
            )


class HTMLParsingStrategy(BaseScrapingStrategy):
    """Estratégia usando parsing de HTML da página de perfil"""
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.name = ScrapingStrategy.HTML_PARSING
    
    async def execute(self, session, username: str, **kwargs) -> StrategyResult:
        try:
            url = f"https://www.instagram.com/{username}/"
            headers = kwargs.get('headers', {})
            
            response = await session.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Tentar extrair dados de meta tags
                meta_desc = soup.find('meta', {'name': 'description'})
                og_title = soup.find('meta', {'property': 'og:title'})
                og_image = soup.find('meta', {'property': 'og:image'})
                
                # Tentar extrair JSON embutido no script
                script_tags = soup.find_all('script', {'type': 'application/ld+json'})
                json_data = None
                for script in script_tags:
                    try:
                        json_data = json.loads(script.string)
                        break
                    except:
                        continue
                
                # Construir dados a partir do que conseguimos extrair
                user_data = {
                    'username': username,
                    'biography': meta_desc.get('content', '') if meta_desc else '',
                    'full_name': og_title.get('content', '').split('(')[0].strip() if og_title else '',
                    'profile_pic_url': og_image.get('content', '') if og_image else '',
                }
                
                # Parsear contadores do meta description
                # Formato típico: "100 Followers, 50 Following, 10 Posts - Descrição"
                if meta_desc:
                    content = meta_desc.get('content', '')
                    import re
                    followers_match = re.search(r'([\d,\.]+[KMB]?)\s*Followers', content, re.I)
                    following_match = re.search(r'([\d,\.]+[KMB]?)\s*Following', content, re.I)
                    
                    if followers_match:
                        user_data['followers_count'] = self._parse_count(followers_match.group(1))
                    if following_match:
                        user_data['following_count'] = self._parse_count(following_match.group(1))
                
                if json_data:
                    user_data['extracted_json'] = json_data
                
                return StrategyResult(
                    success=True,
                    data=user_data,
                    strategy_used=self.name
                )
            
            return StrategyResult(
                success=False,
                error=f"HTML status: {response.status_code}",
                strategy_used=self.name
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                error=str(e),
                strategy_used=self.name
            )
    
    def _parse_count(self, count_str: str) -> int:
        """Converte strings como '1.5K', '2M' para números"""
        count_str = count_str.replace(',', '').replace('.', '')
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
        
        for suffix, mult in multipliers.items():
            if suffix in count_str.upper():
                return int(float(count_str.upper().replace(suffix, '')) * mult)
        
        try:
            return int(count_str)
        except:
            return 0


class NodriverStrategy(BaseScrapingStrategy):
    """Estratégia usando Nodriver (Chrome CDP) - último recurso"""
    
    def __init__(self, logger=None, browser_manager=None):
        super().__init__(logger)
        self.name = ScrapingStrategy.NODRIVER
        self.browser_manager = browser_manager
    
    async def execute(self, session, username: str, **kwargs) -> StrategyResult:
        try:
            if not self.browser_manager:
                return StrategyResult(
                    success=False,
                    error="Browser manager não disponível",
                    strategy_used=self.name
                )
            
            # Navegar para o perfil usando Nodriver
            url = f"https://www.instagram.com/{username}/"
            page = await self.browser_manager.navigate(url)
            
            if page:
                # Aguardar carregamento e extrair dados via JavaScript
                await asyncio.sleep(2)  # Aguardar renderização
                
                # Extrair dados via script
                script = """
                () => {
                    const meta = document.querySelector('meta[name="description"]');
                    const title = document.querySelector('meta[property="og:title"]');
                    const image = document.querySelector('meta[property="og:image"]');
                    return {
                        description: meta ? meta.content : '',
                        title: title ? title.content : '',
                        image: image ? image.content : ''
                    };
                }
                """
                
                result = await page.evaluate(script)
                
                user_data = {
                    'username': username,
                    'biography': result.get('description', ''),
                    'full_name': result.get('title', '').split('(')[0].strip(),
                    'profile_pic_url': result.get('image', ''),
                }
                
                return StrategyResult(
                    success=True,
                    data=user_data,
                    strategy_used=self.name
                )
            
            return StrategyResult(
                success=False,
                error="Nodriver navigation failed",
                strategy_used=self.name
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                error=str(e),
                strategy_used=self.name
            )


class SelfHealingScraper:
    """
    Orquestrador de Self-Healing que gerencia múltiplas estratégias.
    
    Ordem de tentativa:
    1. GraphQL API (mais rápido, mais dados)
    2. API v1 (fallback robusto)
    3. HTML Parsing (quando APIs falham)
    4. Nodriver (último recurso, mais lento)
    """
    
    def __init__(self, session, browser_manager=None):
        self.session = session
        self.logger = logging.getLogger(__name__)
        self.schema_registry = APISchemaRegistry()
        
        # Registrar callback para log de mudanças de schema
        self.schema_registry.on_schema_change(self._on_schema_change)
        
        # Inicializar estratégias em ordem de preferência
        self.strategies: List[BaseScrapingStrategy] = [
            GraphQLStrategy(self.logger),
            APIV1Strategy(self.logger),
            HTMLParsingStrategy(self.logger),
            NodriverStrategy(self.logger, browser_manager),
        ]
        
        # Estatísticas de uso
        self.stats = {
            'total_requests': 0,
            'strategy_usage': {s.value: 0 for s in ScrapingStrategy},
            'failures': 0,
            'schema_changes_detected': 0,
        }
    
    def _on_schema_change(self, endpoint: str, old_hash: str, new_hash: str):
        """Callback quando detecta mudança de schema"""
        self.stats['schema_changes_detected'] += 1
        self.logger.warning(
            f"⚠️ ALERTA: Schema da API mudou! Endpoint: {endpoint}, "
            f"Hash antigo: {old_hash}, Novo: {new_hash}"
        )
    
    async def get_profile(self, username: str, headers: Dict = None) -> StrategyResult:
        """
        Tenta obter perfil usando estratégias encadeadas.
        
        Args:
            username: Nome de usuário do Instagram
            headers: Headers HTTP opcionais
            
        Returns:
            StrategyResult com dados ou erro
        """
        self.stats['total_requests'] += 1
        headers = headers or {}
        
        last_error = None
        
        for strategy in self.strategies:
            self.logger.info(f"🔄 Tentando estratégia: {strategy.name.value}")
            
            result = await strategy.execute(self.session, username, headers=headers)
            
            if result.success:
                self.stats['strategy_usage'][strategy.name.value] += 1
                
                # Registrar schema para detecção de mudanças
                if result.data and result.response_schema_hash:
                    self.schema_registry.register_schema(
                        f"profile_{strategy.name.value}",
                        result.data if isinstance(result.data, dict) else {}
                    )
                
                self.logger.info(f"✅ Sucesso com estratégia: {strategy.name.value}")
                return result
            
            last_error = result.error
            self.logger.warning(f"❌ Falha com {strategy.name.value}: {result.error}")
        
        # Todas estratégias falharam
        self.stats['failures'] += 1
        self.logger.error(f"❌ Todas as estratégias falharam para {username}")
        
        return StrategyResult(
            success=False,
            error=f"Todas estratégias falharam. Último erro: {last_error}"
        )
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso das estratégias"""
        return self.stats.copy()

class InstagramScraper2025:
    """
    Scraper principal do Instagram com Self-Healing e TLS Fingerprint Rotation.
    
    Integra:
    - TLSFingerprintRotator para rotação de fingerprints
    - SelfHealingScraper para fallback automático de estratégias
    - Cache Manager para otimização de requisições
    """
    
    def __init__(self, headless=True, rotate_fingerprint_every: int = 10):
        self.headless = headless
        self.browser_manager = None
        
        # Sistema de rotação de fingerprints TLS
        self.fingerprint_rotator = TLSFingerprintRotator(rotate_every_n=rotate_fingerprint_every)
        
        # Usar session com fingerprint rotativo
        self.session = self.fingerprint_rotator.create_session()
        self.logged_in = False
        self.username = None
        self.db_name = 'instagram_tracker.db'
        self._init_db()
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Self-Healing Scraper com fallback automático de estratégias
        self.self_healing = SelfHealingScraper(
            session=self.session,
            browser_manager=self.browser_manager
        )

    def _init_db(self):
        """Inicializa o banco de dados SQLite"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS post_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                post_code TEXT NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, post_code)
            )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro DB: {e}")

    def initialize_browser(self):
        """Inicializa o NodriverManager se necessário"""
        if not self.browser_manager:
            self.browser_manager = NodriverManager(headless=self.headless)
            return True
        return True

    def login_optional(self, username=None, password=None):
        """Login opcional usando Nodriver (CDP) - Wrapper síncrono"""
        return asyncio.run(self.login_optional_async(username, password))

    async def login_optional_async(self, username=None, password=None):
        """Login opcional usando Nodriver (CDP) - Versão assíncrona"""
        if not username or not password:
            self.logger.info("Nenhuma credencial fornecida. Funcionando sem login.")
            return True
        
        try:
            self.logger.info(f"Tentando fazer login para {username} via Nodriver...")
            
            # Inicializar Nodriver
            if not self.browser_manager:
                self.initialize_browser()
            
            # Tentar login
            success = await self.browser_manager.login(username, password)
            
            if success:
                self.logged_in = True
                self.username = username
                self.logger.info(f"Login Nodriver realizado com sucesso para {username}")
                
                # Sincronizar cookies do Nodriver para o curl_cffi session
                await self._sync_cookies()
                return True
            else:
                self.logger.error("Login Nodriver falhou")
                return False
                
        except Exception as e:
            self.logger.warning(f"Falha no login: {e}. Continuando sem login.")
            return False

    async def _sync_cookies(self):
        """Sincroniza cookies do Nodriver para a sessão curl_cffi"""
        try:
            if self.browser_manager:
                cookies = await self.browser_manager.get_cookies()
                for cookie in cookies:
                    self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', ''))
                self.logger.info("Cookies sincronizados para requests")
        except Exception as e:
            self.logger.error(f"Erro ao sincronizar cookies: {e}")

    def _get_api_headers(self):
        """Retorna headers específicos para chamadas de API interna"""
        # Usar headers do fingerprint rotator como base
        headers = self.fingerprint_rotator.get_randomized_headers()
        headers.update({
            'X-IG-App-ID': '936619743392459',
            'X-ASBD-ID': '129477',
            'X-IG-WWW-Claim': '0',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': '*/*',
        })
        # Adicionar CSRF token se disponível
        csrf = self.session.cookies.get('csrftoken')
        if csrf:
            headers['X-CSRFToken'] = csrf
        return headers

    def get_user_info(self, username):
        """Obtém informações do usuário (Wrapper síncrono para compatibilidade)"""
        return asyncio.run(self.get_profile_info_fast(username))

    async def get_profile_info_fast(self, username):
        """Obtém info do perfil via API Interna (v1)"""
        try:
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            headers = self._get_api_headers()
            
            response = await self.session.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('data', {}).get('user', {})
                if user_data:
                    return self._normalize_user_data(user_data, username)
            
            # Fallback: HTML Parsing se API falhar (ex: bloqueio de endpoint)
            return await self._get_profile_html_fallback(username)
            
        except Exception as e:
            self.logger.error(f"Erro ao obter perfil de {username}: {e}")
            return None

    async def _get_profile_html_fallback(self, username):
        """Fallback via HTML Parsing"""
        try:
            response = await self.session.get(f"https://www.instagram.com/{username}/")
            if response.status_code == 200:
                # Tentar extrair meta tags
                soup = BeautifulSoup(response.text, 'html.parser')
                meta_desc = soup.find('meta', {'name': 'description'})
                if meta_desc:
                    content = meta_desc.get('content', '')
                    # Parsear "100 Followers, 50 Following, 10 Posts..."
                    # Implementação simplificada para fallback
                    return {'username': username, 'biography': content}
            return None
        except:
            return None

    def _normalize_user_data(self, data, username):
        """Normaliza dados da API v1"""
        return {
            'id': data.get('id'),
            'username': data.get('username', username),
            'full_name': data.get('full_name', ''),
            'biography': data.get('biography', ''),
            'followers_count': data.get('edge_followed_by', {}).get('count', 0),
            'following_count': data.get('edge_follow', {}).get('count', 0),
            'is_private': data.get('is_private', False),
            'is_verified': data.get('is_verified', False),
            'profile_pic_url': data.get('profile_pic_url_hd', ''),
            'external_url': data.get('external_url', '')
        }

    def get_user_posts(self, username, limit=20, ignore_pinned=False, media_type='both', start_date=None, end_date=None):
        """Obtém posts (Wrapper síncrono)"""
        return asyncio.run(self.get_user_posts_async(username, limit, ignore_pinned, media_type, start_date, end_date))

    async def get_user_posts_async(self, username, limit=20, ignore_pinned=False, media_type='both', start_date=None, end_date=None):
        """Obtém posts (Versão assíncrona)"""
        # Primeiro precisamos do ID
        user_info = await self.get_profile_info_fast(username)
        if not user_info:
            return []
        
        user_id = user_info.get('id')
        posts = await self.get_user_posts_fast(user_id, count=limit)
        
        # Filtragem básica (implementar filtros de data/pin se necessário)
        return posts if isinstance(posts, list) else posts[0]

    async def get_user_posts_fast(self, user_id, count=12, end_cursor=None):
        """Obtém posts via GraphQL API"""
        try:
            variables = {
                "id": user_id,
                "first": count,
                "after": end_cursor
            }
            params = {
                "query_hash": "e769aa130647d2354c40ea6a439bfc08", # Hash comum para user posts
                "variables": json.dumps(variables)
            }
            
            # URL alternativa se query_hash falhar: API v1
            url = f"https://www.instagram.com/api/v1/feed/user/{user_id}/"
            headers = self._get_api_headers()
            
            response = await self.session.get(url, headers=headers)
            posts = []
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                for item in items:
                    # Tentar obter a melhor imagem disponível
                    image_versions = item.get('image_versions2', {}).get('candidates', [])
                    thumbnail_url = image_versions[0].get('url') if image_versions else None
                    
                    posts.append({
                        'code': item.get('code'),
                        'url': f"https://www.instagram.com/p/{item.get('code')}/",
                        'caption': item.get('caption', {}).get('text', ''),
                        'timestamp': item.get('taken_at'),
                        'like_count': item.get('like_count'),
                        'comment_count': item.get('comment_count'),
                        'media_type': 'video' if item.get('media_type') == 2 else 'image',
                        'thumbnail_url': thumbnail_url,
                        'location': {
                            'name': item.get('location', {}).get('name') if item.get('location') else None,
                            'lat': item.get('location', {}).get('lat') if item.get('location') else None,
                            'lng': item.get('location', {}).get('lng') if item.get('location') else None,
                            'id': item.get('location', {}).get('pk') if item.get('location') else None
                        } if item.get('location') else None
                    })
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Erro ao obter posts: {e}")
            return []

    def get_following_list(self, username, limit=50):
        """Obtém lista de seguindo (Wrapper síncrono)"""
        return asyncio.run(self.get_following_list_async(username, limit))

    async def get_following_list_async(self, username, limit=50):
        """Obtém lista de seguindo (Versão assíncrona)"""
        user_info = await self.get_profile_info_fast(username)
        if not user_info:
            return []
        user_id = user_info.get('id')
        return await self.get_following_list_fast(user_id, count=limit)

    async def get_following_list_fast(self, user_id, count=50):
        """Obtém lista de seguindo via API"""
        if not self.logged_in:
            self.logger.warning("Login necessário para ver lista de seguindo")
            return []
            
        try:
            url = f"https://www.instagram.com/api/v1/friendships/{user_id}/following/?count={count}"
            headers = self._get_api_headers()
            
            response = await self.session.get(url, headers=headers)
            following = []
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                for user in users:
                    following.append({
                        'username': user.get('username'),
                        'full_name': user.get('full_name'),
                        'is_private': user.get('is_private'),
                        'profile_pic_url': user.get('profile_pic_url')
                    })
            
            return following
            
        except Exception as e:
            self.logger.error(f"Erro ao obter seguindo: {e}")
            return []
            
    async def get_post_details_fast(self, shortcode):
        """Obtém detalhes do post via API GraphQL/v1"""
        try:
            # Tentar via API v1 info
            url = f"https://www.instagram.com/api/v1/media/{shortcode}/info/"
            # Nota: shortcode precisa ser convertido para media_id para v1, ou usar endpoint graphql
            # Vamos usar endpoint público de graphql que funciona bem com sessão autenticada
            
            # Alternativa: Web Info Endpoint
            url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
            headers = self._get_api_headers()
            
            response = await self.session.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes do post {shortcode}: {e}")
            return None

    def cleanup(self):
        """Limpa recursos (Wrapper síncrono)"""
        try:
            asyncio.run(self.cleanup_async())
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {e}")

    async def cleanup_async(self):
        """Limpa recursos (Versão assíncrona)"""
        try:
            if self.browser_manager:
                await self.browser_manager.close()
            # Session do curl_cffi não precisa de close explícito se usada em context manager, mas aqui é persistente
            # self.session.close() # AsyncSession close é async
        except Exception as e:
            self.logger.error(f"Erro na limpeza assíncrona: {e}")

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

if __name__ == "__main__":
    print("Testando Instagram Scraper 2025 (God Mode - No Selenium)...")
    
    try:
        # Teste rápido
        with InstagramScraper2025(headless=False) as scraper:
            user_info = scraper.get_user_info("instagram")
            if user_info:
                print(f"✅ Usuário encontrado: {user_info.get('username')}")
            else:
                print("❌ Erro ao obter usuário")
                
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
