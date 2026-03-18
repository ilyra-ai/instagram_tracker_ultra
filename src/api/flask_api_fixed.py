"""
Flask API Corrigida - Instagram Tracker 2025
Usa os novos sistemas de scraping sem APIs descontinuadas
"""

import os
import sys
import logging
from dotenv import load_dotenv
from werkzeug.security import check_password_hash

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar pasta src ao path para imports funcionarem
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS

# Imports dos módulos core
try:
    from core.activity_tracker_2025 import ActivityTracker2025
    from core.instagram_scraper_2025 import InstagramScraper2025
except ImportError:
    # Fallback para imports diretos (compatibilidade)
    try:
        from activity_tracker_2025 import ActivityTracker2025
        from instagram_scraper_2025 import InstagramScraper2025
    except ImportError:
        ActivityTracker2025 = None
        InstagramScraper2025 = None

import asyncio

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__, 
            static_folder='../../static',
            template_folder='../../templates')
app.config['SECRET_KEY'] = 'instagram_tracker_2025_secret_key'

# Habilitar CORS
CORS(app, origins="*")

# =============================================================================
# TASK QUEUE E SOCKETIO (Arquitetura Orientada a Eventos)
# =============================================================================

# Tentar importar Flask-SocketIO
try:
    from flask_socketio import SocketIO, emit
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    SocketIO = None
    emit = None

# Importar Task Queue
try:
    from core.task_queue import get_task_queue, TaskPriority
    TASK_QUEUE_AVAILABLE = True
except ImportError:
    try:
        from task_queue import get_task_queue, TaskPriority
        TASK_QUEUE_AVAILABLE = True
    except ImportError:
        TASK_QUEUE_AVAILABLE = False
        get_task_queue = None

# Importar Sentiment Analyzer
try:
    from analytics.sentiment_analyzer import get_sentiment_analyzer
    SENTIMENT_AVAILABLE = True
except ImportError:
    try:
        from sentiment_analyzer import get_sentiment_analyzer
        SENTIMENT_AVAILABLE = True
    except ImportError:
        SENTIMENT_AVAILABLE = False
        get_sentiment_analyzer = None

# Importar Predictive Engine
try:
    from analytics.predictive_engine import get_predictive_engine
    PREDICTIVE_AVAILABLE = True
except ImportError:
    try:
        from predictive_engine import get_predictive_engine
        PREDICTIVE_AVAILABLE = True
    except ImportError:
        PREDICTIVE_AVAILABLE = False
        get_predictive_engine = None

try:
    from intelligence.ai_vision import get_ai_vision
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    get_ai_vision = None


# Inicializar SocketIO se disponível
if SOCKETIO_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    logger.info("✅ Flask-SocketIO inicializado")
else:
    socketio = None
    logger.warning("⚠️ Flask-SocketIO não disponível. Notificações em tempo real desabilitadas.")

# Variável global para rastreador ativo
active_tracker = None

@app.route('/api/instagram/status', methods=['GET'])
def get_status():
    """Retorna o status da API"""
    return jsonify({
        'service': 'Instagram Tracker API 2025 - Fixed',
        'status': 'online',
        'version': '3.0.0',
        'features': [
            'Web scraping sem APIs descontinuadas',
            'Login opcional persistente', 
            'Rastreamento de atividades de saída',
            'Anti-detecção avançada',
            'Nodriver (CDP)'
        ]
    })

@app.route("/api/instagram/track", methods=["GET"])
def track_activities():
    """Rastreia atividades que o usuário FEZ (curtidas e comentários de saída)"""
    global active_tracker
    
    try:
        data = request.args
        
        if not data or 'username' not in data:
            return jsonify({'error': 'Nome de usuário é obrigatório'}), 400
        
        username = data['username'].replace('@', '').strip()
        login_username = data.get('login_username', '').strip()
        login_password = data.get('login_password', '').strip()
        max_following = data.get('max_following', 20) # Removido limite de performance
        headless = data.get('headless', True)

        if not username:
            return jsonify({'error': 'Nome de usuário não pode estar vazio'}), 400
        
        ignored_users_str = data.get('ignored_users', '')
        ignored_users = [u.strip().replace('@', '') for u in ignored_users_str.split(',') if u.strip()]
        
        logger.info(f"🎯 Iniciando rastreamento para @{username}")
        logger.info(f"Login fornecido: {'Sim' if login_username else 'Não'}")
        logger.info(f"Max following: {max_following}")
        if ignored_users:
            logger.info(f"🚫 Ignorando usuários: {', '.join(ignored_users)}")
        
        # Criar tracker
        active_tracker = ActivityTracker2025(
            headless=headless
        )
        
        try:
            # Rastrear atividades de saída (Agora Async)
            # Usamos asyncio.run para executar a corrotina no contexto síncrono do Flask
            activities = asyncio.run(active_tracker.track_user_outgoing_activities(
                target_username=username,
                login_username=login_username if login_username else None,
                login_password=login_password if login_password else None,
                max_following=max_following,
                ignored_users=ignored_users
            ))
            
            # Organizar resultados
            result = {
                'success': True,
                'username': username,
                'activities': activities,
                'total_activities': len(activities),
                'activity_types': {
                    'outgoing_likes': len([a for a in activities if a.get('type') == 'outgoing_like']),
                    'outgoing_comments': len([a for a in activities if a.get('type') == 'outgoing_comment']),
                    'mentions': len([a for a in activities if a.get('type') == 'mention'])
                },
                'metadata': {
                    'login_used': bool(login_username and active_tracker.scraper.logged_in),
                    'browser_used': 'Nodriver',
                    'max_following_analyzed': max_following,
                    'timestamp': activities[0].get('timestamp') if activities else None
                }
            }
            
            logger.info(f"✅ Rastreamento concluído: {len(activities)} atividades encontradas")
            return jsonify(result)
            
        finally:
            # Limpar recursos
            if active_tracker:
                active_tracker.cleanup()
                active_tracker = None
            
    except Exception as e:
        logger.error(f"❌ Erro no rastreamento: {str(e)}")
        
        # Limpar recursos em caso de erro
        if active_tracker:
            try:
                active_tracker.cleanup()
            except:
                pass
            active_tracker = None
        
        return jsonify({
            'error': f'Erro no rastreamento: {str(e)}',
            'success': False
        }), 500

