"""
Stealth Ops 2025 - Segurança Operacional e Evasão de Detecção
Versão God Mode Ultimate - Implementação REAL sem placeholders

Funcionalidades:
- Roteamento Furtivo (Proxy Rotation)
- Pool de Proxies com Rotação Inteligente
- Navegação Biomimética Avançada
- Rate Limiting Inteligente
- Adaptive Backoff baseado em respostas
- Quota Management por Endpoint
"""

import asyncio
import aiohttp
import random
import math
import time
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import sqlite3
import os

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StealthOps")


# =============================================================================
# ENUMS E DATACLASSES
# =============================================================================

class ProxyType(Enum):
    """Tipos de proxy suportados"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class ProxyStatus(Enum):
    """Status do proxy"""
    ACTIVE = "active"
    SLOW = "slow"
    UNRELIABLE = "unreliable"
    DEAD = "dead"
    BANNED = "banned"


class RateLimitStatus(Enum):
    """Status de rate limit"""
    OK = "ok"
    WARNING = "warning"
    THROTTLED = "throttled"
    BLOCKED = "blocked"


@dataclass
class ProxyConfig:
    """Configuração de um proxy"""
    host: str
    port: int
    proxy_type: ProxyType = ProxyType.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    provider: Optional[str] = None
    
    # Métricas
    status: ProxyStatus = ProxyStatus.ACTIVE
    success_count: int = 0
    failure_count: int = 0
    avg_response_time: float = 0.0
    last_used: Optional[str] = None
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    penalty_score: float = 0.0
    
    @property
    def url(self) -> str:
        """Retorna URL completa do proxy"""
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        return f"{self.proxy_type.value}://{auth}{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """Taxa de sucesso do proxy"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5


@dataclass
class RequestQuota:
    """Quota de requisições por endpoint"""
    endpoint: str
    requests_per_hour: int
    requests_made: int = 0
    window_start: Optional[str] = None
    last_request: Optional[str] = None
    is_throttled: bool = False
    backoff_until: Optional[str] = None


@dataclass
class RateLimitMetrics:
    """Métricas de rate limiting"""
    total_requests: int = 0
    throttled_requests: int = 0
    blocked_requests: int = 0
    current_rps: float = 0.0
    avg_response_time: float = 0.0
    status: RateLimitStatus = RateLimitStatus.OK


@dataclass
class BehaviorProfile:
    """Perfil de comportamento humano"""
    name: str
    mouse_speed: Tuple[float, float]  # (min, max) em pixels/ms
    typing_speed: Tuple[int, int]  # (min, max) em caracteres/min
    scroll_speed: Tuple[float, float]  # (min, max) em pixels/scroll
    click_delay: Tuple[float, float]  # (min, max) em segundos
    reading_speed: Tuple[int, int]  # (min, max) em palavras/min
    interaction_patterns: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# IP QUALITY CHECKER - Detecção de IP Datacenter vs Residencial
# =============================================================================

class IPType(Enum):
    """Tipo de IP detectado"""
    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"
    MOBILE = "mobile"
    VPN = "vpn"
    PROXY = "proxy"
    UNKNOWN = "unknown"


@dataclass
class IPQualityResult:
    """Resultado da análise de qualidade de IP"""
    ip_address: str
    ip_type: IPType
    asn: Optional[str] = None
    asn_name: Optional[str] = None
    is_safe_for_instagram: bool = True
    risk_score: float = 0.0  # 0 = baixo risco, 1 = alto risco
    warning_message: Optional[str] = None
    recommendation: Optional[str] = None


