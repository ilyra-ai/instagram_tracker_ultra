"""
Anti-Detecção Avançada 2026 - Módulo de Evasão de Fingerprinting
Versão God Mode Ultimate - Implementação REAL sem placeholders

Funcionalidades:
- JA4+ Fingerprinting com suporte a HTTP/3 e QUIC
- Canvas & WebGL Fingerprint Spoofing
- Behavioral Analysis Evasion (curvas de Bézier, Poisson delays)
- HTTP/2 Header Consistency
- CDP Detection Evasion
"""

import asyncio
import random
import math
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging


# =============================================================================
# CONFIGURAÇÃO DE LOGGING
# =============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AntiDetection")


# =============================================================================
# CLASSES DE DADOS
# =============================================================================

class BrowserType(Enum):
    """Tipos de navegadores suportados para fingerprinting"""
    CHROME_143 = "chrome143"
    CHROME_144 = "chrome144"
    CHROME_145 = "chrome145"
    SAFARI_18 = "safari18"
    SAFARI_18_1 = "safari18_1"
    EDGE_130 = "edge130"
    EDGE_131 = "edge131"
    FIREFOX_121 = "firefox121"
    FIREFOX_122 = "firefox122"


class ProtocolType(Enum):
    """Tipos de protocolo para JA4"""
    TCP = "t"
    QUIC = "q"
    HTTP3 = "q"


@dataclass
class JA4Fingerprint:
    """
    Estrutura de fingerprint JA4/JA4+
    
    JA4 é o sucessor do JA3, com melhor ordenação e suporte a HTTP/3.
    Formato: protocolo_versaoTLS_SNI_cipherSuites_extensoes_ALPN
    """
    protocol: ProtocolType
    tls_version: str
    sni: str  # 'd' para domain SNI, 'i' para IP
    cipher_count: int
    extension_count: int
    alpn: str  # "h2" ou "h1" ou "h3"
    cipher_suites: List[str] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)
    
    def to_string(self) -> str:
        """Gera string JA4 no formato padronizado"""
        # Formato: t13d1516h2_hash1_hash2
        base = f"{self.protocol.value}{self.tls_version}{self.sni}{self.cipher_count:02d}{self.extension_count:02d}{self.alpn}"
        
        # Hash truncado dos cipher suites (ordenados alfabeticamente - método JA4)
        sorted_ciphers = sorted(self.cipher_suites)
        cipher_hash = hashlib.sha256(",".join(sorted_ciphers).encode()).hexdigest()[:12]
        
        # Hash truncado das extensões (ordenadas alfabeticamente - método JA4)
        sorted_extensions = sorted(self.extensions)
        ext_hash = hashlib.sha256(",".join(sorted_extensions).encode()).hexdigest()[:12]
        
        return f"{base}_{cipher_hash}_{ext_hash}"


@dataclass
class BrowserProfile:
    """
    Perfil completo de navegador para fingerprinting consistente.
    
    Inclui todas as características que devem ser consistentes:
    - User-Agent
    - Sec-Ch-UA headers
    - Screen/window dimensions
    - Canvas fingerprint seed
    - WebGL parameters
    - Audio context parameters
    """
    browser_type: BrowserType
    user_agent: str
    sec_ch_ua: str
    sec_ch_ua_mobile: str
    sec_ch_ua_platform: str
    screen_width: int
    screen_height: int
    color_depth: int
    pixel_ratio: float
    canvas_seed: int
    webgl_vendor: str
    webgl_renderer: str
    audio_sample_rate: int
    timezone: str
    language: str
    languages: List[str]
    platform: str
    hardware_concurrency: int
    device_memory: int
    ja4_fingerprint: JA4Fingerprint


# =============================================================================
# JA4+ FINGERPRINT MANAGER
# =============================================================================