@app.route("/api/instagram/user-info", methods=["GET"])
def get_user_info():
    """Obtém informações básicas do usuário"""
    try:
        data = request.args
        
        if not data or 'username' not in data:
            return jsonify({'error': 'Nome de usuário é obrigatório'}), 400
        
        username = data['username'].replace('@', '').strip()
        login_username = data.get('login_username', '').strip()
        login_password = data.get('login_password', '').strip()
        headless = data.get('headless', True)
        
        logger.info(f"📊 Obtendo informações de @{username}")
        
        # Criar scraper
        scraper = InstagramScraper2025(
            headless=headless
        )
        
        try:
            # Login opcional
            scraper.login_optional(
                login_username if login_username else None,
                login_password if login_password else None
            )
            
            # Obter informações do usuário
            user_info = scraper.get_user_info(username)
            
            if not user_info:
                return jsonify({'error': 'Usuário não encontrado'}), 404
            
            result = {
                'success': True,
                'username': username,
                'user_info': user_info,
                'metadata': {
                    'login_used': scraper.logged_in,
                    'browser_used': 'Nodriver'
                }
            }
            
            logger.info(f"✅ Informações obtidas para @{username}")
            return jsonify(result)
            
        finally:
            scraper.cleanup()
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter informações: {str(e)}")
        return jsonify({
            'error': f'Erro ao obter informações: {str(e)}',
            'success': False
        }), 500

@app.route("/api/instagram/posts", methods=["GET"])
def get_user_posts():
    """Obtém posts recentes do usuário"""
    try:
        data = request.args
        
        if not data or 'username' not in data:
            return jsonify({'error': 'Nome de usuário é obrigatório'}), 400
        
        username = data['username'].replace('@', '').strip()
        limit = data.get('limit', 20)  # Removido limite de performance
        login_username = data.get('login_username', '').strip()
        login_password = data.get('login_password', '').strip()
        headless = data.get('headless', True)
        
        logger.info(f"📸 Obtendo posts de @{username} (limite: {limit})")
        
        # Criar scraper
        scraper = InstagramScraper2025(
            headless=headless
        )
        
        try:
            # Login opcional
            scraper.login_optional(
                login_username if login_username else None,
                login_password if login_password else None
            )
            
            # Obter informações do usuário
            user_info = scraper.get_user_info(username)
            if not user_info:
                return jsonify({'error': 'Usuário não encontrado'}), 404
            
            # Obter posts
            ignore_pinned = data.get('ignore_pinned', False)
            media_type = data.get('media_type', 'both') # 'posts', 'reels', 'both'
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            posts = scraper.get_user_posts(username, limit, ignore_pinned=ignore_pinned, media_type=media_type, start_date=start_date, end_date=end_date)



            
            result = {
                'success': True,
                'username': username,
                'user_info': user_info,
                'posts': posts,
                'total_posts': len(posts),
                'metadata': {
                    'login_used': scraper.logged_in,
                    'browser_used': 'Nodriver',
                    'limit_requested': limit
                }
            }
            
            logger.info(f"✅ {len(posts)} posts obtidos para @{username}")
            return jsonify(result)
            
        finally:
            scraper.cleanup()
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter posts: {str(e)}")
        return jsonify({
            'error': f'Erro ao obter posts: {str(e)}',
            'success': False
        }), 500

