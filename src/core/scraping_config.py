"""
Instagram Tracker 2026 - Configuração Centralizada de Velocidade

Este arquivo contém todas as configurações de velocidade e segurança para
scraping de Instagram, baseadas em pesquisa de fontes técnicas:
- ScrapFly: Rate limits e detecção de bots
- Apify: Session rotation e fingerprinting
- curl_cffi: TLS fingerprinting

USO:
    from src.core.scraping_config import ScrapingConfig
    
    # Obter configuração padrão (segura)
    config = ScrapingConfig.get_safe_config()
    
    # Obter configuração agressiva (mais rápida, maior risco)
    config = ScrapingConfig.get_aggressive_config()
    
    # Configuração customizada
    config = ScrapingConfig(
        requests_per_hour_per_ip=150,
        min_delay_seconds=3.0,
        max_delay_seconds=6.0
    )
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger("ScrapingConfig")


class ScrapingMode(Enum):
    """Modos de operação de scraping"""
    SAFE = "safe"           # Conservador, baixo risco de banimento
    BALANCED = "balanced"   # Equilibrado, bom para uso diário
    AGGRESSIVE = "aggressive"  # Rápido, maior risco de rate limit
    STEALTH = "stealth"     # Ultra-conservador, para contas sensíveis


@dataclass
class ScrapingConfig:
    """
    Configuração centralizada para velocidade e segurança de scraping.
    
    Atributos:
        mode: Modo de operação (safe, balanced, aggressive, stealth)
        requests_per_hour_per_ip: Limite de requests por hora por IP
        requests_per_minute: Limite de requests por minuto
        min_delay_seconds: Delay mínimo entre requisições
        max_delay_seconds: Delay máximo entre requisições
        delay_jitter_percent: Variação aleatória no delay (0.0 a 1.0)
        fingerprint_rotate_every: Rotacionar fingerprint a cada N requests
        sticky_session_minutes: Duração de sticky session em minutos
        backoff_initial: Tempo inicial de backoff em segundos
        backoff_multiplier: Multiplicador de backoff exponencial
        backoff_max: Tempo máximo de backoff em segundos
    """
    
    # Modo de operação
    mode: ScrapingMode = ScrapingMode.BALANCED
    
    # =========================================================================
    # LIMITES DE VELOCIDADE (Baseado em Pesquisa 2026)
    # =========================================================================
    
    # Limite de requests por hora por IP (Instagram: ~200, usamos 80% = 160-180)
    requests_per_hour_per_ip: int = 180
    
    # Limite de requests por minuto (para distribuição uniforme)
    requests_per_minute: int = 3
    
    # =========================================================================
    # DELAYS HUMANIZADOS
    # =========================================================================
    
    # Delay mínimo entre requisições (segundos)
    min_delay_seconds: float = 2.0
    
    # Delay máximo entre requisições (segundos)
    max_delay_seconds: float = 5.0
    
    # Variação aleatória no delay (30% = 0.3)
    delay_jitter_percent: float = 0.3
    
    # =========================================================================
    # ROTAÇÃO E SESSÕES
    # =========================================================================
    
    # Rotacionar fingerprint TLS a cada N requests
    fingerprint_rotate_every: int = 8
    
    # Duração de sticky session em minutos (usar mesmo IP)
    sticky_session_minutes: int = 7
    
    # Rotacionar proxy a cada N requests (0 = não rotacionar)
    proxy_rotate_every: int = 0
    
    # =========================================================================
    # BACKOFF EXPONENCIAL (para erros 429/503)
    # =========================================================================
    
    # Tempo inicial de backoff (segundos)
    backoff_initial: float = 2.0
    
    # Multiplicador de backoff exponencial
    backoff_multiplier: float = 2.0
    
    # Tempo máximo de backoff (segundos) - 5 minutos
    backoff_max: float = 300.0
    
    # =========================================================================
    # SEGURANÇA
    # =========================================================================
    
    # Bloquear IPs de datacenter automaticamente
    block_datacenter_ips: bool = True
    
    # Alertar sobre IPs não residenciais
    warn_non_residential_ips: bool = True
    
    # Verificar qualidade do IP antes de usar
    check_ip_quality: bool = True
    
    # =========================================================================
    # MÉTODOS DE FÁBRICA
    # =========================================================================
    
    @classmethod
    def get_safe_config(cls) -> 'ScrapingConfig':
        """
        Configuração segura para uso conservador.
        Prioriza segurança sobre velocidade.
        
        - 120 requests/hora (60% do limite)
        - Delays de 3-6 segundos
        - Rotação de fingerprint a cada 5 requests
        """
        logger.info("📦 Carregando configuração SAFE")
        return cls(
            mode=ScrapingMode.SAFE,
            requests_per_hour_per_ip=120,
            requests_per_minute=2,
            min_delay_seconds=3.0,
            max_delay_seconds=6.0,
            delay_jitter_percent=0.4,
            fingerprint_rotate_every=5,
            sticky_session_minutes=10,
            backoff_initial=3.0,
            block_datacenter_ips=True,
            warn_non_residential_ips=True,
            check_ip_quality=True
        )
    
    @classmethod
    def get_balanced_config(cls) -> 'ScrapingConfig':
        """
        Configuração balanceada para uso diário.
        Equilíbrio entre velocidade e segurança.
        
        - 180 requests/hora (80% do limite)
        - Delays de 2-5 segundos
        - Rotação de fingerprint a cada 8 requests
        """
        logger.info("📦 Carregando configuração BALANCED")
        return cls(
            mode=ScrapingMode.BALANCED,
            requests_per_hour_per_ip=180,
            requests_per_minute=3,
            min_delay_seconds=2.0,
            max_delay_seconds=5.0,
            delay_jitter_percent=0.3,
            fingerprint_rotate_every=8,
            sticky_session_minutes=7,
            backoff_initial=2.0,
            block_datacenter_ips=True,
            warn_non_residential_ips=True,
            check_ip_quality=True
        )
    
    @classmethod
    def get_aggressive_config(cls) -> 'ScrapingConfig':
        """
        Configuração agressiva para máxima velocidade.
        ATENÇÃO: Maior risco de rate limiting.
        
        - 200 requests/hora (100% do limite)
        - Delays de 1-3 segundos
        - Rotação de fingerprint a cada 15 requests
        """
        logger.warning("⚠️ Carregando configuração AGGRESSIVE - maior risco de rate limiting!")
        return cls(
            mode=ScrapingMode.AGGRESSIVE,
            requests_per_hour_per_ip=200,
            requests_per_minute=4,
            min_delay_seconds=1.0,
            max_delay_seconds=3.0,
            delay_jitter_percent=0.2,
            fingerprint_rotate_every=15,
            sticky_session_minutes=5,
            backoff_initial=1.0,
            block_datacenter_ips=True,
            warn_non_residential_ips=False,
            check_ip_quality=False
        )
    
    @classmethod
    def get_stealth_config(cls) -> 'ScrapingConfig':
        """
        Configuração ultra-conservadora para contas sensíveis.
        Minimiza absolutamente o risco de detecção.
        
        - 60 requests/hora (30% do limite)
        - Delays de 5-10 segundos
        - Rotação de fingerprint a cada 3 requests
        """
        logger.info("🥷 Carregando configuração STEALTH - máxima segurança")
        return cls(
            mode=ScrapingMode.STEALTH,
            requests_per_hour_per_ip=60,
            requests_per_minute=1,
            min_delay_seconds=5.0,
            max_delay_seconds=10.0,
            delay_jitter_percent=0.5,
            fingerprint_rotate_every=3,
            sticky_session_minutes=15,
            backoff_initial=5.0,
            block_datacenter_ips=True,
            warn_non_residential_ips=True,
            check_ip_quality=True
        )
    
    # =========================================================================
    # MÉTODOS UTILITÁRIOS
    # =========================================================================
    
    def get_random_delay(self) -> float:
        """
        Calcula delay aleatório humanizado.
        
        Returns:
            Delay em segundos com jitter aplicado
        """
        import random
        
        base_delay = random.uniform(self.min_delay_seconds, self.max_delay_seconds)
        jitter = base_delay * self.delay_jitter_percent * random.uniform(-1, 1)
        
        return max(0.5, base_delay + jitter)  # Mínimo 0.5s
    
    def get_theoretical_max_profiles_per_hour(self, num_ips: int = 1) -> int:
        """
        Calcula máximo teórico de perfis por hora.
        
        Args:
            num_ips: Número de IPs residenciais disponíveis
            
        Returns:
            Número máximo de perfis que podem ser scrapeados por hora
        """
        profiles_per_ip = self.requests_per_hour_per_ip
        return profiles_per_ip * num_ips
    
    def estimate_time_for_profiles(self, num_profiles: int, num_ips: int = 1) -> float:
        """
        Estima tempo necessário para scrapear N perfis.
        
        Args:
            num_profiles: Número de perfis a scrapear
            num_ips: Número de IPs disponíveis
            
        Returns:
            Tempo estimado em horas
        """
        max_per_hour = self.get_theoretical_max_profiles_per_hour(num_ips)
        return num_profiles / max_per_hour if max_per_hour > 0 else float('inf')
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte configuração para dicionário"""
        return {
            'mode': self.mode.value,
            'requests_per_hour_per_ip': self.requests_per_hour_per_ip,
            'requests_per_minute': self.requests_per_minute,
            'min_delay_seconds': self.min_delay_seconds,
            'max_delay_seconds': self.max_delay_seconds,
            'delay_jitter_percent': self.delay_jitter_percent,
            'fingerprint_rotate_every': self.fingerprint_rotate_every,
            'sticky_session_minutes': self.sticky_session_minutes,
            'proxy_rotate_every': self.proxy_rotate_every,
            'backoff_initial': self.backoff_initial,
            'backoff_multiplier': self.backoff_multiplier,
            'backoff_max': self.backoff_max,
            'block_datacenter_ips': self.block_datacenter_ips,
            'warn_non_residential_ips': self.warn_non_residential_ips,
            'check_ip_quality': self.check_ip_quality,
        }
    
    def __str__(self) -> str:
        return (
            f"ScrapingConfig(mode={self.mode.value}, "
            f"{self.requests_per_hour_per_ip}req/h, "
            f"delay={self.min_delay_seconds}-{self.max_delay_seconds}s)"
        )