class JA4FingerprintManager:
    """
    Gerenciador de fingerprints JA4/JA4+ para 2026.
    
    Implementa:
    - Ordenação alfabética de extensões TLS (método JA4)
    - Suporte a ALPN values (h2, http/1.1, h3)
    - Distinção entre TCP e QUIC/HTTP3
    - Mapeamento JA4+ com dados de camada de aplicação
    """
    
    # Pool de fingerprints JA4 baseados em navegadores reais de Janeiro 2026
    JA4_POOL = {
        BrowserType.CHROME_143: JA4Fingerprint(
            protocol=ProtocolType.TCP,
            tls_version="13",
            sni="d",
            cipher_count=16,
            extension_count=15,
            alpn="h2",
            cipher_suites=[
                "1301", "1302", "1303", "c02b", "c02f",
                "c02c", "c030", "cca9", "cca8", "c013",
                "c014", "009c", "009d", "002f", "0035", "000a"
            ],
            extensions=[
                "0000", "0017", "ff01", "000a", "000b",
                "0023", "0010", "0005", "000d", "002b",
                "002d", "001c", "001b", "0033", "0015"
            ]
        ),
        BrowserType.CHROME_144: JA4Fingerprint(
            protocol=ProtocolType.TCP,
            tls_version="13",
            sni="d",
            cipher_count=16,
            extension_count=16,
            alpn="h2",
            cipher_suites=[
                "1301", "1302", "1303", "c02b", "c02f",
                "c02c", "c030", "cca9", "cca8", "c013",
                "c014", "009c", "009d", "002f", "0035", "000a"
            ],
            extensions=[
                "0000", "0017", "ff01", "000a", "000b",
                "0023", "0010", "0005", "000d", "002b",
                "002d", "001c", "001b", "0033", "0015", "0045"
            ]
        ),
        BrowserType.CHROME_145: JA4Fingerprint(
            protocol=ProtocolType.QUIC,
            tls_version="13",
            sni="d",
            cipher_count=16,
            extension_count=17,
            alpn="h3",
            cipher_suites=[
                "1301", "1302", "1303", "c02b", "c02f",
                "c02c", "c030", "cca9", "cca8", "c013",
                "c014", "009c", "009d", "002f", "0035", "000a"
            ],
            extensions=[
                "0000", "0017", "ff01", "000a", "000b",
                "0023", "0010", "0005", "000d", "002b",
                "002d", "001c", "001b", "0033", "0015", "0045", "0039"
            ]
        ),
        BrowserType.SAFARI_18: JA4Fingerprint(
            protocol=ProtocolType.TCP,
            tls_version="13",
            sni="d",
            cipher_count=12,
            extension_count=11,
            alpn="h2",
            cipher_suites=[
                "1301", "1302", "1303", "c02c", "c02b",
                "00a3", "009f", "ccaa", "c030", "c02f",
                "009e", "c024"
            ],
            extensions=[
                "0000", "0017", "ff01", "000a", "000b",
                "0023", "0010", "000d", "002b", "002d", "0033"
            ]
        ),
        BrowserType.EDGE_130: JA4Fingerprint(
            protocol=ProtocolType.TCP,
            tls_version="13",
            sni="d",
            cipher_count=15,
            extension_count=14,
            alpn="h2",
            cipher_suites=[
                "1301", "1302", "1303", "c02b", "c02f",
                "c02c", "c030", "cca9", "cca8", "c013",
                "c014", "009c", "009d", "002f", "0035"
            ],
            extensions=[
                "0000", "0017", "ff01", "000a", "000b",
                "0023", "0010", "0005", "000d", "002b",
                "002d", "001c", "001b", "0033"
            ]
        ),
    }
    
    def __init__(self):
        self.current_fingerprint: Optional[JA4Fingerprint] = None
        self.rotation_count = 0
    
    def get_fingerprint(self, browser_type: BrowserType) -> JA4Fingerprint:
        """Retorna o fingerprint JA4 para o tipo de navegador"""
        return self.JA4_POOL.get(browser_type, list(self.JA4_POOL.values())[0])
    
    def get_ja4_string(self, browser_type: BrowserType) -> str:
        """Retorna a string JA4 formatada"""
        fp = self.get_fingerprint(browser_type)
        return fp.to_string()
    
    def get_ja4_plus_data(self, browser_type: BrowserType) -> Dict[str, Any]:
        """
        Retorna dados JA4+ completos incluindo camada de aplicação.
        
        JA4+ inclui:
        - JA4 base
        - HTTP headers hasheados
        - Cookie patterns
        """
        fp = self.get_fingerprint(browser_type)
        
        return {
            'ja4': fp.to_string(),
            'ja4_protocol': fp.protocol.value,
            'ja4_tls_version': fp.tls_version,
            'ja4_alpn': fp.alpn,
            'cipher_count': fp.cipher_count,
            'extension_count': fp.extension_count,
        }
    
    def rotate(self) -> JA4Fingerprint:
        """Rotaciona para um novo fingerprint aleatório"""
        self.rotation_count += 1
        browser_types = list(self.JA4_POOL.keys())
        selected = random.choice(browser_types)
        self.current_fingerprint = self.get_fingerprint(selected)
        logger.info(f"🔄 JA4 rotacionado para {selected.value} (#{self.rotation_count})")
        return self.current_fingerprint


# =============================================================================
# BROWSER PROFILE MANAGER
# =============================================================================

class BrowserProfileManager:
    """
    Gerenciador de perfis de navegador para fingerprinting consistente.
    
    Garante que todas as características do navegador sejam consistentes
    entre si para evitar detecção por inconsistência.
    """
    
    PROFILES = {
        BrowserType.CHROME_143: BrowserProfile(
            browser_type=BrowserType.CHROME_143,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            sec_ch_ua='"Chromium";v="143", "Google Chrome";v="143", "Not(A:Brand";v="99"',
            sec_ch_ua_mobile="?0",
            sec_ch_ua_platform='"Windows"',
            screen_width=1920,
            screen_height=1080,
            color_depth=24,
            pixel_ratio=1.0,
            canvas_seed=0x7F3A9B2C,
            webgl_vendor="Google Inc. (NVIDIA Corporation)",
            webgl_renderer="ANGLE (NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
            audio_sample_rate=44100,
            timezone="America/Sao_Paulo",
            language="pt-BR",
            languages=["pt-BR", "pt", "en-US", "en"],
            platform="Win32",
            hardware_concurrency=8,
            device_memory=8,
            ja4_fingerprint=JA4FingerprintManager.JA4_POOL[BrowserType.CHROME_143]
        ),
        BrowserType.CHROME_144: BrowserProfile(
            browser_type=BrowserType.CHROME_144,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            sec_ch_ua='"Chromium";v="144", "Google Chrome";v="144", "Not(A:Brand";v="99"',
            sec_ch_ua_mobile="?0",
            sec_ch_ua_platform='"Windows"',
            screen_width=2560,
            screen_height=1440,
            color_depth=24,
            pixel_ratio=1.25,
            canvas_seed=0x5E8D1C4A,
            webgl_vendor="Google Inc. (NVIDIA Corporation)",
            webgl_renderer="ANGLE (NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0)",
            audio_sample_rate=48000,
            timezone="America/Sao_Paulo",
            language="pt-BR",
            languages=["pt-BR", "pt", "en-US", "en"],
            platform="Win32",
            hardware_concurrency=16,
            device_memory=16,
            ja4_fingerprint=JA4FingerprintManager.JA4_POOL[BrowserType.CHROME_144]
        ),
        BrowserType.SAFARI_18: BrowserProfile(
            browser_type=BrowserType.SAFARI_18,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
            sec_ch_ua='"Safari";v="18", "Not A(Brand";v="99"',
            sec_ch_ua_mobile="?0",
            sec_ch_ua_platform='"macOS"',
            screen_width=2560,
            screen_height=1600,
            color_depth=30,
            pixel_ratio=2.0,
            canvas_seed=0x9A7B3E5F,
            webgl_vendor="Apple Inc.",
            webgl_renderer="Apple M2 Pro",
            audio_sample_rate=44100,
            timezone="America/Sao_Paulo",
            language="pt-BR",
            languages=["pt-BR", "pt", "en-US", "en"],
            platform="MacIntel",
            hardware_concurrency=10,
            device_memory=16,
            ja4_fingerprint=JA4FingerprintManager.JA4_POOL[BrowserType.SAFARI_18]
        ),
        BrowserType.EDGE_130: BrowserProfile(
            browser_type=BrowserType.EDGE_130,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
            sec_ch_ua='"Microsoft Edge";v="130", "Chromium";v="130", "Not(A:Brand";v="99"',
            sec_ch_ua_mobile="?0",
            sec_ch_ua_platform='"Windows"',
            screen_width=1920,
            screen_height=1200,
            color_depth=24,
            pixel_ratio=1.0,
            canvas_seed=0x3C5F8D2A,
            webgl_vendor="Google Inc. (Intel)",
            webgl_renderer="ANGLE (Intel, Intel(R) UHD Graphics 770 Direct3D11 vs_5_0 ps_5_0)",
            audio_sample_rate=48000,
            timezone="America/Sao_Paulo",
            language="pt-BR",
            languages=["pt-BR", "pt", "en-US", "en"],
            platform="Win32",
            hardware_concurrency=12,
            device_memory=32,
            ja4_fingerprint=JA4FingerprintManager.JA4_POOL[BrowserType.EDGE_130]
        ),
    }
    
    def __init__(self):
        self.current_profile: Optional[BrowserProfile] = None
    
    def get_profile(self, browser_type: BrowserType) -> BrowserProfile:
        """Obtém perfil para o tipo de navegador"""
        return self.PROFILES.get(browser_type, list(self.PROFILES.values())[0])
    
    def get_random_profile(self) -> BrowserProfile:
        """Obtém um perfil aleatório"""
        browser_type = random.choice(list(self.PROFILES.keys()))
        self.current_profile = self.get_profile(browser_type)
        return self.current_profile
    
    def get_consistent_headers(self, profile: BrowserProfile) -> Dict[str, str]:
        """
        Gera headers HTTP completamente consistentes com o perfil.
        
        Garante que:
        - User-Agent corresponde ao Sec-Ch-UA
        - Accept-Language corresponde ao language do perfil
        - Todos os Sec-* headers são consistentes
        """
        return {
            'User-Agent': profile.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': ','.join([f"{profile.languages[0]}" if i == 0 else f"{l};q={0.9-i*0.1:.1f}" for i, l in enumerate(profile.languages)]),
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'sec-ch-ua': profile.sec_ch_ua,
            'sec-ch-ua-mobile': profile.sec_ch_ua_mobile,
            'sec-ch-ua-platform': profile.sec_ch_ua_platform,
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
        }


# =============================================================================
# CANVAS & WEBGL FINGERPRINT SPOOFING
# =============================================================================

