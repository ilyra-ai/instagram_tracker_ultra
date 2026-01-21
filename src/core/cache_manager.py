"""
Cache Manager - Sistema de Cache Inteligente para Instagram Intelligence System
Implementa cache hierárquico L1 (memória) + L2 (disco) com backoff exponencial.

Autor: Instagram Intelligence System 2026
Versão: 1.0.0
"""

import time
import hashlib
import logging
import functools
import random
from typing import Any, Callable, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path

# Tenacity para retry com backoff
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Diskcache para cache L2 (disco)
try:
    import diskcache
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False
    diskcache = None

logger = logging.getLogger(__name__)


class CacheEntry:
    """Representa uma entrada no cache com TTL"""
    
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = datetime.now()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou"""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)
    
    def time_remaining(self) -> float:
        """Retorna segundos restantes até expiração"""
        expiry = self.created_at + timedelta(seconds=self.ttl)
        remaining = (expiry - datetime.now()).total_seconds()
        return max(0, remaining)


class CacheManager:
    """
    Gerenciador de Cache Hierárquico
    
    L1: Cache em memória (dict) - Ultra rápido, volátil
    L2: Cache em disco (diskcache) - Persistente, mais lento
    
    Estratégia:
    1. Verificar L1 primeiro
    2. Se não encontrar, verificar L2
    3. Se encontrar em L2, promover para L1
    4. Se não encontrar, executar função e cachear
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, cache_dir: str = ".cache", l1_max_size: int = 1000):
        """
        Inicializa o gerenciador de cache
        
        Args:
            cache_dir: Diretório para cache L2
            l1_max_size: Número máximo de itens em L1
        """
        if self._initialized:
            return
            
        self._initialized = True
        self.l1_cache: Dict[str, CacheEntry] = {}
        self.l1_max_size = l1_max_size
        self.cache_dir = Path(cache_dir)
        
        # Inicializar L2 (disco)
        if DISKCACHE_AVAILABLE:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.l2_cache = diskcache.Cache(str(self.cache_dir), size_limit=500 * 1024 * 1024)  # 500MB
            logger.info(f"📦 Cache L2 inicializado em {self.cache_dir}")
        else:
            self.l2_cache = None
            logger.warning("⚠️ diskcache não disponível. Apenas cache L1 ativo.")
        
        # Estatísticas
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'misses': 0,
            'sets': 0
        }
        
        logger.info("✅ CacheManager inicializado")
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Gera uma chave única baseada na função e argumentos"""
        # Serializar argumentos de forma segura
        key_parts = [func_name]
        
        for arg in args:
            if hasattr(arg, '__dict__'):
                key_parts.append(str(id(type(arg))))  # Para objetos, usar tipo
            else:
                key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache (L1 primeiro, depois L2)
        
        Returns:
            Valor cacheado ou None se não encontrado/expirado
        """
        # Verificar L1
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if not entry.is_expired():
                self.stats['l1_hits'] += 1
                logger.debug(f"🎯 L1 HIT: {key[:8]}...")
                return entry.value
            else:
                # Expirado, remover
                del self.l1_cache[key]
        
        # Verificar L2
        if self.l2_cache is not None:
            try:
                value = self.l2_cache.get(key)
                if value is not None:
                    self.stats['l2_hits'] += 1
                    logger.debug(f"💾 L2 HIT: {key[:8]}...")
                    # Promover para L1
                    self._promote_to_l1(key, value, ttl=300)  # 5 min default para promoção
                    return value
            except Exception as e:
                logger.error(f"Erro ao ler L2: {e}")
        
        self.stats['misses'] += 1
        logger.debug(f"❌ MISS: {key[:8]}...")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 600) -> None:
        """
        Armazena valor no cache (L1 e L2)
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Time-to-live em segundos (default: 10 minutos)
        """
        # Armazenar em L1
        self._set_l1(key, value, ttl)
        
        # Armazenar em L2
        if self.l2_cache is not None:
            try:
                self.l2_cache.set(key, value, expire=ttl)
            except Exception as e:
                logger.error(f"Erro ao gravar L2: {e}")
        
        self.stats['sets'] += 1
        logger.debug(f"✅ SET: {key[:8]}... (TTL: {ttl}s)")
    
    def _set_l1(self, key: str, value: Any, ttl: int) -> None:
        """Armazena em L1 com controle de tamanho"""
        # Se L1 está cheio, remover entradas mais antigas/expiradas
        if len(self.l1_cache) >= self.l1_max_size:
            self._evict_l1()
        
        self.l1_cache[key] = CacheEntry(value, ttl)
    
    def _promote_to_l1(self, key: str, value: Any, ttl: int) -> None:
        """Promove valor de L2 para L1"""
        self._set_l1(key, value, ttl)
    
    def _evict_l1(self) -> None:
        """Remove entradas expiradas ou mais antigas de L1"""
        # Primeiro, remover expiradas
        expired_keys = [k for k, v in self.l1_cache.items() if v.is_expired()]
        for key in expired_keys:
            del self.l1_cache[key]
        
        # Se ainda está cheio, remover 20% mais antigas
        if len(self.l1_cache) >= self.l1_max_size:
            sorted_entries = sorted(
                self.l1_cache.items(),
                key=lambda x: x[1].created_at
            )
            to_remove = len(sorted_entries) // 5  # 20%
            for key, _ in sorted_entries[:to_remove]:
                del self.l1_cache[key]
    
    def invalidate(self, key: str) -> None:
        """Remove entrada específica do cache"""
        if key in self.l1_cache:
            del self.l1_cache[key]
        
        if self.l2_cache is not None:
            try:
                self.l2_cache.delete(key)
            except Exception:
                pass
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Remove entradas que contêm o padrão na chave"""
        count = 0
        
        # L1
        keys_to_remove = [k for k in self.l1_cache if pattern in k]
        for key in keys_to_remove:
            del self.l1_cache[key]
            count += 1
        
        # L2 não suporta pattern matching facilmente
        return count
    
    def clear_all(self) -> None:
        """Limpa todo o cache"""
        self.l1_cache.clear()
        
        if self.l2_cache is not None:
            try:
                self.l2_cache.clear()
            except Exception as e:
                logger.error(f"Erro ao limpar L2: {e}")
        
        logger.info("🗑️ Cache limpo completamente")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        total_requests = self.stats['l1_hits'] + self.stats['l2_hits'] + self.stats['misses']
        hit_rate = 0
        if total_requests > 0:
            hit_rate = (self.stats['l1_hits'] + self.stats['l2_hits']) / total_requests * 100
        
        return {
            **self.stats,
            'l1_size': len(self.l1_cache),
            'l2_available': self.l2_cache is not None,
            'hit_rate': f"{hit_rate:.1f}%",
            'total_requests': total_requests
        }


# Instância global do gerenciador
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Retorna instância global do gerenciador de cache"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(ttl: int = 600, key_prefix: str = ""):
    """
    Decorator para cachear resultados de funções
    
    Args:
        ttl: Time-to-live em segundos (default: 10 minutos)
        key_prefix: Prefixo opcional para a chave do cache
    
    Exemplo:
        @cached(ttl=300)
        def get_user_info(username):
            return api.fetch_user(username)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Gerar chave
            prefix = key_prefix or func.__name__
            cache_key = cache._generate_key(prefix, args, kwargs)
            
            # Verificar cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Executar função
            result = func(*args, **kwargs)
            
            # Cachear resultado (exceto None)
            if result is not None:
                cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cached_async(ttl: int = 600, key_prefix: str = ""):
    """
    Decorator para cachear resultados de funções assíncronas
    
    Args:
        ttl: Time-to-live em segundos
        key_prefix: Prefixo opcional para a chave do cache
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            prefix = key_prefix or func.__name__
            cache_key = cache._generate_key(prefix, args, kwargs)
            
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            
            if result is not None:
                cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def with_backoff_jitter(
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: float = 0.5
):
    """
    Decorator para retry com backoff exponencial e jitter estocástico
    
    Args:
        max_attempts: Número máximo de tentativas
        base_delay: Delay base em segundos
        max_delay: Delay máximo em segundos
        jitter: Fator de aleatoriedade (0.0 a 1.0)
    
    Fórmula: delay = min(max_delay, base_delay * 2^attempt) * (1 + random(-jitter, +jitter))
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        # Calcular delay com backoff exponencial
                        delay = min(max_delay, base_delay * (2 ** attempt))
                        
                        # Aplicar jitter estocástico
                        jitter_factor = 1 + random.uniform(-jitter, jitter)
                        delay *= jitter_factor
                        
                        logger.warning(
                            f"⚠️ Tentativa {attempt + 1}/{max_attempts} falhou. "
                            f"Retry em {delay:.2f}s... Erro: {e}"
                        )
                        time.sleep(delay)
            
            # Todas tentativas falharam
            logger.error(f"❌ Todas {max_attempts} tentativas falharam")
            raise last_exception
        
        return wrapper
    return decorator