@app.route("/api/instagram/following", methods=["GET"])
def get_following():
    """Obtém lista de usuários que o target está seguindo"""
    try:
        data = request.args
        
        if not data or 'username' not in data:
            return jsonify({'error': 'Nome de usuário é obrigatório'}), 400
        
        username = data['username'].replace('@', '').strip()
        limit = data.get('limit', 50)  # Removido limite de performance
        login_username = data.get('login_username', '').strip()
        login_password = data.get('login_password', '').strip()
        headless = data.get('headless', True)
        
        logger.info(f"👥 Obtendo seguindo de @{username} (limite: {limit})")
        
        # Criar scraper
        scraper = InstagramScraper2025(
            headless=headless
        )
        
        try:
            # Login opcional
            scraper.login_optional(
                login_username if login_username else None,
                login_password if login_password else None
            )
            
            # Obter lista de seguindo
            following_list = scraper.get_following_list(username, limit)
            
            result = {
                'success': True,
                'username': username,
                'following': following_list,
                'total_following': len(following_list),
                'metadata': {
                    'login_used': scraper.logged_in,
                    'browser_used': 'Nodriver',
                    'limit_requested': limit,
                    'note': 'Lista de seguindo requer login para dados completos'
                }
            }
            
            logger.info(f"✅ {len(following_list)} usuários seguidos obtidos para @{username}")
            return jsonify(result)
            
        finally:
            scraper.cleanup()
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter seguindo: {str(e)}")
        return jsonify({
            'error': f'Erro ao obter seguindo: {str(e)}',
            'success': False
        }), 500

@app.route("/api/instagram/locations", methods=["GET"])
def get_locations():
    """Rastreia locais frequentados pelo usuário"""
    try:
        data = request.args
        
        if not data or 'username' not in data:
            return jsonify({'error': 'Nome de usuário é obrigatório'}), 400
        
        username = data['username'].replace('@', '').strip()
        limit = data.get('limit', 50)
        login_username = data.get('login_username', '').strip()
        login_password = data.get('login_password', '').strip()
        headless = data.get('headless', True)
        
        logger.info(f"📍 Rastreando locais de @{username}")
        
        tracker = ActivityTracker2025(headless=headless)
        
        try:
            # Login opcional
            if login_username and login_password:
                tracker.scraper.login_optional(login_username, login_password)
            
            # Rastrear locais
            locations = asyncio.run(tracker.track_user_locations(username, limit=limit))
            
            result = {
                'success': True,
                'username': username,
                'locations': locations,
                'total_locations': len(locations),
                'metadata': {
                    'login_used': tracker.scraper.logged_in,
                    'browser_used': 'Nodriver'
                }
            }
            
            logger.info(f"✅ {len(locations)} locais obtidos para @{username}")
            return jsonify(result)
            
        finally:
            tracker.cleanup()
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter locais: {str(e)}")
        return jsonify({
            'error': f'Erro ao obter locais: {str(e)}',
            'success': False
        }), 500

@app.route('/api/instagram/test', methods=['GET'])
def test_system():
    """Testa o sistema de scraping com melhor tratamento de erros"""
    try:
        logger.info("🧪 Testando sistema de scraping (God Mode)...")
        
        scraper = None
        try:
            logger.info("⚙️ Inicializando InstagramScraper2025 para teste...")
            scraper = InstagramScraper2025(headless=True)
            
            # Teste de Inicialização do Browser (Nodriver)
            logger.info("🔧 Testando inicialização do Browser (Nodriver)...")
            if scraper.initialize_browser():
                logger.info("✅ Browser Manager inicializado")
                browser_working = True
            else:
                logger.warning("⚠️ Falha na inicialização do Browser Manager")
                browser_working = False
            
            # Teste de Conectividade Async (curl_cffi)
            logger.info("🌐 Testando conectividade Async (curl_cffi)...")
            async def test_connectivity():
                try:
                    # Testar acesso ao Instagram
                    headers = scraper._get_api_headers()
                    logger.info(f"Headers usados: {headers}")
                    response = await scraper.session.get("https://www.instagram.com/", headers=headers)
                    logger.info(f"Status Code recebido: {response.status_code}")
                    if response.status_code != 200:
                        logger.warning(f"Resposta não-200: {response.text[:200]}...")
                    return response.status_code == 200
                except Exception as e:
                    logger.error(f"Erro no teste de conectividade: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return False

            connectivity_ok = asyncio.run(test_connectivity())
            
            if connectivity_ok:
                logger.info("✅ Conectividade Async OK")
                scraping_working = True
                message = "Sistema funcionando corretamente - Async Requests OK"
            else:
                logger.error("❌ Falha na conectividade Async")
                scraping_working = False
                message = "Falha na conectividade com Instagram"
            
            result = {
                'success': browser_working and scraping_working,
                'message': message,
                'test_user': 'instagram',
                'followers': 0,
                'browser_working': browser_working,
                'scraping_working': scraping_working,
                'chrome_version': 'Nodriver (Chrome CDP)',
                'chromedriver_version': 'Nodriver Internal'
            }
            
            logger.info(f"✅ Teste concluído: {message}")
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erro no teste do sistema: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'Erro no teste: {str(e)}',
                'browser_working': False,
                'scraping_working': False,
                'error': str(e)
            }), 500
        finally:
            # Limpar recursos
            if scraper:
                try:
                    scraper.cleanup()
                except Exception as cleanup_error:
                    logger.warning(f"Erro na limpeza: {cleanup_error}")
    
    except Exception as outer_e:
        logger.error(f"❌ Erro crítico no teste: {str(outer_e)}")
        return jsonify({
            'success': False,
            'message': f'Erro crítico: {str(outer_e)}',
            'browser_working': False,
            'scraping_working': False
        }), 500