# =============================================================================
# INSTÂNCIA GLOBAL PADRÃO
# =============================================================================

# Configuração padrão usada pelo sistema
DEFAULT_CONFIG = ScrapingConfig.get_balanced_config()


def get_config(mode: Optional[str] = None) -> ScrapingConfig:
    """
    Obtém configuração de scraping.
    
    Args:
        mode: Modo desejado ('safe', 'balanced', 'aggressive', 'stealth')
              Se None, retorna a configuração padrão (balanced)
              
    Returns:
        ScrapingConfig configurado
    """
    if mode is None:
        return DEFAULT_CONFIG
    
    mode_lower = mode.lower()
    
    if mode_lower == 'safe':
        return ScrapingConfig.get_safe_config()
    elif mode_lower == 'balanced':
        return ScrapingConfig.get_balanced_config()
    elif mode_lower == 'aggressive':
        return ScrapingConfig.get_aggressive_config()
    elif mode_lower == 'stealth':
        return ScrapingConfig.get_stealth_config()
    else:
        logger.warning(f"Modo desconhecido: {mode}. Usando 'balanced'.")
        return ScrapingConfig.get_balanced_config()


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    print("🧪 Testando ScrapingConfig...")
    
    configs = [
        ScrapingConfig.get_safe_config(),
        ScrapingConfig.get_balanced_config(),
        ScrapingConfig.get_aggressive_config(),
        ScrapingConfig.get_stealth_config(),
    ]
    
    for config in configs:
        print(f"\n{config}")
        print(f"   Máx perfis/hora (1 IP): {config.get_theoretical_max_profiles_per_hour(1)}")
        print(f"   Máx perfis/hora (10 IPs): {config.get_theoretical_max_profiles_per_hour(10)}")
        print(f"   Tempo para 1000 perfis (10 IPs): {config.estimate_time_for_profiles(1000, 10):.2f}h")
        print(f"   Delay exemplo: {config.get_random_delay():.2f}s")
    
    print("\n✅ Teste concluído!")