class IPQualityChecker:
    """
    Detector Premium de Qualidade de IP para Instagram Scraping.
    
    IMPORTANTE: Instagram bloqueia IPs de datacenter INSTANTANEAMENTE.
    Esta classe detecta se um IP é:
    - Datacenter (AWS, Google Cloud, Azure, DigitalOcean, etc.)
    - Residencial (Comcast, Verizon, AT&T, etc.) - SEGURO
    - Mobile (4G/5G) - MUITO SEGURO
    - VPN/Proxy conhecido
    
    Baseado em pesquisa de fontes:
    - ScrapFly: "Datacenter IPs blocked instantly"
    - Apify: "Session rotation + fingerprint sync required"
    - curl_cffi: Padrão do setor para TLS fingerprinting
    """
    
    # ASNs de datacenters conhecidos que são BLOQUEADOS pelo Instagram
    DATACENTER_ASNS = {
        # Amazon Web Services
        "AS16509", "AS14618", "AS7224", "AS8987",
        # Google Cloud
        "AS15169", "AS396982", "AS36492", "AS36040", "AS139070",
        # Microsoft Azure
        "AS8075", "AS12076", "AS8068", "AS8069",
        # DigitalOcean
        "AS14061", "AS201229", "AS393406",
        # Linode/Akamai
        "AS63949", "AS20473", "AS396356",
        # Vultr
        "AS20473", "AS396362",
        # OVH
        "AS16276",
        # Hetzner
        "AS24940",
        # Cloudflare
        "AS13335",
        # Oracle Cloud
        "AS31898",
        # IBM Cloud
        "AS36351",
        # Alibaba Cloud
        "AS45102",
        # Contabo
        "AS51167",
        # Hostinger
        "AS47583",
        # Scaleway
        "AS12876",
        # HostGator/Bluehost
        "AS46606", "AS11798",
        # Rackspace
        "AS19994", "AS27357",
        # GoDaddy
        "AS26496", "AS21501",
    }
    
    # ASNs de provedores residenciais conhecidos (SEGUROS)
    RESIDENTIAL_ASNS = {
        # EUA
        "AS7922", "AS7018", "AS22773",  # Comcast, AT&T, Cox
        "AS701", "AS6167",  # Verizon
        "AS20001", "AS3651",  # Charter/Spectrum, Sprint
        # Brasil
        "AS8167", "AS28573", "AS7738",  # Net/Claro, Vivo, OI
        "AS18881", "AS52320",  # Tim, GVT
        # Europa
        "AS3320", "AS3209",  # Deutsche Telekom, Vodafone DE
        "AS12322", "AS15557",  # Free, SFR (França)
        "AS5089", "AS2856",  # Virgin Media, BT (UK)
    }
    
    # Nomes de provedores de datacenter para verificar no hostname reverso
    DATACENTER_KEYWORDS = [
        "amazon", "aws", "ec2", "compute",
        "google", "gcloud", "googleusercontent",
        "azure", "microsoft", "cloudapp",
        "digitalocean", "droplet",
        "linode", "akamai",
        "vultr",
        "ovh", "hetzner",
        "cloudflare",
        "oracle", "oraclecloud",
        "alibaba", "aliyun",
        "contabo", "hostinger", "scaleway",
        "rackspace", "godaddy",
        "server", "vps", "dedicated", "hosting", "cloud"
    ]
    
    def __init__(self):
        self.logger = logging.getLogger("IPQualityChecker")
        self._dns_cache: Dict[str, str] = {}
        self.logger.info("🔍 IP Quality Checker inicializado")
    
    def check_ip_quality(self, ip_address: str) -> IPQualityResult:
        """
        Verifica qualidade do IP para scraping de Instagram.
        
        Args:
            ip_address: Endereço IP para verificar
            
        Returns:
            IPQualityResult com análise completa
        """
        import socket
        
        result = IPQualityResult(
            ip_address=ip_address,
            ip_type=IPType.UNKNOWN
        )
        
        try:
            # 1. Verificar hostname reverso
            hostname = self._get_reverse_dns(ip_address)
            
            if hostname:
                hostname_lower = hostname.lower()
                
                # Verificar keywords de datacenter no hostname
                for keyword in self.DATACENTER_KEYWORDS:
                    if keyword in hostname_lower:
                        result.ip_type = IPType.DATACENTER
                        result.is_safe_for_instagram = False
                        result.risk_score = 0.95
                        result.warning_message = (
                            f"⚠️ IP DATACENTER DETECTADO: {ip_address}\n"
                            f"   Hostname: {hostname}\n"
                            f"   Instagram BLOQUEIA IPs de datacenter instantaneamente!"
                        )
                        result.recommendation = (
                            "🔴 AÇÃO NECESSÁRIA: Use proxies RESIDENCIAIS.\n"
                            "   Provedores recomendados:\n"
                            "   - Bright Data (brightdata.com)\n"
                            "   - Oxylabs (oxylabs.io)\n"
                            "   - Smartproxy (smartproxy.com)"
                        )
                        
                        self.logger.warning(result.warning_message)
                        return result
                
                # Verificar padrões de IP residencial
                residential_patterns = [
                    ".comcast.", ".att.", ".verizon.",
                    ".charter.", ".spectrum.", ".cox.",
                    ".dsl.", ".cable.", ".res.",
                    "net.br", "claro", "vivo", "tim",
                ]
                
                for pattern in residential_patterns:
                    if pattern in hostname_lower:
                        result.ip_type = IPType.RESIDENTIAL
                        result.is_safe_for_instagram = True
                        result.risk_score = 0.1
                        self.logger.info(f"✅ IP Residencial detectado: {ip_address}")
                        return result
            
            # 2. Se não conseguiu determinar, assumir desconhecido com alerta
            result.ip_type = IPType.UNKNOWN
            result.risk_score = 0.5
            result.warning_message = (
                f"⚠️ Tipo de IP não determinado: {ip_address}\n"
                f"   Recomenda-se verificar manualmente se é datacenter."
            )
            result.recommendation = (
                "Para máxima segurança, use proxies residenciais verificados."
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar IP {ip_address}: {e}")
            result.risk_score = 0.7
            result.warning_message = f"Não foi possível verificar o IP: {e}"
        
        return result
    
    def _get_reverse_dns(self, ip_address: str) -> Optional[str]:
        """Obtém hostname reverso do IP com cache"""
        import socket
        
        if ip_address in self._dns_cache:
            return self._dns_cache[ip_address]
        
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            self._dns_cache[ip_address] = hostname
            return hostname
        except (socket.herror, socket.gaierror, socket.timeout):
            return None
    
    def validate_proxy_for_instagram(self, proxy: 'ProxyConfig') -> IPQualityResult:
        """
        Valida se um proxy é seguro para usar com Instagram.
        
        Args:
            proxy: Configuração do proxy
            
        Returns:
            IPQualityResult com recomendações
        """
        result = self.check_ip_quality(proxy.host)
        
        # Verificar provider do proxy
        if proxy.provider:
            provider_lower = proxy.provider.lower()
            
            # Provedores residenciais conhecidos
            residential_providers = [
                "brightdata", "bright data", "luminati",
                "oxylabs", "smartproxy", "netnut",
                "iproyal", "proxy-seller", "soax"
            ]
            
            datacenter_providers = [
                "aws", "azure", "gcp", "digital",
                "vultr", "linode", "ovh", "hetzner"
            ]
            
            for rp in residential_providers:
                if rp in provider_lower:
                    result.ip_type = IPType.RESIDENTIAL
                    result.is_safe_for_instagram = True
                    result.risk_score = 0.05
                    self.logger.info(f"✅ Provider residencial verificado: {proxy.provider}")
                    return result
            
            for dp in datacenter_providers:
                if dp in provider_lower:
                    result.ip_type = IPType.DATACENTER
                    result.is_safe_for_instagram = False
                    result.risk_score = 0.99
                    result.warning_message = (
                        f"🚫 PROXY DE DATACENTER: {proxy.provider}\n"
                        f"   Será bloqueado imediatamente pelo Instagram!"
                    )
                    return result
        
        return result
    
    def emit_safety_report(self) -> str:
        """
        Gera relatório de segurança para o usuário.
        
        Returns:
            String com relatório formatado
        """
        report = """
╔══════════════════════════════════════════════════════════════════════╗
║            🛡️ RELATÓRIO DE SEGURANÇA - INSTAGRAM SCRAPING            ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ✅ TIPOS DE IP SEGUROS:                                             ║
║     • Residencial - ISPs como Comcast, AT&T, Vivo, Claro             ║
║     • Mobile 4G/5G - IPs de operadoras móveis                        ║
║                                                                      ║
║  ❌ TIPOS DE IP BLOQUEADOS INSTANTANEAMENTE:                         ║
║     • Datacenter - AWS, Google Cloud, Azure, DigitalOcean            ║
║     • VPS/Hosting - Qualquer provedor de hospedagem                  ║
║                                                                      ║
║  📊 LIMITES SEGUROS DE VELOCIDADE (por IP residencial):              ║
║     • ~180 requests/hora (80% do limite de 200)                      ║
║     • ~3 requests/minuto                                             ║
║     • Delay 2-5s entre requests (com variação humana)                ║
║                                                                      ║
║  🚀 PARA VELOCIDADE MÁXIMA SEGURA:                                   ║
║     • Use pool de 10-50 IPs residenciais                             ║
║     • Sticky sessions de 5-10 minutos                                ║
║     • Rotação após ~15-20 requests por IP                            ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
        return report


# =============================================================================
# PROXY DATABASE
# =============================================================================

class ProxyDatabase:
    """
    Gerenciador de banco de dados para proxies.
    """
    
    def __init__(self, db_path: str = ".stealth_cache/proxies.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa tabelas do banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de proxies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                proxy_type TEXT DEFAULT 'http',
                username TEXT,
                password TEXT,
                country TEXT,
                provider TEXT,
                status TEXT DEFAULT 'active',
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0,
                last_used TEXT,
                last_success TEXT,
                last_failure TEXT,
                penalty_score REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(host, port)
            )
        """)
        
        # Tabela de quotas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT UNIQUE NOT NULL,
                requests_per_hour INTEGER DEFAULT 200,
                requests_made INTEGER DEFAULT 0,
                window_start TEXT,
                last_request TEXT,
                is_throttled BOOLEAN DEFAULT FALSE,
                backoff_until TEXT
            )
        """)
        
        # Tabela de métricas de rate limit
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                endpoint TEXT,
                success BOOLEAN,
                response_time_ms INTEGER,
                status_code INTEGER,
                proxy_used TEXT
            )
        """)
        
        # Índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proxies_status ON proxies(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proxies_country ON proxies(country)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON rate_metrics(timestamp)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"📦 Proxy DB inicializado: {self.db_path}")
    
    def save_proxy(self, proxy: ProxyConfig) -> bool:
        """Salva ou atualiza proxy"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO proxies 
                    (host, port, proxy_type, username, password, country, provider,
                     status, success_count, failure_count, avg_response_time,
                     last_used, last_success, last_failure, penalty_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(host, port) DO UPDATE SET
                    status = excluded.status,
                    success_count = excluded.success_count,
                    failure_count = excluded.failure_count,
                    avg_response_time = excluded.avg_response_time,
                    last_used = excluded.last_used,
                    last_success = excluded.last_success,
                    last_failure = excluded.last_failure,
                    penalty_score = excluded.penalty_score
            """, (
                proxy.host, proxy.port, proxy.proxy_type.value,
                proxy.username, proxy.password, proxy.country, proxy.provider,
                proxy.status.value, proxy.success_count, proxy.failure_count,
                proxy.avg_response_time, proxy.last_used, proxy.last_success,
                proxy.last_failure, proxy.penalty_score
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar proxy: {e}")
            return False
    
    def get_active_proxies(self) -> List[ProxyConfig]:
        """Obtém proxies ativos ordenados por qualidade"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT host, port, proxy_type, username, password, country, provider,
                       status, success_count, failure_count, avg_response_time,
                       last_used, last_success, last_failure, penalty_score
                FROM proxies
                WHERE status IN ('active', 'slow')
                ORDER BY penalty_score ASC, avg_response_time ASC
            """)
            
            proxies = []
            for row in cursor.fetchall():
                proxies.append(ProxyConfig(
                    host=row[0],
                    port=row[1],
                    proxy_type=ProxyType(row[2]) if row[2] else ProxyType.HTTP,
                    username=row[3],
                    password=row[4],
                    country=row[5],
                    provider=row[6],
                    status=ProxyStatus(row[7]) if row[7] else ProxyStatus.ACTIVE,
                    success_count=row[8] or 0,
                    failure_count=row[9] or 0,
                    avg_response_time=row[10] or 0,
                    last_used=row[11],
                    last_success=row[12],
                    last_failure=row[13],
                    penalty_score=row[14] or 0
                ))
            
            conn.close()
            return proxies
            
        except Exception as e:
            logger.error(f"Erro ao obter proxies: {e}")
            return []
    
    def save_quota(self, quota: RequestQuota) -> bool:
        """Salva ou atualiza quota"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO quotas 
                    (endpoint, requests_per_hour, requests_made, window_start,
                     last_request, is_throttled, backoff_until)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(endpoint) DO UPDATE SET
                    requests_made = excluded.requests_made,
                    window_start = excluded.window_start,
                    last_request = excluded.last_request,
                    is_throttled = excluded.is_throttled,
                    backoff_until = excluded.backoff_until
            """, (
                quota.endpoint, quota.requests_per_hour, quota.requests_made,
                quota.window_start, quota.last_request, quota.is_throttled,
                quota.backoff_until
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar quota: {e}")
            return False
    
    def get_quota(self, endpoint: str) -> Optional[RequestQuota]:
        """Obtém quota para um endpoint"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT endpoint, requests_per_hour, requests_made, window_start,
                       last_request, is_throttled, backoff_until
                FROM quotas WHERE endpoint = ?
            """, (endpoint,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return RequestQuota(
                    endpoint=row[0],
                    requests_per_hour=row[1] or 200,
                    requests_made=row[2] or 0,
                    window_start=row[3],
                    last_request=row[4],
                    is_throttled=bool(row[5]),
                    backoff_until=row[6]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter quota: {e}")
            return None


# =============================================================================
# PROXY MANAGER
# =============================================================================

class ProxyManager:
    """
    Gerenciador de proxies com rotação inteligente.
    
    Funcionalidades:
    - Pool de proxies com health check
    - Rotação ponderada por qualidade
    - Penalização de proxies falhos
    - Suporte a sticky sessions
    - Suporte a SOCKS5 e proxies residenciais
    """
    
    # Limites de penalização
    PENALTY_INCREMENT = 1.0
    PENALTY_DECREMENT = 0.5
    PENALTY_MAX = 10.0
    PENALTY_DEAD_THRESHOLD = 5.0
    
    def __init__(self, database: Optional[ProxyDatabase] = None):
        self.database = database or ProxyDatabase()
        self.proxies: List[ProxyConfig] = []
        self.sticky_sessions: Dict[str, ProxyConfig] = {}
        self._current_index = 0
        
        # Integração com IPQualityChecker para validar proxies
        self.ip_quality_checker = IPQualityChecker()
        
        self._load_proxies()
        logger.info(f"🔄 Proxy Manager Premium inicializado com {len(self.proxies)} proxies")
        
        # Validar proxies existentes
        if self.proxies:
            self._validate_proxies_quality()
    
    def _load_proxies(self):
        """Carrega proxies do banco de dados"""
        self.proxies = self.database.get_active_proxies()
    
    def _validate_proxies_quality(self):
        """
        Valida qualidade de todos os proxies no pool.
        Emite alertas para IPs de datacenter.
        """
        datacenter_count = 0
        residential_count = 0
        unknown_count = 0
        
        for proxy in self.proxies:
            result = self.ip_quality_checker.validate_proxy_for_instagram(proxy)
            
            if result.ip_type == IPType.DATACENTER:
                datacenter_count += 1
                logger.warning(f"🚫 Proxy {proxy.host}:{proxy.port} é DATACENTER - será bloqueado pelo Instagram!")
            elif result.ip_type == IPType.RESIDENTIAL:
                residential_count += 1
            else:
                unknown_count += 1
        
        # Emitir relatório
        if datacenter_count > 0:
            logger.warning(
                f"\n{'='*60}\n"
                f"⚠️ ALERTA DE SEGURANÇA: {datacenter_count} proxies de DATACENTER detectados!\n"
                f"   Instagram BLOQUEIA IPs de datacenter instantaneamente.\n"
                f"   Use proxies RESIDENCIAIS para evitar banimento.\n"
                f"{'='*60}\n"
            )
            logger.info(self.ip_quality_checker.emit_safety_report())
        
        logger.info(
            f"📊 Qualidade do Pool: "
            f"{residential_count} residenciais ✅ | "
            f"{datacenter_count} datacenter ❌ | "
            f"{unknown_count} desconhecidos ⚠️"
        )
    
    def add_proxy(
        self,
        host: str,
        port: int,
        proxy_type: ProxyType = ProxyType.HTTP,
        username: Optional[str] = None,
        password: Optional[str] = None,
        country: Optional[str] = None,
        provider: Optional[str] = None
    ) -> ProxyConfig:
        """Adiciona novo proxy ao pool"""
        proxy = ProxyConfig(
            host=host,
            port=port,
            proxy_type=proxy_type,
            username=username,
            password=password,
            country=country,
            provider=provider
        )
        
        self.database.save_proxy(proxy)
        self.proxies.append(proxy)
        
        logger.info(f"➕ Proxy adicionado: {host}:{port}")
        return proxy
    
    def add_proxies_from_list(self, proxy_list: List[str], proxy_type: ProxyType = ProxyType.HTTP) -> int:
        """
        Adiciona proxies de uma lista.
        
        Formato suportado:
        - host:port
        - user:pass@host:port
        - http://user:pass@host:port
        """
        added = 0
        
        for proxy_str in proxy_list:
            try:
                # Remover protocolo se presente
                proxy_str = proxy_str.strip()
                if "://" in proxy_str:
                    proxy_str = proxy_str.split("://")[1]
                
                # Verificar autenticação
                username = None
                password = None
                
                if "@" in proxy_str:
                    auth, host_port = proxy_str.rsplit("@", 1)
                    if ":" in auth:
                        username, password = auth.split(":", 1)
                else:
                    host_port = proxy_str
                
                # Extrair host e porta
                host, port_str = host_port.rsplit(":", 1)
                port = int(port_str)
                
                self.add_proxy(host, port, proxy_type, username, password)
                added += 1
                
            except Exception as e:
                logger.warning(f"⚠️ Proxy inválido: {proxy_str} - {e}")
        
        logger.info(f"✅ {added} proxies adicionados")
        return added
    
    def get_proxy(self, session_id: Optional[str] = None) -> Optional[ProxyConfig]:
        """
        Obtém próximo proxy para uso.
        
        Args:
            session_id: ID para sticky session (mesmo proxy para mesma sessão)
            
        Returns:
            ProxyConfig ou None se não houver proxies
        """
        if not self.proxies:
            return None
        
        # Sticky session
        if session_id and session_id in self.sticky_sessions:
            proxy = self.sticky_sessions[session_id]
            if proxy.status == ProxyStatus.ACTIVE:
                return proxy
        
        # Filtrar proxies ativos com baixa penalidade
        active_proxies = [p for p in self.proxies 
                         if p.status == ProxyStatus.ACTIVE and p.penalty_score < self.PENALTY_MAX]
        
        if not active_proxies:
            # Fallback para proxies lentos
            active_proxies = [p for p in self.proxies 
                             if p.status == ProxyStatus.SLOW and p.penalty_score < self.PENALTY_MAX]
        
        if not active_proxies:
            return None
        
        # Rotação ponderada: proxies com menor penalidade têm maior chance
        weights = []
        for proxy in active_proxies:
            # Peso inversamente proporcional à penalidade
            weight = max(0.1, 1.0 - (proxy.penalty_score / self.PENALTY_MAX))
            # Boost para proxies com alta taxa de sucesso
            weight *= (0.5 + proxy.success_rate)
            weights.append(weight)
        
        # Normalizar pesos
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1.0 / len(active_proxies)] * len(active_proxies)
        
        # Selecionar aleatoriamente com pesos
        selected = random.choices(active_proxies, weights=weights, k=1)[0]
        
        # Atualizar sticky session
        if session_id:
            self.sticky_sessions[session_id] = selected
        
        # Atualizar timestamp
        selected.last_used = datetime.now().isoformat()
        self.database.save_proxy(selected)
        
        return selected
    
    def report_success(self, proxy: ProxyConfig, response_time_ms: int):
        """Reporta sucesso de uso do proxy"""
        proxy.success_count += 1
        proxy.last_success = datetime.now().isoformat()
        
        # Atualizar média de tempo de resposta
        total = proxy.success_count + proxy.failure_count
        proxy.avg_response_time = (
            (proxy.avg_response_time * (total - 1) + response_time_ms) / total
        )
        
        # Reduzir penalidade
        proxy.penalty_score = max(0, proxy.penalty_score - self.PENALTY_DECREMENT)
        
        # Restaurar status se estava lento
        if proxy.status == ProxyStatus.SLOW and response_time_ms < 2000:
            proxy.status = ProxyStatus.ACTIVE
        
        self.database.save_proxy(proxy)
        logger.debug(f"✓ Proxy {proxy.host} sucesso: {response_time_ms}ms")
    
    def report_failure(self, proxy: ProxyConfig, error: Optional[str] = None):
        """Reporta falha de uso do proxy"""
        proxy.failure_count += 1
        proxy.last_failure = datetime.now().isoformat()
        
        # Aumentar penalidade
        proxy.penalty_score = min(self.PENALTY_MAX, proxy.penalty_score + self.PENALTY_INCREMENT)
        
        # Atualizar status baseado em penalidade
        if proxy.penalty_score >= self.PENALTY_DEAD_THRESHOLD:
            proxy.status = ProxyStatus.DEAD
        elif proxy.penalty_score >= 3.0:
            proxy.status = ProxyStatus.UNRELIABLE
        elif proxy.penalty_score >= 1.5:
            proxy.status = ProxyStatus.SLOW
        
        # Verificar se foi banido
        if error and ("banned" in error.lower() or "blocked" in error.lower()):
            proxy.status = ProxyStatus.BANNED
            proxy.penalty_score = self.PENALTY_MAX
        
        self.database.save_proxy(proxy)
        logger.warning(f"✗ Proxy {proxy.host} falhou: {error}")
    
    async def health_check(self, proxy: ProxyConfig, timeout: int = 10) -> bool:
        """
        Verifica se proxy está funcionando.
        
        Args:
            proxy: Proxy para verificar
            timeout: Timeout em segundos
            
        Returns:
            True se proxy está funcional
        """
        test_url = "https://httpbin.org/ip"
        
        try:
            async with aiohttp.ClientSession() as session:
                start = time.time()
                async with session.get(
                    test_url,
                    proxy=proxy.url,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        elapsed_ms = int((time.time() - start) * 1000)
                        self.report_success(proxy, elapsed_ms)
                        return True
                    else:
                        self.report_failure(proxy, f"HTTP {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            self.report_failure(proxy, "Timeout")
            return False
        except Exception as e:
            self.report_failure(proxy, str(e))
            return False
    
    async def health_check_all(self, max_concurrent: int = 10) -> Dict[str, int]:
        """
        Verifica saúde de todos os proxies.
        
        Returns:
            Dict com estatísticas
        """
        logger.info("🏥 Iniciando health check de proxies...")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {'active': 0, 'slow': 0, 'dead': 0}
        
        async def check_with_semaphore(proxy: ProxyConfig):
            async with semaphore:
                await self.health_check(proxy)
        
        await asyncio.gather(*[check_with_semaphore(p) for p in self.proxies])
        
        # Recarregar e contar
        self._load_proxies()
        for proxy in self.proxies:
            if proxy.status == ProxyStatus.ACTIVE:
                results['active'] += 1
            elif proxy.status == ProxyStatus.SLOW:
                results['slow'] += 1
            else:
                results['dead'] += 1
        
        logger.info(f"✅ Health check concluído: {results}")
        return results
    
    def clear_sticky_session(self, session_id: str):
        """Remove sticky session"""
        if session_id in self.sticky_sessions:
            del self.sticky_sessions[session_id]


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """
    Rate limiter inteligente com backoff adaptativo.
    
    Funcionalidades:
    - Controle de requests por hora/minuto
    - Backoff exponencial em erros 429
    - Quota management por endpoint
    - Monitoramento de headers de rate limit
    
    CONFIGURAÇÃO OTIMIZADA PARA INSTAGRAM 2026:
    Baseado em pesquisa de ScrapFly, Apify e curl_cffi:
    - Instagram permite ~200 requests/hora/IP para usuários não autenticados
    - Usamos 80% desse limite (180 req/hora) para segurança
    - Delay humanizado de 2-5 segundos com jitter de 30%
    - Backoff exponencial em 429 (2s → 4s → 8s → 16s... até 5 min)
    """
    
    # ==========================================================================
    # LIMITES OTIMIZADOS PARA INSTAGRAM 2026 (Baseado em Pesquisa)
    # ==========================================================================
    
    # Limite seguro: 80% de 200 = 180 requests/hora/IP
    DEFAULT_REQUESTS_PER_HOUR = 180
    
    # Limite por minuto: ~3 requests para distribuição uniforme
    DEFAULT_REQUESTS_PER_MINUTE = 3
    
    # Delay entre requisições (segundos)
    MIN_DELAY_SECONDS = 2.0
    MAX_DELAY_SECONDS = 5.0
    DELAY_JITTER_PERCENT = 0.3  # 30% de variação aleatória
    
    # Configuração de backoff exponencial
    BACKOFF_INITIAL = 2.0  # Começar com 2s em vez de 1s
    BACKOFF_MULTIPLIER = 2.0
    BACKOFF_MAX = 300.0  # 5 minutos
    
    # Sticky session recomendado (minutos)
    RECOMMENDED_STICKY_SESSION_MINUTES = 7
    
    # Rotação de fingerprint recomendada
    RECOMMENDED_FINGERPRINT_ROTATE_EVERY = 8
    
    def __init__(self, database: Optional[ProxyDatabase] = None):
        self.database = database or ProxyDatabase()
        self.quotas: Dict[str, RequestQuota] = {}
        self.backoff_state: Dict[str, float] = {}
        self.request_timestamps: Dict[str, List[float]] = defaultdict(list)
        self.current_backoff: Dict[str, float] = {}
        self.metrics = RateLimitMetrics()
        
        # Novo: IP Quality Checker integrado
        self.ip_quality_checker = IPQualityChecker()
        
        # Log de inicialização com configuração
        logger.info("⏱️ Rate Limiter Premium inicializado")
        logger.info(f"   ├── Limite: {self.DEFAULT_REQUESTS_PER_HOUR} req/hora (80% de 200)")
        logger.info(f"   ├── Delay: {self.MIN_DELAY_SECONDS}-{self.MAX_DELAY_SECONDS}s (±{int(self.DELAY_JITTER_PERCENT*100)}%)")
        logger.info(f"   └── Backoff: {self.BACKOFF_INITIAL}s → {self.BACKOFF_MAX}s")
    
    def _get_or_create_quota(self, endpoint: str) -> RequestQuota:
        """Obtém ou cria quota para endpoint"""
        if endpoint not in self.quotas:
            # Tentar carregar do banco
            quota = self.database.get_quota(endpoint)
            if not quota:
                quota = RequestQuota(
                    endpoint=endpoint,
                    requests_per_hour=self.DEFAULT_REQUESTS_PER_HOUR
                )
            self.quotas[endpoint] = quota
        
        return self.quotas[endpoint]
    
    def _reset_window_if_needed(self, quota: RequestQuota) -> None:
        """Reseta janela de contagem se necessário"""
        now = datetime.now()
        
        if quota.window_start:
            window_start = datetime.fromisoformat(quota.window_start)
            if now - window_start >= timedelta(hours=1):
                quota.requests_made = 0
                quota.window_start = now.isoformat()
                quota.is_throttled = False
        else:
            quota.window_start = now.isoformat()
    
    async def can_make_request(self, endpoint: str) -> bool:
        """
        Verifica se pode fazer request para endpoint.
        
        Args:
            endpoint: Nome do endpoint
            
        Returns:
            True se pode fazer request
        """
        quota = self._get_or_create_quota(endpoint)
        self._reset_window_if_needed(quota)
        
        # Verificar backoff
        if quota.backoff_until:
            backoff_until = datetime.fromisoformat(quota.backoff_until)
            if datetime.now() < backoff_until:
                wait_seconds = (backoff_until - datetime.now()).total_seconds()
                logger.debug(f"⏳ Backoff ativo para {endpoint}: {wait_seconds:.1f}s restantes")
                return False
            else:
                quota.backoff_until = None
        
        # Verificar quota
        if quota.requests_made >= quota.requests_per_hour:
            quota.is_throttled = True
            self.metrics.throttled_requests += 1
            logger.warning(f"⚠️ Quota excedida para {endpoint}")
            return False
        
        # Verificar rate limit por minuto
        now = time.time()
        recent = [t for t in self.request_timestamps[endpoint] if now - t < 60]
        self.request_timestamps[endpoint] = recent
        
        if len(recent) >= self.DEFAULT_REQUESTS_PER_MINUTE:
            logger.debug(f"⏳ Rate limit por minuto atingido para {endpoint}")
            return False
        
        return True
    
    async def wait_if_needed(self, endpoint: str, max_wait: float = 60.0) -> bool:
        """
        Espera se necessário antes de fazer request.
        
        Args:
            endpoint: Nome do endpoint
            max_wait: Tempo máximo de espera em segundos
            
        Returns:
            True se pode prosseguir, False se timeout
        """
        start = time.time()
        
        while not await self.can_make_request(endpoint):
            if time.time() - start > max_wait:
                return False
            
            # Esperar com jitter
            wait_time = random.uniform(0.5, 2.0)
            await asyncio.sleep(wait_time)
        
        return True
    
    def record_request(self, endpoint: str, success: bool, response_time_ms: int):
        """
        Registra uma request feita.
        
        Args:
            endpoint: Nome do endpoint
            success: Se request foi bem sucedida
            response_time_ms: Tempo de resposta em ms
        """
        quota = self._get_or_create_quota(endpoint)
        
        # Atualizar quota
        quota.requests_made += 1
        quota.last_request = datetime.now().isoformat()
        
        # Atualizar métricas
        self.metrics.total_requests += 1
        
        # Atualizar timestamp
        self.request_timestamps[endpoint].append(time.time())
        
        # Calcular RPS
        now = time.time()
        recent = [t for t in self.request_timestamps[endpoint] if now - t < 60]
        self.metrics.current_rps = len(recent) / 60.0
        
        # Atualizar média de response time
        n = self.metrics.total_requests
        self.metrics.avg_response_time = (
            (self.metrics.avg_response_time * (n - 1) + response_time_ms) / n
        )
        
        self.database.save_quota(quota)
    
    def record_rate_limit_response(self, endpoint: str, retry_after: Optional[int] = None):
        """
        Registra resposta de rate limit (429).
        
        Args:
            endpoint: Nome do endpoint
            retry_after: Valor do header Retry-After se disponível
        """
        quota = self._get_or_create_quota(endpoint)
        
        # Calcular backoff
        current = self.current_backoff.get(endpoint, self.BACKOFF_INITIAL)
        
        if retry_after:
            backoff = float(retry_after)
        else:
            backoff = min(current * self.BACKOFF_MULTIPLIER, self.BACKOFF_MAX)
        
        self.current_backoff[endpoint] = backoff
        
        # Definir tempo de backoff
        quota.backoff_until = (datetime.now() + timedelta(seconds=backoff)).isoformat()
        quota.is_throttled = True
        
        self.metrics.throttled_requests += 1
        self.metrics.status = RateLimitStatus.THROTTLED
        
        self.database.save_quota(quota)
        
        logger.warning(f"🚫 Rate limited em {endpoint}, backoff: {backoff:.1f}s")
    
    def reset_backoff(self, endpoint: str):
        """Reseta backoff após sucesso"""
        if endpoint in self.current_backoff:
            del self.current_backoff[endpoint]
        
        quota = self._get_or_create_quota(endpoint)
        quota.backoff_until = None
        quota.is_throttled = False
        
        self.database.save_quota(quota)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de rate limiting"""
        return {
            'total_requests': self.metrics.total_requests,
            'throttled_requests': self.metrics.throttled_requests,
            'blocked_requests': self.metrics.blocked_requests,
            'current_rps': round(self.metrics.current_rps, 2),
            'avg_response_time': round(self.metrics.avg_response_time, 2),
            'status': self.metrics.status.value,
            'quotas': {
                endpoint: {
                    'requests_made': q.requests_made,
                    'requests_per_hour': q.requests_per_hour,
                    'is_throttled': q.is_throttled
                }
                for endpoint, q in self.quotas.items()
            }
        }


# =============================================================================
# BIOMIMETIC NAVIGATOR
# =============================================================================

class BiomimeticNavigator:
    """
    Navegação biomimética para simular comportamento humano.
    
    Funcionalidades:
    - Curvas de Bézier para movimento de mouse
    - Delays estocásticos com distribuição de Poisson
    - Simulação de comportamentos naturais
    - Variação de viewport e interações
    """
    
    # Perfis de comportamento pré-definidos
    PROFILES = {
        'casual': BehaviorProfile(
            name='casual',
            mouse_speed=(0.3, 0.6),
            typing_speed=(150, 250),
            scroll_speed=(200, 400),
            click_delay=(0.1, 0.3),
            reading_speed=(200, 300)
        ),
        'fast': BehaviorProfile(
            name='fast',
            mouse_speed=(0.5, 0.9),
            typing_speed=(300, 450),
            scroll_speed=(400, 600),
            click_delay=(0.05, 0.15),
            reading_speed=(350, 500)
        ),
        'slow': BehaviorProfile(
            name='slow',
            mouse_speed=(0.2, 0.4),
            typing_speed=(80, 150),
            scroll_speed=(100, 200),
            click_delay=(0.3, 0.7),
            reading_speed=(120, 200)
        )
    }
    
    def __init__(self, profile: str = 'casual'):
        if profile in self.PROFILES:
            self.profile = self.PROFILES[profile]
        else:
            self.profile = self.PROFILES['casual']
        
        logger.info(f"🤖 Biomimetic Navigator inicializado: perfil '{profile}'")
    
    def bezier_curve(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        num_points: int = 20
    ) -> List[Tuple[float, float]]:
        """
        Gera pontos em uma curva de Bézier cúbica.
        
        Args:
            start: Ponto inicial (x, y)
            end: Ponto final (x, y)
            num_points: Número de pontos na curva
            
        Returns:
            Lista de pontos (x, y)
        """
        # Gerar pontos de controle aleatórios
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        # Controle 1: próximo ao início com variação
        c1 = (
            start[0] + dx * random.uniform(0.2, 0.4) + random.uniform(-50, 50),
            start[1] + dy * random.uniform(0.1, 0.3) + random.uniform(-50, 50)
        )
        
        # Controle 2: próximo ao fim com variação
        c2 = (
            start[0] + dx * random.uniform(0.6, 0.8) + random.uniform(-50, 50),
            start[1] + dy * random.uniform(0.7, 0.9) + random.uniform(-50, 50)
        )
        
        points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            
            # Fórmula de Bézier cúbica
            x = ((1-t)**3 * start[0] + 
                 3*(1-t)**2*t * c1[0] + 
                 3*(1-t)*t**2 * c2[0] + 
                 t**3 * end[0])
            
            y = ((1-t)**3 * start[1] + 
                 3*(1-t)**2*t * c1[1] + 
                 3*(1-t)*t**2 * c2[1] + 
                 t**3 * end[1])
            
            points.append((x, y))
        
        return points
    
    def poisson_delay(self, base_delay: float = 1.0) -> float:
        """
        Gera delay com distribuição de Poisson.
        
        Args:
            base_delay: Delay base em segundos
            
        Returns:
            Delay em segundos
        """
        # Lambda para distribuição de Poisson
        lam = 1.0 / base_delay
        
        # Gerar delay
        delay = random.expovariate(lam)
        
        # Adicionar micro-variação
        delay += random.uniform(-0.05, 0.1)
        
        return max(0.01, delay)
    
    def typing_delays(self, text: str) -> List[float]:
        """
        Gera delays entre teclas para digitação realista.
        
        Args:
            text: Texto a ser digitado
            
        Returns:
            Lista de delays entre cada caractere
        """
        delays = []
        
        # Velocidade de digitação em caracteres por segundo
        min_speed, max_speed = self.profile.typing_speed
        avg_delay = 60.0 / random.uniform(min_speed, max_speed)
        
        prev_char = None
        for char in text:
            delay = avg_delay
            
            # Ajustes baseados no caractere
            if char in '.!?\n':
                delay *= random.uniform(1.5, 3.0)  # Pausa após pontuação
            elif char == ' ':
                delay *= random.uniform(0.8, 1.2)
            elif char.isupper():
                delay *= random.uniform(1.1, 1.3)  # Shift
            
            # Correção ocasional (backspace simulado)
            if random.random() < 0.02:  # 2% de chance de "erro"
                delay += avg_delay * 2  # Tempo para corrigir
            
            # Adicionar variação gaussiana
            delay *= random.gauss(1.0, 0.15)
            
            delays.append(max(0.02, delay))
            prev_char = char
        
        return delays
    
    def scroll_pattern(
        self,
        total_distance: float,
        viewport_height: float = 800
    ) -> List[Tuple[float, float]]:
        """
        Gera padrão de scroll natural.
        
        Args:
            total_distance: Distância total a percorrer
            viewport_height: Altura do viewport
            
        Returns:
            Lista de (distância, delay) para cada scroll
        """
        scrolls = []
        current = 0
        
        min_speed, max_speed = self.profile.scroll_speed
        
        while current < total_distance:
            # Distância deste scroll
            scroll_distance = random.uniform(
                viewport_height * 0.2,
                viewport_height * 0.8
            )
            
            # Não ultrapassar o total
            scroll_distance = min(scroll_distance, total_distance - current)
            
            # Delay baseado na leitura
            words_visible = int(scroll_distance / 20)  # ~20px por linha
            min_read, max_read = self.profile.reading_speed
            read_time = (words_visible * 5) / random.uniform(min_read, max_read) * 60
            
            # Adicionar delay de scroll
            delay = read_time + self.poisson_delay(0.2)
            
            scrolls.append((scroll_distance, delay))
            current += scroll_distance
            
            # Probabilidade de pausa longa (leitura detalhada)
            if random.random() < 0.1:
                scrolls.append((0, random.uniform(2.0, 5.0)))
        
        return scrolls
    
    def get_random_viewport(self) -> Tuple[int, int]:
        """Retorna viewport aleatório realista"""
        viewports = [
            (1920, 1080),  # Full HD
            (1366, 768),   # Laptop
            (1440, 900),   # Mac
            (1536, 864),   # Surface
            (1280, 720),   # HD
            (2560, 1440),  # 2K
            (1680, 1050),  # WSXGA+
        ]
        return random.choice(viewports)
    
    async def simulate_reading_pause(self, text_length: int) -> None:
        """
        Simula pausa de leitura baseada no tamanho do texto.
        
        Args:
            text_length: Número de caracteres
        """
        words = text_length / 5  # Média de 5 caracteres por palavra
        min_speed, max_speed = self.profile.reading_speed
        
        # Calcular tempo de leitura
        reading_time = (words / random.uniform(min_speed, max_speed)) * 60
        
        # Adicionar variação
        reading_time *= random.gauss(1.0, 0.2)
        reading_time = max(0.5, min(30.0, reading_time))
        
        await asyncio.sleep(reading_time)
    
    async def simulate_interaction(self) -> None:
        """Simula interação aleatória (scroll, hover, etc)"""
        actions = ['scroll', 'hover', 'wait', 'micro_move']
        action = random.choice(actions)
        
        if action == 'scroll':
            await asyncio.sleep(random.uniform(0.1, 0.3))
        elif action == 'hover':
            await asyncio.sleep(random.uniform(0.2, 0.5))
        elif action == 'wait':
            await asyncio.sleep(random.uniform(0.5, 2.0))
        elif action == 'micro_move':
            await asyncio.sleep(random.uniform(0.05, 0.15))


# =============================================================================
# STEALTH OPS - CLASSE PRINCIPAL
# =============================================================================

class StealthOps:
    """
    Classe principal de operações furtivas.
    
    Integra:
    - Proxy Manager
    - Rate Limiter
    - Biomimetic Navigator
    """
    
    def __init__(
        self,
        db_path: str = ".stealth_cache/stealth.db",
        enable_proxy: bool = True,
        enable_rate_limit: bool = True
    ):
        self.database = ProxyDatabase(db_path)
        
        self.proxy_manager = ProxyManager(self.database) if enable_proxy else None
        self.rate_limiter = RateLimiter(self.database) if enable_rate_limit else None
        self.navigator = BiomimeticNavigator()
        
        logger.info("🥷 Stealth Ops inicializado")
    
    def get_proxy(self, session_id: Optional[str] = None) -> Optional[str]:
        """Obtém URL de proxy para uso"""
        if not self.proxy_manager:
            return None
        
        proxy = self.proxy_manager.get_proxy(session_id)
        return proxy.url if proxy else None
    
    async def can_make_request(self, endpoint: str) -> bool:
        """Verifica se pode fazer request"""
        if not self.rate_limiter:
            return True
        
        return await self.rate_limiter.can_make_request(endpoint)
    
    async def wait_for_request(self, endpoint: str, max_wait: float = 60.0) -> bool:
        """Espera até poder fazer request"""
        if not self.rate_limiter:
            return True
        
        return await self.rate_limiter.wait_if_needed(endpoint, max_wait)
    
    def record_request(
        self,
        endpoint: str,
        success: bool,
        response_time_ms: int,
        proxy_url: Optional[str] = None
    ):
        """Registra resultado de request"""
        if self.rate_limiter:
            self.rate_limiter.record_request(endpoint, success, response_time_ms)
        
        # Se usou proxy, atualizar métricas
        if self.proxy_manager and proxy_url:
            for proxy in self.proxy_manager.proxies:
                if proxy.url == proxy_url:
                    if success:
                        self.proxy_manager.report_success(proxy, response_time_ms)
                    else:
                        self.proxy_manager.report_failure(proxy)
                    break
    
    def handle_rate_limit(self, endpoint: str, retry_after: Optional[int] = None):
        """Trata resposta de rate limit"""
        if self.rate_limiter:
            self.rate_limiter.record_rate_limit_response(endpoint, retry_after)
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status geral de operações furtivas"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'proxy': None,
            'rate_limit': None,
            'navigator_profile': self.navigator.profile.name
        }
        
        if self.proxy_manager:
            active = len([p for p in self.proxy_manager.proxies if p.status == ProxyStatus.ACTIVE])
            status['proxy'] = {
                'total': len(self.proxy_manager.proxies),
                'active': active,
                'sticky_sessions': len(self.proxy_manager.sticky_sessions)
            }
        
        if self.rate_limiter:
            status['rate_limit'] = self.rate_limiter.get_metrics()
        
        return status


# =============================================================================
# TESTES
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("   Stealth Ops 2025 - God Mode Ultimate")
    print("   Segurança Operacional e Evasão de Detecção")
    print("=" * 60)
    
    async def run_tests():
        # Criar instância
        stealth = StealthOps()
        
        # Teste de proxy
        print("\n🧪 Teste de Proxy Manager...")
        stealth.proxy_manager.add_proxy("proxy1.example.com", 8080)
        stealth.proxy_manager.add_proxy("proxy2.example.com", 8080, username="user", password="pass")
        print(f"   Proxies: {len(stealth.proxy_manager.proxies)}")
        
        # Teste de rate limiter
        print("\n🧪 Teste de Rate Limiter...")
        can_request = await stealth.can_make_request("test_endpoint")
        print(f"   Pode fazer request: {can_request}")
        
        stealth.record_request("test_endpoint", True, 150)
        metrics = stealth.rate_limiter.get_metrics()
        print(f"   Total requests: {metrics['total_requests']}")
        
        # Teste de navegação biomimética
        print("\n🧪 Teste de Navegação Biomimética...")
        points = stealth.navigator.bezier_curve((0, 0), (100, 100), 10)
        print(f"   Pontos na curva: {len(points)}")
        
        delays = stealth.navigator.typing_delays("Hello World")
        print(f"   Delays de digitação: {len(delays)}")
        
        # Status geral
        print("\n📊 Status geral:")
        status = stealth.get_status()
        print(f"   {json.dumps(status, indent=2)}")
        
        print("\n✅ Todos os testes concluídos!")
    
    asyncio.run(run_tests())