# =============================================================================
# ENDPOINTS DE TASK QUEUE (Arquitetura Orientada a Eventos)
# =============================================================================

@app.route('/api/tasks/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Retorna o status de uma tarefa específica.
    
    Args:
        task_id: ID único da tarefa
        
    Returns:
        JSON com status, progresso, resultado ou erro
    """
    if not TASK_QUEUE_AVAILABLE:
        return jsonify({
            'error': 'TaskQueue não disponível',
            'success': False
        }), 503
    
    try:
        queue = get_task_queue()
        status = queue.get_task_status(task_id)
        
        if status:
            return jsonify({
                'success': True,
                'task': status
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Tarefa não encontrada'
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter status da tarefa: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tasks/enqueue', methods=['POST'])
def enqueue_task():
    """
    Enfileira uma nova tarefa para processamento assíncrono.
    
    Body JSON esperado:
    {
        "task_type": "scrape_profile" | "track_activities",
        "metadata": { ... },
        "priority": "low" | "normal" | "high" | "critical"
    }
    
    Returns:
        JSON com task_id para acompanhamento
    """
    if not TASK_QUEUE_AVAILABLE:
        return jsonify({
            'error': 'TaskQueue não disponível',
            'success': False
        }), 503
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Body JSON é obrigatório'
            }), 400
        
        task_type = data.get('task_type')
        metadata = data.get('metadata', {})
        priority_str = data.get('priority', 'normal').upper()
        
        if not task_type:
            return jsonify({
                'success': False,
                'error': 'task_type é obrigatório'
            }), 400
        
        # Mapear string para enum
        priority_map = {
            'LOW': TaskPriority.LOW,
            'NORMAL': TaskPriority.NORMAL,
            'HIGH': TaskPriority.HIGH,
            'CRITICAL': TaskPriority.CRITICAL
        }
        priority = priority_map.get(priority_str, TaskPriority.NORMAL)
        
        # Enfileirar tarefa
        queue = get_task_queue()
        task_id = queue.enqueue(
            task_type=task_type,
            metadata=metadata,
            priority=priority
        )
        
        logger.info(f"📥 Tarefa enfileirada via API: {task_id} ({task_type})")
        
        # Notificar via SocketIO se disponível
        if SOCKETIO_AVAILABLE and socketio:
            socketio.emit('task_enqueued', {
                'task_id': task_id,
                'task_type': task_type,
                'priority': priority_str
            })
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Tarefa enfileirada com sucesso',
            'status_endpoint': f'/api/tasks/status/{task_id}'
        }), 202
        
    except Exception as e:
        logger.error(f"❌ Erro ao enfileirar tarefa: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tasks/list', methods=['GET'])
def list_tasks():
    """
    Lista todas as tarefas, opcionalmente filtradas por status.
    
    Query params:
        status: pending | running | completed | failed | cancelled
    """
    if not TASK_QUEUE_AVAILABLE:
        return jsonify({
            'error': 'TaskQueue não disponível',
            'success': False
        }), 503
    
    try:
        status_filter = request.args.get('status')
        
        queue = get_task_queue()
        tasks = queue.get_all_tasks(status=status_filter)
        
        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar tarefas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tasks/stats', methods=['GET'])
def get_queue_stats():
    """
    Retorna estatísticas da fila de tarefas.
    """
    if not TASK_QUEUE_AVAILABLE:
        return jsonify({
            'error': 'TaskQueue não disponível',
            'success': False
        }), 503
    
    try:
        queue = get_task_queue()
        stats = queue.get_queue_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tasks/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """
    Cancela uma tarefa pendente.
    """
    if not TASK_QUEUE_AVAILABLE:
        return jsonify({
            'error': 'TaskQueue não disponível',
            'success': False
        }), 503
    
    try:
        queue = get_task_queue()
        cancelled = queue.cancel_task(task_id)
        
        if cancelled:
            # Notificar via SocketIO
            if SOCKETIO_AVAILABLE and socketio:
                socketio.emit('task_cancelled', {'task_id': task_id})
            
            return jsonify({
                'success': True,
                'message': 'Tarefa cancelada com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Tarefa não encontrada ou não pode ser cancelada'
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Erro ao cancelar tarefa: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# EVENTOS SOCKETIO (Notificações em Tempo Real)
# =============================================================================

if SOCKETIO_AVAILABLE and socketio:
    @socketio.on('connect')
    def handle_connect():
        """Cliente conectou via WebSocket"""
        logger.info("🔌 Cliente WebSocket conectado")
        emit('connected', {'message': 'Conectado ao servidor de notificações'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Cliente desconectou"""
        logger.info("🔌 Cliente WebSocket desconectado")
    
    @socketio.on('subscribe_task')
    def handle_subscribe_task(data):
        """Cliente quer receber atualizações de uma tarefa específica"""
        task_id = data.get('task_id')
        if task_id:
            logger.info(f"📡 Cliente inscrito para atualizações da tarefa: {task_id}")
            emit('subscribed', {'task_id': task_id})


# =============================================================================
# ENDPOINTS DE INTELIGÊNCIA ARTIFICIAL
# =============================================================================

@app.route('/api/intelligence/sentiment/<username>', methods=['GET'])
def analyze_user_sentiment(username):
    """
    Analisa o sentimento dos textos associados a um usuário (bio, comentários, posts).
    
    Args:
        username: Nome de usuário do Instagram
        
    Query params:
        include_bio: bool (default True) - Incluir análise da biografia
        include_posts: bool (default True) - Incluir análise de legendas dos posts
        max_posts: int (default 20) - Número máximo de posts para analisar
        
    Returns:
        JSON com análise de sentimento completa
    """
    if not SENTIMENT_AVAILABLE:
        return jsonify({
            'error': 'Módulo de análise de sentimento não disponível',
            'success': False
        }), 503
    
    try:
        username = username.replace('@', '').strip()
        
        if not username:
            return jsonify({
                'success': False,
                'error': 'Nome de usuário é obrigatório'
            }), 400
        
        # Parâmetros
        include_bio = request.args.get('include_bio', 'true').lower() == 'true'
        include_posts = request.args.get('include_posts', 'true').lower() == 'true'
        max_posts = int(request.args.get('max_posts', 20))
        
        logger.info(f"🧠 Iniciando análise de sentimento para @{username}")
        
        # Criar scraper para obter dados
        scraper = InstagramScraper2025(headless=True)
        
        try:
            # Obter informações do usuário
            user_info = scraper.get_user_info(username)
            
            if not user_info:
                return jsonify({
                    'success': False,
                    'error': 'Usuário não encontrado'
                }), 404
            
            # Inicializar analisador
            analyzer = get_sentiment_analyzer()
            
            textos_para_analisar = []
            resultados_detalhados = {
                'bio': None,
                'posts': []
            }
            
            # Analisar biografia
            if include_bio and user_info.get('biography'):
                bio = user_info.get('biography', '')
                if bio:
                    bio_result = analyzer.analyze(bio)
                    resultados_detalhados['bio'] = bio_result.to_dict()
                    textos_para_analisar.append(bio_result)
            
            # Analisar posts
            if include_posts:
                posts = scraper.get_user_posts(username, limit=max_posts)
                
                for post in posts:
                    caption = post.get('caption', '')
                    if caption:
                        post_result = analyzer.analyze(caption)
                        resultados_detalhados['posts'].append({
                            'post_code': post.get('code', ''),
                            'caption_preview': caption[:100] + '...' if len(caption) > 100 else caption,
                            'sentiment': post_result.to_dict()
                        })
                        textos_para_analisar.append(post_result)
            
            # Calcular sentimento agregado
            sentimento_agregado = analyzer.get_aggregate_sentiment(textos_para_analisar)
            
            result = {
                'success': True,
                'username': username,
                'sentimento_agregado': sentimento_agregado,
                'detalhes': resultados_detalhados,
                'metadata': {
                    'total_textos_analisados': len(textos_para_analisar),
                    'include_bio': include_bio,
                    'include_posts': include_posts,
                    'max_posts': max_posts
                }
            }
            
            logger.info(f"✅ Análise de sentimento concluída para @{username}: {sentimento_agregado.get('categoria_dominante', 'neutro')}")
            return jsonify(result)
            
        finally:
            scraper.cleanup()
            
    except Exception as e:
        logger.error(f"❌ Erro na análise de sentimento: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/intelligence/sentiment/text', methods=['POST'])
def analyze_text_sentiment():
    """
    Analisa o sentimento de um texto fornecido diretamente.
    
    Body JSON:
    {
        "text": "Texto para analisar",
        "texts": ["Lista", "de", "textos"]  // Alternativa para múltiplos textos
    }
    
    Returns:
        JSON com análise de sentimento
    """
    if not SENTIMENT_AVAILABLE:
        return jsonify({
            'error': 'Módulo de análise de sentimento não disponível',
            'success': False
        }), 503
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Body JSON é obrigatório'
            }), 400
        
        analyzer = get_sentiment_analyzer()
        
        # Texto único
        text = data.get('text')
        if text:
            result = analyzer.analyze(text)
            return jsonify({
                'success': True,
                'resultado': result.to_dict()
            })
        
        # Múltiplos textos
        texts = data.get('texts', [])
        if texts:
            results = analyzer.analyze_batch(texts)
            agregado = analyzer.get_aggregate_sentiment(results)
            
            return jsonify({
                'success': True,
                'resultados': [r.to_dict() for r in results],
                'agregado': agregado
            })
        
        return jsonify({
            'success': False,
            'error': 'Forneça "text" ou "texts" no body'
        }), 400
        
    except Exception as e:
        logger.error(f"❌ Erro na análise de sentimento: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/intelligence/prediction/<username>', methods=['GET'])
def analyze_user_prediction(username):
    """
    Analisa padrões comportamentais e gera previsões de atividade.
    
    Args:
        username: Nome de usuário do Instagram
        
    Query params:
        max_posts: int (default 50) - Número máximo de posts para analisar
        
    Returns:
        JSON com análise de previsibilidade e previsões
    """
    if not PREDICTIVE_AVAILABLE:
        return jsonify({
            'error': 'Módulo de análise preditiva não disponível',
            'success': False
        }), 503
    
    try:
        username = username.replace('@', '').strip()
        
        if not username:
            return jsonify({
                'success': False,
                'error': 'Nome de usuário é obrigatório'
            }), 400
        
        max_posts = int(request.args.get('max_posts', 50))
        
        logger.info(f"🔮 Iniciando análise preditiva para @{username}")
        
        # Criar scraper para obter dados
        scraper = InstagramScraper2025(headless=True)
        
        try:
            # Obter informações do usuário
            user_info = scraper.get_user_info(username)
            
            if not user_info:
                return jsonify({
                    'success': False,
                    'error': 'Usuário não encontrado'
                }), 404
            
            # Obter posts para análise
            posts = scraper.get_user_posts(username, limit=max_posts)
            
            if not posts:
                return jsonify({
                    'success': False,
                    'error': 'Nenhum post encontrado para análise'
                }), 404
            
            # Inicializar motor preditivo
            engine = get_predictive_engine()
            
            # Realizar análise
            resultado = engine.analisar(posts, username)
            
            result = {
                'success': True,
                'username': username,
                'analise': resultado.to_dict(),
                'resumo': {
                    'score_previsibilidade': resultado.score_previsibilidade,
                    'nivel': resultado.nivel_previsibilidade,
                    'horarios_pico': resultado.horarios_pico,
                    'dias_pico': resultado.dias_pico,
                    'tendencia': resultado.tendencia
                },
                'metadata': {
                    'posts_analisados': len(posts),
                    'max_posts': max_posts
                }
            }
            
            logger.info(f"✅ Análise preditiva concluída para @{username}: Score {resultado.score_previsibilidade:.1f}/100")
            return jsonify(result)
            
        finally:
            scraper.cleanup()
            
    except Exception as e:
        logger.error(f"❌ Erro na análise preditiva: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/intelligence/visual/<username>', methods=['GET'])
def analyze_user_visual(username):
    """
    Analisa imagens dos posts de um usuário usando visão computacional.
    
    Args:
        username: Nome de usuário do Instagram
        
    Query params:
        max_images: int (default 20) - Número máximo de imagens para analisar
        conf_threshold: float (default 0.5) - Limiar de confiança para detecções
        
    Returns:
        JSON com análise visual do perfil (categorias, tags, objetos detectados)
    """
    if not VISION_AVAILABLE:
        return jsonify({
            'error': 'Módulo de visão computacional não disponível',
            'success': False
        }), 503
    
    try:
        username = username.replace('@', '').strip()
        
        if not username:
            return jsonify({
                'success': False,
                'error': 'Nome de usuário é obrigatório'
            }), 400
        
        max_images = int(request.args.get('max_images', 20))
        conf_threshold = float(request.args.get('conf_threshold', 0.5))
        
        logger.info(f"🖼️ Iniciando análise visual para @{username}")
        
        # Criar scraper para obter dados
        scraper = InstagramScraper2025(headless=True)
        
        try:
            # Obter informações do usuário
            user_info = scraper.get_user_info(username)
            
            if not user_info:
                return jsonify({
                    'success': False,
                    'error': 'Usuário não encontrado'
                }), 404
            
            # Obter posts para análise
            posts = scraper.get_user_posts(username, limit=max_images)
            
            if not posts:
                return jsonify({
                    'success': False,
                    'error': 'Nenhum post encontrado para análise'
                }), 404
            
            # Inicializar módulo de visão
            vision = get_ai_vision()
            
            # Verificar se modelo está carregado
            if not vision.model_loaded:
                return jsonify({
                    'success': False,
                    'error': 'Modelo de visão computacional não carregado. Verifique dependências (pillow, numpy, onnxruntime)'
                }), 503
            
            # Realizar análise
            resultado = vision.analyze_profile_images(posts, username, max_images, conf_threshold)
            
            result = {
                'success': True,
                'username': username,
                'analise': resultado.to_dict(),
                'resumo': {
                    'total_imagens': resultado.total_imagens,
                    'categorias_dominantes': resultado.categorias_dominantes,
                    'tags_principais': resultado.tags_frequentes[:10],
                    'tipo_conteudo': resultado.perfil_visual.get('tipo_conteudo', 'indefinido')
                },
                'metadata': {
                    'max_images': max_images,
                    'conf_threshold': conf_threshold
                }
            }
            
            logger.info(f"✅ Análise visual concluída para @{username}: {resultado.total_imagens} imagens analisadas")
            return jsonify(result)
            
        finally:
            scraper.cleanup()
            
    except Exception as e:
        logger.error(f"❌ Erro na análise visual: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/intelligence/visual/image', methods=['POST'])
def analyze_single_image():
    """
    Analisa uma imagem específica fornecida via URL.
    
    Body JSON:
    {
        "url": "https://exemplo.com/imagem.jpg"
    }
    
    Returns:
        JSON com objetos detectados, categorias e tags
    """
    if not VISION_AVAILABLE:
        return jsonify({
            'error': 'Módulo de visão computacional não disponível',
            'success': False
        }), 503
    
    try:
        data = request.get_json()
        
        if not data or not data.get('url'):
            return jsonify({
                'success': False,
                'error': 'URL da imagem é obrigatória no body JSON'
            }), 400
        
        url = data.get('url')
        conf_threshold = float(data.get('conf_threshold', 0.5))
        
        vision = get_ai_vision()
        
        if not vision.model_loaded:
            return jsonify({
                'success': False,
                'error': 'Modelo de visão computacional não carregado'
            }), 503
        
        resultado = vision.analyze_image(url, conf_threshold)
        
        return jsonify({
            'success': True,
            'resultado': resultado.to_dict()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro na análise de imagem: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/instagram/stop', methods=['POST'])
def stop_tracking():
    """Para o rastreamento ativo"""
    global active_tracker
    
    try:
        if active_tracker:
            active_tracker.cleanup()
            active_tracker = None
            logger.info("🛑 Rastreamento interrompido pelo usuário")
            return jsonify({
                'success': True,
                'message': 'Rastreamento interrompido'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Nenhum rastreamento ativo'
            })
            
    except Exception as e:
        logger.error(f"❌ Erro ao parar rastreamento: {str(e)}")
        return jsonify({
            'error': f'Erro ao parar rastreamento: {str(e)}',
            'success': False
        }), 500

# Rotas para servir arquivos estáticos
@app.route('/')
def index():
    """Página principal - Dashboard"""
    return render_template('dashboard.html')

@app.route('/login')
def login_page():
    """Página de login"""
    return render_template('login.html')

@app.route('/app')
def app_page():
    """Página principal da aplicação"""
    return render_template('index_fixed.html')

@app.route('/api/auth/login', methods=['POST'])
def authenticate():
    """Endpoint para autenticação"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos'
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Obter credenciais das variáveis de ambiente
        VALID_USERNAME = os.getenv('ADMIN_USERNAME')
        VALID_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH')

        if not VALID_USERNAME or not VALID_PASSWORD_HASH:
            logger.error("❌ ADMIN_USERNAME ou ADMIN_PASSWORD_HASH não configurado no ambiente")
            return jsonify({
                'success': False,
                'error': 'Erro de configuração de segurança do servidor'
            }), 500
        
        if username == VALID_USERNAME and check_password_hash(VALID_PASSWORD_HASH, password):
            logger.info(f"✅ Login bem-sucedido para usuário: {username}")
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso',
                'user': username,
                'redirect': '/app'
            })
        else:
            logger.warning(f"❌ Tentativa de login inválida para usuário: {username}")
            return jsonify({
                'success': False,
                'error': 'Usuário ou senha incorretos'
            }), 401
            
    except Exception as e:
        logger.error(f"❌ Erro na autenticação: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

# =============================================================================
# ENDPOINTS DE LLM GENERATIVA (Gemini e Ollama)
# =============================================================================

# Importar clientes de LLM
try:
    from ai.gemini_client import get_gemini_client
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    get_gemini_client = None

try:
    from ai.ollama_client import get_ollama_client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    get_ollama_client = None


@app.route('/api/ai/gemini/generate', methods=['POST'])
def gemini_generate():
    """
    Gera conteúdo usando Google Gemini.
    
    Body JSON:
    {
        "prompt": "Texto do prompt",
        "temperature": 0.7 (opcional)
    }
    """
    if not GEMINI_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Módulo Gemini não disponível'
        }), 503
    
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        temperature = data.get('temperature', 0.7)
        
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt é obrigatório'
            }), 400
        
        client = get_gemini_client()
        if not client.is_configured:
            return jsonify({
                'success': False,
                'error': 'Gemini não configurado. Verifique a API Key no .env'
            }), 503
        
        result = client.generate_content(prompt, temperature)
        
        return jsonify({
            'success': True,
            'model': client.model_name,
            'response': result
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no Gemini generate: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/gemini/analyze-profile', methods=['POST'])
def gemini_analyze_profile():
    """
    Analisa biografia de perfil usando Gemini.
    
    Body JSON:
    {
        "bio": "Texto da bio",
        "username": "nome_usuario"
    }
    """
    if not GEMINI_AVAILABLE:
        return jsonify({'success': False, 'error': 'Módulo Gemini não disponível'}), 503
    
    try:
        data = request.get_json()
        bio = data.get('bio', '')
        username = data.get('username', 'desconhecido')
        
        client = get_gemini_client()
        if not client.is_configured:
            return jsonify({'success': False, 'error': 'Gemini não configurado'}), 503
        
        analysis = client.analyze_profile_bio(bio, username)
        
        return jsonify({
            'success': True,
            'model': client.model_name,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no Gemini analyze-profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/gemini/models', methods=['GET'])
def gemini_list_models():
    """Lista modelos Gemini disponíveis."""
    if not GEMINI_AVAILABLE:
        return jsonify({'success': False, 'error': 'Módulo Gemini não disponível'}), 503
    
    try:
        client = get_gemini_client()
        models = client.list_available_models() if client.is_configured else []
        
        return jsonify({
            'success': True,
            'current_model': client.model_name if client.is_configured else None,
            'models': models
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar modelos Gemini: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/ollama/generate', methods=['POST'])
def ollama_generate():
    """
    Gera conteúdo usando Ollama (LLM Local).
    
    Body JSON:
    {
        "prompt": "Texto do prompt",
        "temperature": 0.7 (opcional)
    }
    """
    if not OLLAMA_AVAILABLE:
        return jsonify({'success': False, 'error': 'Módulo Ollama não disponível'}), 503
    
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        temperature = data.get('temperature', 0.7)
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt é obrigatório'}), 400
        
        client = get_ollama_client()
        if not client.is_configured:
            return jsonify({
                'success': False,
                'error': f'Ollama não disponível em {client.base_url}'
            }), 503
        
        result = client.generate_content(prompt, temperature)
        
        return jsonify({
            'success': True,
            'model': client.model_name,
            'response': result
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no Ollama generate: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/ollama/analyze-profile', methods=['POST'])
def ollama_analyze_profile():
    """
    Analisa biografia de perfil usando Ollama.
    
    Body JSON:
    {
        "bio": "Texto da bio",
        "username": "nome_usuario"
    }
    """
    if not OLLAMA_AVAILABLE:
        return jsonify({'success': False, 'error': 'Módulo Ollama não disponível'}), 503
    
    try:
        data = request.get_json()
        bio = data.get('bio', '')
        username = data.get('username', 'desconhecido')
        
        client = get_ollama_client()
        if not client.is_configured:
            return jsonify({'success': False, 'error': 'Ollama não disponível'}), 503
        
        analysis = client.analyze_profile_bio(bio, username)
        
        return jsonify({
            'success': True,
            'model': client.model_name,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no Ollama analyze-profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/ollama/models', methods=['GET'])
def ollama_list_models():
    """Lista modelos Ollama disponíveis."""
    if not OLLAMA_AVAILABLE:
        return jsonify({'success': False, 'error': 'Módulo Ollama não disponível'}), 503
    
    try:
        client = get_ollama_client()
        
        return jsonify({
            'success': True,
            'connected': client.is_configured,
            'base_url': client.base_url,
            'current_model': client.model_name if client.is_configured else None,
            'models': client.list_available_models()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar modelos Ollama: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    """Retorna status de todos os provedores de LLM."""
    status = {
        'gemini': {
            'available': GEMINI_AVAILABLE,
            'configured': False,
            'model': None
        },
        'ollama': {
            'available': OLLAMA_AVAILABLE,
            'configured': False,
            'model': None,
            'base_url': None
        }
    }
    
    if GEMINI_AVAILABLE:
        try:
            client = get_gemini_client()
            status['gemini']['configured'] = client.is_configured
            status['gemini']['model'] = client.model_name if client.is_configured else None
        except:
            pass
    
    if OLLAMA_AVAILABLE:
        try:
            client = get_ollama_client()
            status['ollama']['configured'] = client.is_configured
            status['ollama']['model'] = client.model_name if client.is_configured else None
            status['ollama']['base_url'] = client.base_url
        except:
            pass
    
    return jsonify({
        'success': True,
        'providers': status
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Endpoint para logout"""
    try:
        logger.info("🚪 Logout realizado")
        return jsonify({
            'success': True,
            'message': 'Logout realizado com sucesso'
        })
    except Exception as e:
        logger.error(f"❌ Erro no logout: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@app.route('/<path:filename>')
def static_files(filename):
    """Arquivos estáticos"""
    return send_from_directory('.', filename)

# Tratamento de erros
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

# Limpeza ao encerrar
@app.teardown_appcontext
def cleanup_tracker(error):
    global active_tracker
    if active_tracker:
        try:
            active_tracker.cleanup()
        except:
            pass
        active_tracker = None

if __name__ == '__main__':
    logger.info("🚀 Iniciando Instagram Tracker API 2025 - Fixed")
    logger.info("📍 Acesse: http://localhost:5000")
    logger.info("🔧 API Status: http://localhost:5000/api/instagram/status")
    logger.info("🧪 Teste: http://localhost:5000/api/instagram/test")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )

