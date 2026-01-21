"""
Core Module - Componentes centrais do sistema

Exporta:
- InstagramScraper2025: Scraper principal
- ActivityTracker2025: Rastreador de atividades
- BrowserManager: Gerenciador de navegador
- CacheManager: Gerenciador de cache
- TaskQueue: Fila de tarefas assíncronas
"""

from .instagram_scraper_2025 import InstagramScraper2025
from .activity_tracker_2025 import ActivityTracker2025
from .browser_manager import BrowserManager, NodriverManager, SessionManager
from .cache_manager import CacheManager, cached, with_backoff_jitter
from .task_queue import TaskQueue, get_task_queue, TaskPriority, TaskStatus

BrowserManager = NodriverManager

__all__ = [
    'InstagramScraper2025',
    'ActivityTracker2025',
    'BrowserManager',
    'NodriverManager',
    'SessionManager',
    'CacheManager',
    'cached',
    'with_backoff_jitter',
    'TaskQueue',
    'get_task_queue',
    'TaskPriority',
    'TaskStatus'
]
