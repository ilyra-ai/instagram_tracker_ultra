"""
Task Queue - Sistema de Fila Assíncrona para Instagram Intelligence System
Implementa arquitetura orientada a eventos com workers e tracking de tarefas.

Autor: Instagram Intelligence System 2026
Versão: 1.0.0
"""

import asyncio
import logging
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading
import json

try:
    from core.browser_manager import NodriverManager as BrowserManager
except ImportError:
    from browser_manager import NodriverManager as BrowserManager


class TaskStatus(Enum):
    """Status possíveis de uma tarefa"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Níveis de prioridade para tarefas"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskInfo:
    """Informações completas de uma tarefa"""
    task_id: str
    task_type: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0.0 a 1.0
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'status': self.status.value,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'result': self.result,
            'error': self.error,
            'metadata': self.metadata,
            'duration_seconds': self._get_duration(),
        }
    
    def _get_duration(self) -> Optional[float]:
        """Calcula duração da tarefa em segundos"""
        if self.started_at:
            end = self.completed_at or datetime.now()
            return (end - self.started_at).total_seconds()
        return None


@dataclass(order=True)
class PrioritizedTask:
    """Wrapper para ordenação por prioridade na fila"""
    priority: int
    task: Any = field(compare=False)
    
    def __post_init__(self):
        # Inverter prioridade para ordenação (maior = primeiro)
        self.priority = -self.priority


class TaskRegistry:
    """
    Registro central de tarefas.
    Mantém histórico e permite consulta de status.
    """
    
    def __init__(self, max_history: int = 1000):
        self.tasks: Dict[str, TaskInfo] = {}
        self.max_history = max_history
        self.completed_tasks: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def register(self, task_id: str, task_type: str, priority: TaskPriority = TaskPriority.NORMAL, 
                 metadata: Dict = None) -> TaskInfo:
        """Registra uma nova tarefa"""
        with self._lock:
            task_info = TaskInfo(
                task_id=task_id,
                task_type=task_type,
                status=TaskStatus.PENDING,
                priority=priority,
                created_at=datetime.now(),
                metadata=metadata or {}
            )
            self.tasks[task_id] = task_info
            self.logger.debug(f"📝 Tarefa registrada: {task_id} ({task_type})")
            return task_info
    
    def update_status(self, task_id: str, status: TaskStatus, 
                      progress: float = None, result: Any = None, error: str = None) -> Optional[TaskInfo]:
        """Atualiza status de uma tarefa"""
        with self._lock:
            if task_id not in self.tasks:
                return None
            
            task = self.tasks[task_id]
            task.status = status
            
            if progress is not None:
                task.progress = min(1.0, max(0.0, progress))
            
            if status == TaskStatus.RUNNING and task.started_at is None:
                task.started_at = datetime.now()
            
            if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                task.completed_at = datetime.now()
                if result is not None:
                    task.result = result
                if error is not None:
                    task.error = error
                
                # Mover para histórico
                self.completed_tasks.append(task)
            
            self.logger.debug(f"📊 Tarefa {task_id}: {status.value} ({task.progress*100:.0f}%)")
            return task
    
    def get(self, task_id: str) -> Optional[TaskInfo]:
        """Obtém informações de uma tarefa"""
        with self._lock:
            return self.tasks.get(task_id)
    
    def get_all(self, status_filter: TaskStatus = None) -> List[TaskInfo]:
        """Lista todas as tarefas, opcionalmente filtradas por status"""
        with self._lock:
            tasks = list(self.tasks.values())
            if status_filter:
                tasks = [t for t in tasks if t.status == status_filter]
            return tasks
    
    def get_history(self, limit: int = 100) -> List[TaskInfo]:
        """Retorna histórico de tarefas completadas"""
        with self._lock:
            return list(self.completed_tasks)[-limit:]
    
    def cleanup_old(self, max_age_hours: int = 24):
        """Remove tarefas antigas do registro ativo"""
        with self._lock:
            now = datetime.now()
            to_remove = []
            for task_id, task in self.tasks.items():
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    age = (now - task.created_at).total_seconds() / 3600
                    if age > max_age_hours:
                        to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.tasks[task_id]
            
            if to_remove:
                self.logger.info(f"🧹 Removidas {len(to_remove)} tarefas antigas")


class AsyncTaskWorker:
    """
    Worker assíncrono que processa tarefas da fila.
    Suporta múltiplos workers em paralelo.
    """
    
    def __init__(self, worker_id: int, queue: asyncio.PriorityQueue, 
                 registry: TaskRegistry, handlers: Dict[str, Callable]):
        self.worker_id = worker_id
        self.queue = queue
        self.registry = registry
        self.handlers = handlers
        self.running = False
        self.current_task: Optional[str] = None
        self.logger = logging.getLogger(f"Worker-{worker_id}")
    
    async def start(self):
        """Inicia o loop do worker"""
        self.running = True
        self.logger.info(f"🚀 Worker {self.worker_id} iniciado")
        
        while self.running:
            try:
                # Aguardar próxima tarefa (com timeout para permitir shutdown)
                try:
                    prioritized_task = await asyncio.wait_for(
                        self.queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                task_info: TaskInfo = prioritized_task.task
                self.current_task = task_info.task_id
                
                self.logger.info(f"⚙️ Processando: {task_info.task_id} ({task_info.task_type})")
                
                # Atualizar status para RUNNING
                self.registry.update_status(task_info.task_id, TaskStatus.RUNNING)
                
                # Encontrar handler para o tipo de tarefa
                handler = self.handlers.get(task_info.task_type)
                
                if handler:
                    try:
                        # Executar handler
                        result = await handler(task_info)
                        
                        # Sucesso
                        self.registry.update_status(
                            task_info.task_id,
                            TaskStatus.COMPLETED,
                            progress=1.0,
                            result=result
                        )
                        self.logger.info(f"✅ Concluído: {task_info.task_id}")
                        
                    except Exception as e:
                        # Falha
                        self.registry.update_status(
                            task_info.task_id,
                            TaskStatus.FAILED,
                            error=str(e)
                        )
                        self.logger.error(f"❌ Falhou: {task_info.task_id} - {e}")
                else:
                    # Handler não encontrado
                    self.registry.update_status(
                        task_info.task_id,
                        TaskStatus.FAILED,
                        error=f"Handler não encontrado para tipo: {task_info.task_type}"
                    )
                    self.logger.error(f"❌ Handler não encontrado: {task_info.task_type}")
                
                self.current_task = None
                self.queue.task_done()
                
            except Exception as e:
                self.logger.error(f"❌ Erro no worker: {e}")
    
    async def stop(self):
        """Para o worker graciosamente"""
        self.running = False
        self.logger.info(f"⏹️ Worker {self.worker_id} parando...")


class TaskQueue:
    """
    Gerenciador principal de fila de tarefas.
    
    Funcionalidades:
    - Fila de prioridade assíncrona
    - Múltiplos workers paralelos
    - Registro e tracking de tarefas
    - Callbacks para notificação de eventos
    """
    
    def __init__(self, num_workers: int = 3, max_queue_size: int = 1000):
        self.queue: asyncio.PriorityQueue = None  # Criado no start()
        self.registry = TaskRegistry()
        self.handlers: Dict[str, Callable] = {}
        self.workers: List[AsyncTaskWorker] = []
        self.num_workers = num_workers
        self.max_queue_size = max_queue_size
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # Callbacks para eventos
        self.on_task_complete: List[Callable] = []
        self.on_task_failed: List[Callable] = []
        self.on_task_progress: List[Callable] = []
        
        # Lock para thread-safety
        self._lock = threading.Lock()
    
    def register_handler(self, task_type: str, handler: Callable[[TaskInfo], Awaitable[Any]]):
        """
        Registra um handler para um tipo de tarefa.
        
        Args:
            task_type: Nome do tipo de tarefa (ex: 'scrape_profile')
            handler: Função assíncrona que processa a tarefa
        """
        self.handlers[task_type] = handler
        self.logger.info(f"📋 Handler registrado: {task_type}")
    
    async def start(self):
        """Inicia a fila e workers"""
        if self.running:
            return
        
        self.running = True
        self.queue = asyncio.PriorityQueue(maxsize=self.max_queue_size)
        
        # Criar e iniciar workers
        for i in range(self.num_workers):
            worker = AsyncTaskWorker(i, self.queue, self.registry, self.handlers)
            self.workers.append(worker)
            asyncio.create_task(worker.start())
        
        self.logger.info(f"🚀 TaskQueue iniciada com {self.num_workers} workers")
    
    async def stop(self):
        """Para a fila e todos workers"""
        self.running = False
        
        # Parar workers
        for worker in self.workers:
            await worker.stop()
        
        # Aguardar fila esvaziar
        if self.queue:
            await self.queue.join()
        
        self.workers.clear()
        self.logger.info("⏹️ TaskQueue parada")
    
    def enqueue(self, task_type: str, metadata: Dict = None, 
                priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """
        Adiciona uma tarefa à fila.
        
        Args:
            task_type: Tipo da tarefa (deve ter handler registrado)
            metadata: Dados adicionais para a tarefa
            priority: Prioridade da tarefa
            
        Returns:
            task_id: ID único da tarefa
        """
        task_id = str(uuid.uuid4())
        
        # Registrar tarefa
        task_info = self.registry.register(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            metadata=metadata
        )
        
        # Adicionar à fila de prioridade
        prioritized = PrioritizedTask(priority=priority.value, task=task_info)
        
        try:
            self.queue.put_nowait(prioritized)
            self.logger.info(f"📥 Tarefa enfileirada: {task_id} ({task_type})")
        except asyncio.QueueFull:
            self.registry.update_status(task_id, TaskStatus.FAILED, error="Fila cheia")
            self.logger.error(f"❌ Fila cheia, tarefa rejeitada: {task_id}")
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Retorna status de uma tarefa específica"""
        task = self.registry.get(task_id)
        if task:
            return task.to_dict()
        return None
    
    def get_all_tasks(self, status: str = None) -> List[Dict]:
        """Lista todas as tarefas"""
        status_enum = None
        if status:
            try:
                status_enum = TaskStatus(status)
            except ValueError:
                pass
        
        tasks = self.registry.get_all(status_enum)
        return [t.to_dict() for t in tasks]
    
    def get_queue_stats(self) -> Dict:
        """Retorna estatísticas da fila"""
        pending = len([t for t in self.registry.get_all() if t.status == TaskStatus.PENDING])
        running = len([t for t in self.registry.get_all() if t.status == TaskStatus.RUNNING])
        completed = len([t for t in self.registry.get_all() if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in self.registry.get_all() if t.status == TaskStatus.FAILED])
        
        return {
            'queue_size': self.queue.qsize() if self.queue else 0,
            'pending': pending,
            'running': running,
            'completed': completed,
            'failed': failed,
            'total': pending + running + completed + failed,
            'workers_active': len([w for w in self.workers if w.running]),
            'workers_total': len(self.workers),
        }
    
    def update_progress(self, task_id: str, progress: float):
        """Atualiza progresso de uma tarefa (0.0 a 1.0)"""
        self.registry.update_status(task_id, TaskStatus.RUNNING, progress=progress)
        
        # Notificar callbacks
        for callback in self.on_task_progress:
            try:
                callback(task_id, progress)
            except Exception:
                pass
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancela uma tarefa pendente"""
        task = self.registry.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            self.registry.update_status(task_id, TaskStatus.CANCELLED)
            return True
        return False


# =============================================================================
# HANDLERS DE EXEMPLO PARA TAREFAS COMUNS
# =============================================================================

async def handler_scrape_profile(task_info: TaskInfo) -> Dict:
    """
    Handler para scraping de perfil.
    Metadata esperado: {'username': str}
    """
    username = task_info.metadata.get('username')
    if not username:
        raise ValueError("username é obrigatório no metadata")
    
    # Importar aqui para evitar circular import
    try:
        from core.instagram_scraper_2025 import InstagramScraper2025
    except ImportError:
        from instagram_scraper_2025 import InstagramScraper2025
    
    scraper = InstagramScraper2025(headless=True)
    try:
        result = await scraper.self_healing.get_profile(username)
        return result.data if result.success else {'error': result.error}
    finally:
        scraper.cleanup()


async def handler_track_activities(task_info: TaskInfo) -> Dict:
    """
    Handler para rastreamento de atividades.
    Metadata esperado: {'target_username': str, 'max_following': int}
    """
    target = task_info.metadata.get('target_username')
    max_following = task_info.metadata.get('max_following', 50)
    
    if not target:
        raise ValueError("target_username é obrigatório no metadata")
    
    try:
        from core.activity_tracker_2025 import ActivityTracker2025
    except ImportError:
        from activity_tracker_2025 import ActivityTracker2025
    
    tracker = ActivityTracker2025(headless=True)
    try:
        activities = await tracker.track_user_outgoing_activities(
            target_username=target,
            max_following=max_following
        )
        
        # Calcular ranking de afinidade
        affinity_ranking = tracker.get_affinity_ranking(activities)
        
        return {
            'activities': activities, 
            'count': len(activities),
            'affinity_ranking': affinity_ranking
        }
    finally:
        tracker.cleanup()


# =============================================================================
# INSTÂNCIA GLOBAL (SINGLETON)
# =============================================================================

_task_queue_instance: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """Retorna instância singleton da TaskQueue"""
    global _task_queue_instance
    if _task_queue_instance is None:
        _task_queue_instance = TaskQueue(num_workers=3)
        
        # Registrar handlers padrão
        _task_queue_instance.register_handler('scrape_profile', handler_scrape_profile)
        _task_queue_instance.register_handler('track_activities', handler_track_activities)
        
        # Handler de teste para validação
        async def handler_test_task(task_info: TaskInfo) -> Dict:
            return {'status': 'ok', 'data': task_info.metadata.get('data')}
            
        _task_queue_instance.register_handler('test_task', handler_test_task)
    
    return _task_queue_instance


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    async def test():
        queue = get_task_queue()
        await queue.start()
        
        # Enfileirar tarefa de teste
        task_id = queue.enqueue(
            task_type='scrape_profile',
            metadata={'username': 'instagram'},
            priority=TaskPriority.HIGH
        )
        
        print(f"Tarefa criada: {task_id}")
        
        # Aguardar um pouco
        await asyncio.sleep(5)
        
        # Verificar status
        status = queue.get_task_status(task_id)
        print(f"Status: {json.dumps(status, indent=2, default=str)}")
        
        # Estatísticas
        stats = queue.get_queue_stats()
        print(f"Stats: {stats}")
        
        await queue.stop()
    
    asyncio.run(test())
