"""
Stealth Module - Anti-detecção e operações furtivas

Exporta:
- AntiDetection: Técnicas de anti-detecção
- StealthOps: Operações furtivas (proxy, rate limit)
"""

from .anti_detection import AntiDetection, JA4FingerprintManager, BrowserProfileManager, CanvasWebGLSpoofer, BehavioralEvasion
from .stealth_ops import StealthOps, ProxyManager, RateLimiter, BiomimeticNavigator

__all__ = [
    'AntiDetection',
    'JA4FingerprintManager',
    'CanvasWebGLSpoofer',
    'BehavioralEvasion',
    'StealthOps',
    'ProxyManager',
    'RateLimiter',
    'BiomimeticNavigator'
]