def with_backoff_jitter_async(
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: float = 0.5
):
    """Versão assíncrona do decorator with_backoff_jitter"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        delay = min(max_delay, base_delay * (2 ** attempt))
                        jitter_factor = 1 + random.uniform(-jitter, jitter)
                        delay *= jitter_factor
                        
                        logger.warning(
                            f"⚠️ Tentativa {attempt + 1}/{max_attempts} falhou. "
                            f"Retry em {delay:.2f}s... Erro: {e}"
                        )
                        await asyncio.sleep(delay)
            
            logger.error(f"❌ Todas {max_attempts} tentativas falharam")
            raise last_exception
        
        return wrapper
    return decorator


# Decorator usando tenacity (alternativa mais robusta)
def with_tenacity_retry(
    max_attempts: int = 5,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator usando tenacity para retry robusto
    
    Args:
        max_attempts: Número máximo de tentativas
        min_wait: Tempo mínimo de espera (segundos)
        max_wait: Tempo máximo de espera (segundos)
        exceptions: Tupla de exceções para retry
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=lambda retry_state: logger.warning(
            f"⚠️ Retry {retry_state.attempt_number}/{max_attempts} "
            f"após {retry_state.outcome.exception()}"
        )
    )


if __name__ == "__main__":
    # Teste do CacheManager
    logging.basicConfig(level=logging.DEBUG)
    
    cache = get_cache_manager()
    
    # Teste básico
    cache.set("test_key", {"data": "valor"}, ttl=60)
    result = cache.get("test_key")
    print(f"Resultado: {result}")
    
    # Teste do decorator
    @cached(ttl=30)
    def fetch_data(user_id: int):
        print(f"Buscando dados do usuário {user_id}...")
        return {"id": user_id, "name": f"User {user_id}"}
    
    # Primeira chamada (cache miss)
    data1 = fetch_data(123)
    print(f"Primeira chamada: {data1}")
    
    # Segunda chamada (cache hit)
    data2 = fetch_data(123)
    print(f"Segunda chamada: {data2}")
    
    # Estatísticas
    print(f"\nEstatísticas: {cache.get_stats()}")
    
    # Teste backoff
    @with_backoff_jitter(max_attempts=3, base_delay=0.5)
    def failing_function():
        raise ValueError("Simulando erro")
    
    try:
        failing_function()
    except ValueError:
        print("Função falhou após todas tentativas (esperado)")