class CanvasWebGLSpoofer:
    """
    Spoofing de Canvas e WebGL fingerprints.
    
    Implementa:
    - Canvas fingerprint spoofing com ruído determinístico
    - WebGL parameter injection
    - Perfis de rendering consistentes (não randomizados)
    - Audio Context fingerprint spoofing
    """
    
    def __init__(self, profile: Optional[BrowserProfile] = None):
        self.profile = profile
        self.canvas_noise_seed = profile.canvas_seed if profile else random.randint(0, 0xFFFFFFFF)
    
    def get_canvas_spoof_script(self) -> str:
        """
        Gera script JavaScript para spoofing de Canvas fingerprint.
        
        O ruído é determinístico baseado no seed para manter consistência.
        """
        seed = self.canvas_noise_seed
        
        return f"""
        (function() {{
            // Seed para ruído determinístico
            const seed = {seed};
            
            // Gerador de números pseudo-aleatórios determinístico (Mulberry32)
            function mulberry32(a) {{
                return function() {{
                    let t = a += 0x6D2B79F5;
                    t = Math.imul(t ^ t >>> 15, t | 1);
                    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
                    return ((t ^ t >>> 14) >>> 0) / 4294967296;
                }}
            }}
            
            const random = mulberry32(seed);
            
            // Override toDataURL
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type, quality) {{
                const ctx = this.getContext('2d');
                if (ctx) {{
                    const imageData = ctx.getImageData(0, 0, this.width, this.height);
                    const data = imageData.data;
                    
                    // Adicionar ruído imperceptível mas determinístico
                    for (let i = 0; i < data.length; i += 4) {{
                        // Modificar apenas canal alpha levemente
                        const noise = Math.floor((random() - 0.5) * 2);
                        data[i + 3] = Math.max(0, Math.min(255, data[i + 3] + noise));
                    }}
                    
                    ctx.putImageData(imageData, 0, 0);
                }}
                return originalToDataURL.apply(this, arguments);
            }};
            
            // Override toBlob
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {{
                const ctx = this.getContext('2d');
                if (ctx) {{
                    const imageData = ctx.getImageData(0, 0, this.width, this.height);
                    const data = imageData.data;
                    
                    for (let i = 0; i < data.length; i += 4) {{
                        const noise = Math.floor((random() - 0.5) * 2);
                        data[i + 3] = Math.max(0, Math.min(255, data[i + 3] + noise));
                    }}
                    
                    ctx.putImageData(imageData, 0, 0);
                }}
                return originalToBlob.apply(this, arguments);
            }};
            
            // Override getImageData
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function() {{
                const imageData = originalGetImageData.apply(this, arguments);
                const data = imageData.data;
                
                for (let i = 0; i < data.length; i += 4) {{
                    const noise = Math.floor((random() - 0.5) * 2);
                    data[i + 3] = Math.max(0, Math.min(255, data[i + 3] + noise));
                }}
                
                return imageData;
            }};
            
            console.log('[AntiDetection] Canvas fingerprint spoofing ativado');
        }})();
        """
    
    def get_webgl_spoof_script(self) -> str:
        """
        Gera script JavaScript para spoofing de WebGL fingerprint.
        
        Mascara informações de GPU e parâmetros WebGL.
        """
        vendor = self.profile.webgl_vendor if self.profile else "Google Inc. (NVIDIA Corporation)"
        renderer = self.profile.webgl_renderer if self.profile else "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)"
        
        return f"""
        (function() {{
            // WebGL Vendor e Renderer spoofing
            const vendor = "{vendor}";
            const renderer = "{renderer}";
            
            // Override getParameter para WebGL
            const getParameterProxyHandler = {{
                apply: function(target, thisArg, argumentsList) {{
                    const param = argumentsList[0];
                    
                    // UNMASKED_VENDOR_WEBGL
                    if (param === 37445) {{
                        return vendor;
                    }}
                    
                    // UNMASKED_RENDERER_WEBGL
                    if (param === 37446) {{
                        return renderer;
                    }}
                    
                    return Reflect.apply(target, thisArg, argumentsList);
                }}
            }};
            
            // Aplicar para WebGL1
            if (typeof WebGLRenderingContext !== 'undefined') {{
                WebGLRenderingContext.prototype.getParameter = new Proxy(
                    WebGLRenderingContext.prototype.getParameter,
                    getParameterProxyHandler
                );
            }}
            
            // Aplicar para WebGL2
            if (typeof WebGL2RenderingContext !== 'undefined') {{
                WebGL2RenderingContext.prototype.getParameter = new Proxy(
                    WebGL2RenderingContext.prototype.getParameter,
                    getParameterProxyHandler
                );
            }}
            
            // Override getExtension para debug renderer info
            const originalGetExtension = WebGLRenderingContext.prototype.getExtension;
            WebGLRenderingContext.prototype.getExtension = function(name) {{
                if (name === 'WEBGL_debug_renderer_info') {{
                    return {{
                        UNMASKED_VENDOR_WEBGL: 37445,
                        UNMASKED_RENDERER_WEBGL: 37446
                    }};
                }}
                return originalGetExtension.apply(this, arguments);
            }};
            
            console.log('[AntiDetection] WebGL fingerprint spoofing ativado');
        }})();
        """
    
    def get_audio_spoof_script(self) -> str:
        """
        Gera script JavaScript para spoofing de AudioContext fingerprint.
        """
        sample_rate = self.profile.audio_sample_rate if self.profile else 44100
        
        return f"""
        (function() {{
            const targetSampleRate = {sample_rate};
            
            // Override AudioContext
            const originalAudioContext = window.AudioContext || window.webkitAudioContext;
            
            if (originalAudioContext) {{
                window.AudioContext = window.webkitAudioContext = function(options) {{
                    const ctx = new originalAudioContext(options);
                    
                    // Spoofar sampleRate
                    Object.defineProperty(ctx, 'sampleRate', {{
                        get: function() {{ return targetSampleRate; }}
                    }});
                    
                    return ctx;
                }};
                
                // Manter prototype
                window.AudioContext.prototype = originalAudioContext.prototype;
            }}
            
            // Override OfflineAudioContext para fingerprinting via oscillator
            const originalOfflineAudioContext = window.OfflineAudioContext || window.webkitOfflineAudioContext;
            
            if (originalOfflineAudioContext) {{
                window.OfflineAudioContext = window.webkitOfflineAudioContext = function(channels, length, sampleRate) {{
                    return new originalOfflineAudioContext(channels, length, targetSampleRate);
                }};
            }}
            
            console.log('[AntiDetection] Audio fingerprint spoofing ativado');
        }})();
        """
    
    def get_all_spoof_scripts(self) -> str:
        """Retorna todos os scripts de spoofing combinados"""
        return f"""
        {self.get_canvas_spoof_script()}
        {self.get_webgl_spoof_script()}
        {self.get_audio_spoof_script()}
        """


# =============================================================================
# BEHAVIORAL ANALYSIS EVASION
# =============================================================================

class BehavioralEvasion:
    """
    Evasão de análise comportamental.
    
    Implementa:
    - Curvas de Bézier para movimento de mouse realista
    - Variação estocástica em typing speed (distribuição normal)
    - Scrolling patterns naturais com aceleração/desaceleração
    - Delays com distribuição de Poisson
    - Micro-movimentos de mouse
    - Padrões de leitura humana
    """
    
    def __init__(self, randomness_factor: float = 0.3):
        """
        Inicializa o módulo de evasão comportamental.
        
        Args:
            randomness_factor: Fator de aleatoriedade (0.0 a 1.0)
        """
        self.randomness_factor = randomness_factor
    
    # -------------------------------------------------------------------------
    # CURVAS DE BÉZIER PARA MOVIMENTO DE MOUSE
    # -------------------------------------------------------------------------
    
    def generate_bezier_path(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        num_points: int = 50,
        control_point_variation: float = 0.3
    ) -> List[Tuple[float, float]]:
        """
        Gera caminho de movimento do mouse usando curvas de Bézier cúbicas.
        
        Simula movimento humano natural com aceleração/desaceleração.
        
        Args:
            start: Ponto inicial (x, y)
            end: Ponto final (x, y)
            num_points: Número de pontos no caminho
            control_point_variation: Variação dos pontos de controle
            
        Returns:
            Lista de coordenadas (x, y) do caminho
        """
        x0, y0 = start
        x3, y3 = end
        
        # Calcular distância
        distance = math.sqrt((x3 - x0) ** 2 + (y3 - y0) ** 2)
        
        # Gerar pontos de controle com variação natural
        # Ponto de controle 1: mais próximo do início
        variation1 = control_point_variation * distance * random.uniform(0.5, 1.5)
        angle1 = math.atan2(y3 - y0, x3 - x0) + random.uniform(-0.5, 0.5)
        x1 = x0 + variation1 * math.cos(angle1)
        y1 = y0 + variation1 * math.sin(angle1)
        
        # Ponto de controle 2: mais próximo do fim
        variation2 = control_point_variation * distance * random.uniform(0.5, 1.5)
        angle2 = math.atan2(y0 - y3, x0 - x3) + random.uniform(-0.5, 0.5)
        x2 = x3 + variation2 * math.cos(angle2)
        y2 = y3 + variation2 * math.sin(angle2)
        
        # Gerar pontos na curva de Bézier
        path = []
        for i in range(num_points):
            t = i / (num_points - 1)
            
            # Fórmula da curva de Bézier cúbica
            x = (1-t)**3 * x0 + 3*(1-t)**2 * t * x1 + 3*(1-t) * t**2 * x2 + t**3 * x3
            y = (1-t)**3 * y0 + 3*(1-t)**2 * t * y1 + 3*(1-t) * t**2 * y2 + t**3 * y3
            
            # Adicionar micro-variação para parecer mais humano
            x += random.gauss(0, 0.5)
            y += random.gauss(0, 0.5)
            
            path.append((x, y))
        
        return path
    
    def generate_micro_movements(
        self,
        center: Tuple[float, float],
        duration_ms: int = 500,
        amplitude: float = 3.0
    ) -> List[Tuple[float, float, int]]:
        """
        Gera micro-movimentos do mouse (tremor natural).
        
        Simula o tremor natural da mão humana.
        
        Args:
            center: Ponto central dos movimentos
            duration_ms: Duração em milissegundos
            amplitude: Amplitude máxima dos movimentos
            
        Returns:
            Lista de (x, y, delay_ms)
        """
        movements = []
        elapsed = 0
        x, y = center
        
        while elapsed < duration_ms:
            # Movimento pequeno com distribuição normal
            dx = random.gauss(0, amplitude)
            dy = random.gauss(0, amplitude)
            
            # Novo ponto
            new_x = x + dx
            new_y = y + dy
            
            # Delay entre movimentos (20-50ms)
            delay = random.randint(20, 50)
            elapsed += delay
            
            movements.append((new_x, new_y, delay))
            
            # Retornar levemente ao centro
            x = center[0] + (new_x - center[0]) * 0.7
            y = center[1] + (new_y - center[1]) * 0.7
        
        return movements
    
    # -------------------------------------------------------------------------
    # TYPING COM DISTRIBUIÇÃO NORMAL
    # -------------------------------------------------------------------------
    
    def get_typing_delay(
        self,
        base_delay_ms: int = 100,
        variation_ms: int = 50
    ) -> int:
        """
        Retorna delay entre teclas com distribuição normal.
        
        Simula velocidade de digitação humana com variação natural.
        
        Args:
            base_delay_ms: Delay base em milissegundos
            variation_ms: Desvio padrão da variação
            
        Returns:
            Delay em milissegundos
        """
        delay = random.gauss(base_delay_ms, variation_ms)
        
        # Garantir mínimo e máximo razoáveis
        delay = max(30, min(300, delay))
        
        # Ocasionalmente adicionar pausa maior (como se pensando)
        if random.random() < 0.05:  # 5% de chance
            delay += random.randint(200, 500)
        
        return int(delay)
    
    def get_typing_delays_for_text(self, text: str) -> List[int]:
        """
        Gera lista de delays para digitar um texto.
        
        Considera padrões reais de digitação:
        - Letras comuns são mais rápidas
        - Shift + letra é mais lento
        - Espaço após palavra é mais lento
        """
        delays = []
        
        for i, char in enumerate(text):
            base_delay = 100
            
            # Letras comuns são mais rápidas
            if char.lower() in 'etaoinsrhldc':
                base_delay = 80
            
            # Números são mais lentos
            if char.isdigit():
                base_delay = 120
            
            # Símbolos são ainda mais lentos
            if char in '!@#$%^&*()_+-=[]{}|;:,./<>?':
                base_delay = 150
            
            # Maiúsculas são mais lentas (shift + tecla)
            if char.isupper():
                base_delay += 30
            
            # Espaço após palavra pode ter pausa
            if char == ' ' and random.random() < 0.3:
                base_delay += 100
            
            delay = self.get_typing_delay(base_delay, base_delay // 3)
            delays.append(delay)
        
        return delays
    
    # -------------------------------------------------------------------------
    # DELAYS COM DISTRIBUIÇÃO DE POISSON
    # -------------------------------------------------------------------------
    
    def get_poisson_delay(self, lambda_param: float = 2.0, scale: float = 1000.0) -> int:
        """
        Gera delay com distribuição de Poisson.
        
        Mais realista que delays uniformes para simular
        tempo de reação humana.
        
        Args:
            lambda_param: Parâmetro lambda da distribuição
            scale: Fator de escala em ms
            
        Returns:
            Delay em milissegundos
        """
        # Gerar valor Poisson
        L = math.exp(-lambda_param)
        k = 0
        p = 1.0
        
        while p > L:
            k += 1
            p *= random.random()
        
        delay_ms = (k - 1) * scale / lambda_param
        
        # Adicionar pequena variação
        delay_ms += random.uniform(-50, 50)
        
        return max(100, int(delay_ms))
    
    # -------------------------------------------------------------------------
    # SCROLLING NATURAL
    # -------------------------------------------------------------------------
    
    def generate_scroll_pattern(
        self,
        total_distance: int,
        scroll_speed: str = 'medium'
    ) -> List[Tuple[int, int]]:
        """
        Gera padrão de scroll natural com aceleração/desaceleração.
        
        Args:
            total_distance: Distância total a scrollar (pixels)
            scroll_speed: 'slow', 'medium', 'fast'
            
        Returns:
            Lista de (delta_pixels, delay_ms)
        """
        speed_multipliers = {
            'slow': 0.5,
            'medium': 1.0,
            'fast': 1.5
        }
        
        multiplier = speed_multipliers.get(scroll_speed, 1.0)
        
        scrolls = []
        remaining = total_distance
        position = 0
        progress = 0.0
        
        while remaining > 0:
            # Calcular fator de easing (ease-in-out)
            progress = 1 - (remaining / total_distance)
            
            # Ease-in-out cubic
            if progress < 0.5:
                easing = 4 * progress * progress * progress
            else:
                easing = 1 - pow(-2 * progress + 2, 3) / 2
            
            # Delta baseado no easing
            base_delta = random.randint(50, 150) * multiplier
            delta = int(base_delta * (0.3 + 0.7 * easing))
            
            # Não ultrapassar o restante
            delta = min(delta, remaining)
            
            # Delay variável
            delay = random.randint(30, 80)
            
            scrolls.append((delta, delay))
            remaining -= delta
        
        return scrolls
    
    # -------------------------------------------------------------------------
    # PADRÕES DE LEITURA
    # -------------------------------------------------------------------------
    
    def generate_reading_pauses(
        self,
        text_length: int,
        words_per_minute: int = 200
    ) -> List[int]:
        """
        Gera pausas de leitura baseadas em padrões de eye-tracking.
        
        Simula tempo que humano levaria para ler conteúdo.
        
        Args:
            text_length: Número de caracteres do texto
            words_per_minute: Velocidade de leitura
            
        Returns:
            Lista de pausas em ms em pontos de leitura
        """
        # Estimar número de palavras (média 5 caracteres/palavra)
        estimated_words = text_length / 5
        
        # Tempo total de leitura em ms
        total_time_ms = (estimated_words / words_per_minute) * 60 * 1000
        
        # Dividir em pausas naturais
        num_pauses = max(3, int(estimated_words / 10))
        
        pauses = []
        remaining_time = total_time_ms
        
        for i in range(num_pauses):
            # Pausas não uniformes (Poisson-like)
            if remaining_time > 0:
                pause = self.get_poisson_delay(lambda_param=2.0, scale=remaining_time / (num_pauses - i))
                pause = min(pause, remaining_time * 0.5)
                pauses.append(int(pause))
                remaining_time -= pause
        
        return pauses


# =============================================================================
# CDP DETECTION EVASION
# =============================================================================

class CDPEvasion:
    """
    Evasão de detecção de Chrome DevTools Protocol.
    
    Implementa:
    - Minimização de CDP calls detectáveis
    - Patching de Runtime.consoleAPICalled
    - Remoção de indicadores WebDriver
    - Stealth patches similares a puppeteer-stealth
    """
    
    @staticmethod
    def get_stealth_scripts() -> str:
        """
        Retorna scripts JavaScript para evasão de detecção CDP.
        
        Implementa técnicas similares ao puppeteer-extra-plugin-stealth.
        """
        return """
        (function() {
            'use strict';
            
            // =================================================================
            // 1. WEBDRIVER PROPERTY OVERRIDE
            // =================================================================
            
            // Deletar navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
            
            // Deletar window.webdriver
            delete window.webdriver;
            
            // Deletar document.webdriver
            delete document.webdriver;
            
            // =================================================================
            // 2. CHROME RUNTIME
            // =================================================================
            
            // Adicionar chrome.runtime fake
            if (!window.chrome) {
                window.chrome = {};
            }
            
            if (!window.chrome.runtime) {
                window.chrome.runtime = {
                    connect: function() { return {}; },
                    sendMessage: function() {},
                    onMessage: { addListener: function() {} },
                    id: undefined
                };
            }
            
            // =================================================================
            // 3. PERMISSIONS API
            // =================================================================
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = function(parameters) {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: Notification.permission });
                }
                return originalQuery.apply(this, arguments);
            };
            
            // =================================================================
            // 4. PLUGINS & MIMETYPES
            // =================================================================
            
            // Adicionar plugins fake se vazio
            if (navigator.plugins.length === 0) {
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                    ]
                });
            }
            
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => [
                    { type: 'application/pdf', suffixes: 'pdf', description: '' },
                    { type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format' }
                ]
            });
            
            // =================================================================
            // 5. LANGUAGES
            // =================================================================
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en']
            });
            
            // =================================================================
            // 6. HARDWARE CONCURRENCY
            // =================================================================
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            // =================================================================
            // 7. DEVICE MEMORY
            // =================================================================
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            
            // =================================================================
            // 8. CONNECTION
            // =================================================================
            
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                })
            });
            
            // =================================================================
            // 9. IFRAME CONTENTWINDOW
            // =================================================================
            
            // Fix para iframes headless
            try {
                const elementDescriptor = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
                Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                    get: function() {
                        const contentWindow = elementDescriptor.get.apply(this);
                        if (contentWindow && contentWindow.navigator) {
                            Object.defineProperty(contentWindow.navigator, 'webdriver', {
                                get: () => undefined
                            });
                        }
                        return contentWindow;
                    }
                });
            } catch (e) {}
            
            // =================================================================
            // 10. CONSOLE.DEBUG OVERRIDE
            // =================================================================
            
            // Mascarar outputs de debug automatizados
            const originalDebug = console.debug;
            console.debug = function(...args) {
                // Filtrar mensagens de automação
                const filtered = args.filter(arg => {
                    if (typeof arg === 'string') {
                        return !arg.includes('puppeteer') && 
                               !arg.includes('webdriver') &&
                               !arg.includes('automation') &&
                               !arg.includes('cdp');
                    }
                    return true;
                });
                if (filtered.length > 0) {
                    originalDebug.apply(console, filtered);
                }
            };
            
            // =================================================================
            // 11. STACK TRACE CLEANING
            // =================================================================
            
            // Limpar stack traces que revelem automação
            const originalError = Error;
            window.Error = function(...args) {
                const error = new originalError(...args);
                if (error.stack) {
                    error.stack = error.stack
                        .split('\\n')
                        .filter(line => !line.includes('puppeteer') && !line.includes('nodriver'))
                        .join('\\n');
                }
                return error;
            };
            window.Error.prototype = originalError.prototype;
            
            // =================================================================
            // 12. AUTOMATION INDICATOR REMOVAL
            // =================================================================
            
            // Remover qualquer indicador residual
            const automationIndicators = [
                '__webdriver_evaluate',
                '__selenium_evaluate',
                '__webdriver_script_function',
                '__webdriver_script_func',
                '__webdriver_script_fn',
                '__fxdriver_evaluate',
                '__driver_unwrapped',
                '__webdriver_unwrapped',
                '__driver_evaluate',
                '__selenium_unwrapped',
                '__fxdriver_unwrapped',
                '_Selenium_IDE_Recorder',
                '_selenium',
                'calledSelenium',
                '$chrome_asyncScriptInfo',
                '$cdc_asdjflasutopfhvcZLmcfl_',
                '$cdc_',
                'domAutomation',
                'domAutomationController'
            ];
            
            automationIndicators.forEach(indicator => {
                try {
                    if (window[indicator]) {
                        delete window[indicator];
                    }
                    if (document[indicator]) {
                        delete document[indicator];
                    }
                } catch (e) {}
            });
            
            console.log('[AntiDetection] CDP evasion scripts carregados');
        })();
        """
    
    @staticmethod
    def get_runtime_patch_script() -> str:
        """
        Script para patch de Runtime.consoleAPICalled.
        
        Impede que chamadas de console sejam usadas para fingerprinting.
        """
        return """
        (function() {
            // Interceptar e filtrar chamadas de console que podem ser usadas para detectar automação
            const consoleMethods = ['log', 'warn', 'error', 'info', 'debug', 'trace'];
            
            consoleMethods.forEach(method => {
                const original = console[method];
                console[method] = function(...args) {
                    // Filtrar argumentos que podem revelar automação
                    const safeArgs = args.map(arg => {
                        if (typeof arg === 'string') {
                            // Remover referências a ferramentas de automação
                            return arg
                                .replace(/puppeteer/gi, 'browser')
                                .replace(/playwright/gi, 'browser')
                                .replace(/selenium/gi, 'browser')
                                .replace(/webdriver/gi, 'driver')
                                .replace(/nodriver/gi, 'browser')
                                .replace(/cdp/gi, 'protocol');
                        }
                        return arg;
                    });
                    
                    return original.apply(console, safeArgs);
                };
            });
        })();
        """


# =============================================================================
# ANTI-DETECTION MANAGER - CLASSE PRINCIPAL
# =============================================================================

class AntiDetectionManager:
    """
    Gerenciador principal de anti-detecção.
    
    Integra todos os módulos:
    - JA4+ Fingerprinting
    - Canvas/WebGL Spoofing
    - Behavioral Evasion
    - CDP Evasion
    """
    
    def __init__(self, browser_type: Optional[BrowserType] = None):
        """
        Inicializa o gerenciador de anti-detecção.
        
        Args:
            browser_type: Tipo de navegador a simular
        """
        self.browser_type = browser_type or random.choice(list(BrowserType))
        
        # Inicializar componentes
        self.ja4_manager = JA4FingerprintManager()
        self.profile_manager = BrowserProfileManager()
        self.profile = self.profile_manager.get_profile(self.browser_type)
        self.canvas_spoofer = CanvasWebGLSpoofer(self.profile)
        self.behavioral = BehavioralEvasion()
        
        logger.info(f"🛡️ AntiDetectionManager inicializado")
        logger.info(f"   └── Perfil: {self.browser_type.value}")
    
    def get_all_injection_scripts(self) -> str:
        """
        Retorna todos os scripts de injeção combinados.
        
        Deve ser injetado na página antes de qualquer interação.
        """
        scripts = []
        
        # CDP Evasion (primeiro, para cobrir outros scripts)
        scripts.append(CDPEvasion.get_stealth_scripts())
        scripts.append(CDPEvasion.get_runtime_patch_script())
        
        # Canvas/WebGL/Audio Spoofing
        scripts.append(self.canvas_spoofer.get_all_spoof_scripts())
        
        return "\n\n".join(scripts)
    
    def get_consistent_headers(self) -> Dict[str, str]:
        """Retorna headers HTTP consistentes com o perfil"""
        return self.profile_manager.get_consistent_headers(self.profile)
    
    def get_ja4_fingerprint(self) -> str:
        """Retorna fingerprint JA4 do perfil"""
        return self.ja4_manager.get_ja4_string(self.browser_type)
    
    async def humanized_click(
        self,
        nodriver_tab: Any,
        element: Any,
        with_micro_movements: bool = True
    ) -> None:
        """
        Realiza clique humanizado em um elemento.
        
        Args:
            nodriver_tab: Tab do Nodriver
            element: Elemento a clicar
            with_micro_movements: Adicionar micro-movimentos antes do clique
        """
        try:
            # Obter posição do elemento
            box = await element.get_bounding_box()
            if not box:
                await element.click()
                return
            
            # Calcular centro do elemento com pequena variação
            center_x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
            center_y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
            
            # Micro-movimentos antes do clique
            if with_micro_movements:
                movements = self.behavioral.generate_micro_movements(
                    (center_x, center_y),
                    duration_ms=200
                )
                
                for x, y, delay in movements:
                    await nodriver_tab.mouse.move(x, y)
                    await asyncio.sleep(delay / 1000)
            
            # Clique
            await nodriver_tab.mouse.click(center_x, center_y)
            
        except Exception as e:
            logger.debug(f"Fallback para clique simples: {e}")
            await element.click()
    
    async def humanized_type(
        self,
        element: Any,
        text: str
    ) -> None:
        """
        Digita texto de forma humanizada.
        
        Args:
            element: Elemento de input
            text: Texto a digitar
        """
        delays = self.behavioral.get_typing_delays_for_text(text)
        
        for i, char in enumerate(text):
            await element.send_keys(char)
            await asyncio.sleep(delays[i] / 1000)
    
    async def humanized_scroll(
        self,
        nodriver_tab: Any,
        distance: int,
        direction: str = 'down'
    ) -> None:
        """
        Realiza scroll humanizado.
        
        Args:
            nodriver_tab: Tab do Nodriver
            distance: Distância em pixels
            direction: 'up' ou 'down'
        """
        scrolls = self.behavioral.generate_scroll_pattern(distance)
        
        for delta, delay in scrolls:
            if direction == 'up':
                delta = -delta
            
            await nodriver_tab.mouse.scroll(0, delta)
            await asyncio.sleep(delay / 1000)
    
    async def reading_pause(self, text_length: int) -> None:
        """
        Pausa como se estivesse lendo um texto.
        
        Args:
            text_length: Número de caracteres do texto
        """
        pauses = self.behavioral.generate_reading_pauses(text_length)
        total_pause = sum(pauses)
        
        logger.debug(f"   └── Pausa de leitura: {total_pause}ms")
        await asyncio.sleep(total_pause / 1000)
    
    def rotate_profile(self) -> BrowserProfile:
        """Rotaciona para um novo perfil aleatório"""
        self.browser_type = random.choice(list(BrowserType))
        self.profile = self.profile_manager.get_profile(self.browser_type)
        self.canvas_spoofer = CanvasWebGLSpoofer(self.profile)
        
        logger.info(f"🔄 Perfil rotacionado para {self.browser_type.value}")
        return self.profile


# =============================================================================
# TESTES E EXECUÇÃO DIRETA
# =============================================================================

# Alias para compatibilidade
AntiDetection = AntiDetectionManager

if __name__ == "__main__":
    print("=" * 60)
    print("   Anti-Detecção Avançada 2026 - God Mode Ultimate")
    print("   Módulo de Evasão de Fingerprinting")
    print("=" * 60)
    
    # Teste do JA4 Manager
    print("\n🧪 Teste JA4FingerprintManager:")
    ja4_manager = JA4FingerprintManager()
    for browser_type in list(BrowserType)[:3]:
        ja4 = ja4_manager.get_ja4_string(browser_type)
        print(f"   {browser_type.value}: {ja4}")
    
    # Teste do Profile Manager
    print("\n🧪 Teste BrowserProfileManager:")
    profile_manager = BrowserProfileManager()
    profile = profile_manager.get_random_profile()
    print(f"   Perfil selecionado: {profile.browser_type.value}")
    print(f"   User-Agent: {profile.user_agent[:50]}...")
    print(f"   Canvas seed: {hex(profile.canvas_seed)}")
    
    # Teste do Behavioral Evasion
    print("\n🧪 Teste BehavioralEvasion:")
    behavioral = BehavioralEvasion()
    
    path = behavioral.generate_bezier_path((0, 0), (100, 100), num_points=5)
    print(f"   Caminho Bézier (5 pontos): {path}")
    
    delays = behavioral.get_typing_delays_for_text("teste")
    print(f"   Delays para 'teste': {delays}")
    
    poisson = behavioral.get_poisson_delay()
    print(f"   Delay Poisson: {poisson}ms")
    
    # Teste do Anti-Detection Manager
    print("\n🧪 Teste AntiDetectionManager:")
    manager = AntiDetectionManager()
    print(f"   JA4: {manager.get_ja4_fingerprint()}")
    print(f"   Headers: {list(manager.get_consistent_headers().keys())}")
    
    print("\n✅ Todos os testes concluídos!")
