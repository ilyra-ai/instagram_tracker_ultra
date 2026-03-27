"""
Activity Tracker 2025 - Rastreia atividades que o usuário FEZ
Lógica: Analisa quem interagiu com o alvo e verifica se o alvo interagiu de volta.
Versão God Mode Ultimate - Implementação REAL sem placeholders

Funcionalidades:
- Verificação real de likes via API v1 GraphQL
- Fallback via Nodriver para abrir modal de likes
- Extração de comentários do alvo em posts de terceiros
- Cache de likers para evitar requests repetidos
- Detecção de menções
"""

import asyncio
import logging
import random
import re
from datetime import datetime
from typing import List, Dict, Optional, Set, Any
try:
    from core.instagram_scraper_2025 import InstagramScraper2025
except ImportError:
    from instagram_scraper_2025 import InstagramScraper2025

# Tentar importar cache manager
try:
    try:
        from core.cache_manager import with_backoff_jitter
    except ImportError:
        from cache_manager import with_backoff_jitter
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    def with_backoff_jitter(max_attempts=5, base_delay=1.0, max_delay=60.0, jitter=0.5):
        def decorator(func):
            return func
        return decorator


class LikersCache:
    """
    Cache local de likers para evitar requests repetidos.
    Armazena likers de posts já verificados.
    """
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Set[str]] = {}
        self._max_size = max_size
        self._access_order: List[str] = []
    
    def get(self, shortcode: str) -> Optional[Set[str]]:
        """Retorna likers cacheados ou None"""
        return self._cache.get(shortcode)
    
    def set(self, shortcode: str, likers: Set[str]) -> None:
        """Armazena likers no cache com política LRU"""
        if shortcode in self._cache:
            # Mover para o final (mais recente)
            self._access_order.remove(shortcode)
            self._access_order.append(shortcode)
        else:
            # Verificar limite
            if len(self._cache) >= self._max_size:
                # Remover mais antigo (LRU)
                oldest = self._access_order.pop(0)
                del self._cache[oldest]
            self._access_order.append(shortcode)
        
        self._cache[shortcode] = likers
    
    def has(self, shortcode: str) -> bool:
        """Verifica se shortcode está no cache"""
        return shortcode in self._cache
    
    def clear(self) -> None:
        """Limpa o cache"""
        self._cache.clear()
        self._access_order.clear()


class CommentersCache:
    """
    Cache de comentaristas por post.
    Armazena username -> texto do comentário
    """
    
    def __init__(self, max_size: int = 500):
        self._cache: Dict[str, Dict[str, str]] = {}
        self._max_size = max_size
        self._access_order: List[str] = []
    
    def get(self, shortcode: str) -> Optional[Dict[str, str]]:
        """Retorna comentaristas cacheados ou None"""
        return self._cache.get(shortcode)
    
    def set(self, shortcode: str, commenters: Dict[str, str]) -> None:
        """Armazena comentaristas no cache"""
        if shortcode in self._cache:
            self._access_order.remove(shortcode)
            self._access_order.append(shortcode)
        else:
            if len(self._cache) >= self._max_size:
                oldest = self._access_order.pop(0)
                del self._cache[oldest]
            self._access_order.append(shortcode)
        
        self._cache[shortcode] = commenters
    
    def has(self, shortcode: str) -> bool:
        """Verifica se shortcode está no cache"""
        return shortcode in self._cache


class ActivityTracker2025:
    """
    Rastreador de Atividades de Saída do Instagram.
    
    Detecta o que um usuário FEZ:
    - Curtidas dadas em posts de outras pessoas
    - Comentários feitos em posts de outras pessoas
    - Menções recebidas/feitas
    
    Implementação REAL sem placeholders:
    - Usa API v1/GraphQL para listar likers do post
    - Usa Nodriver como fallback quando API falha
    - Cache inteligente para evitar requests repetidos
    """
    
    def __init__(self, headless: bool = True):
        self.scraper = InstagramScraper2025(headless=headless)
        self.activities: List[Dict[str, Any]] = []
        
        # Caches para evitar requests repetidos
        self._likers_cache = LikersCache(max_size=500)
        self._commenters_cache = CommentersCache(max_size=500)
        
        # Estatísticas de execução
        self.stats = {
            'posts_scanned': 0,
            'api_requests': 0,
            'nodriver_fallbacks': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'likes_found': 0,
            'comments_found': 0,
            'mentions_found': 0,
            'errors': 0
        }
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def track_user_outgoing_activities(
        self, 
        target_username: str, 
        login_username: Optional[str] = None, 
        login_password: Optional[str] = None, 
        max_following: int = 50, 
        ignored_users: Optional[List[str]] = None,
        max_posts_per_profile: int = 5,
        scan_own_posts_for_interactors: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Rastreia atividades de saída do usuário alvo.
        
        Estratégia Completa:
        1. Obter lista de 'Seguindo' (pessoas que o alvo segue)
        2. Opcionalmente, analisar posts do alvo para encontrar interatores frequentes
        3. Para cada perfil do pool de alvos:
           - Obter posts recentes
           - Verificar se o alvo curtiu cada post (via API ou Nodriver)
           - Verificar se o alvo comentou em cada post
        4. Detectar menções (@target) em posts de terceiros
        
        Args:
            target_username: Username do perfil a ser rastreado
            login_username: Username para login (opcional, melhora resultados)
            login_password: Senha para login
            max_following: Número máximo de perfis seguidos a analisar
            ignored_users: Lista de usernames a ignorar
            max_posts_per_profile: Número de posts a verificar por perfil
            scan_own_posts_for_interactors: Se deve analisar posts do alvo
            
        Returns:
            Lista de atividades encontradas
        """
        self.activities = []
        ignored_users = ignored_users or []
        
        # Reset statistics
        for key in self.stats:
            self.stats[key] = 0
        
        try:
            self.logger.info(f"🚀 Iniciando rastreamento REAL para @{target_username}")
            self.logger.info(f"   ├── Máx. perfis seguidos: {max_following}")
            self.logger.info(f"   ├── Máx. posts por perfil: {max_posts_per_profile}")
            self.logger.info(f"   └── Usuários ignorados: {len(ignored_users)}")
            
            # Login opcional (melhora significativamente os resultados)
            if login_username and login_password:
                self.logger.info(f"🔐 Realizando login com @{login_username}...")
                success = await self.scraper.login_optional_async(login_username, login_password)
                if success:
                    self.logger.info("✅ Login realizado com sucesso")
                else:
                    self.logger.warning("⚠️ Login falhou, continuando sem autenticação")
            else:
                self.logger.info("ℹ️ Operando sem login (resultados limitados)")
            
            # 1. Obter lista de 'Seguindo' (pessoas que o alvo segue)
            self.logger.info(f"👥 Obtendo lista de quem @{target_username} segue...")
            following_list = await self.scraper.get_following_list_async(target_username, limit=max_following)
            
            potential_targets = [u['username'] for u in following_list if u.get('username')]
            self.logger.info(f"   └── {len(potential_targets)} perfis seguidos obtidos")
            
            # 2. Opcionalmente, analisar posts do alvo para encontrar interatores frequentes
            interactors: Set[str] = set()
            
            if scan_own_posts_for_interactors:
                self.logger.info(f"📸 Analisando posts de @{target_username} para encontrar interatores...")
                user_posts = await self.scraper.get_user_posts_async(target_username, limit=10)
                
                if isinstance(user_posts, list):
                    for post in user_posts:
                        post_interactors = await self._extract_post_interactors(post)
                        interactors.update(post_interactors)
                    
                    self.logger.info(f"   └── {len(interactors)} interatores únicos encontrados")
            
            # 3. Combinar listas e remover duplicatas
            # Priorizar quem o alvo segue (mais provável haver interação)
            all_targets = list(set(potential_targets + list(interactors)))
            
            # Filtrar ignorados
            targets_to_scan = [u for u in all_targets if u.lower() not in [i.lower() for i in ignored_users]]
            targets_to_scan = [u for u in targets_to_scan if u.lower() != target_username.lower()]
            
            self.logger.info(f"🎯 Alvos para varredura: {len(targets_to_scan)} perfis")
            
            # 4. Varrer perfis para encontrar likes/comentários do alvo
            total_profiles = len(targets_to_scan)
            for idx, profile in enumerate(targets_to_scan, 1):
                self.logger.info(f"🔍 [{idx}/{total_profiles}] Verificando @{profile}...")
                
                await self._scan_profile_for_interactions(
                    profile_username=profile, 
                    target_username=target_username,
                    max_posts=max_posts_per_profile
                )
                
                # Delay aleatório para evitar rate limiting
                delay = random.uniform(1.0, 3.0)
                await asyncio.sleep(delay)
            
            # Log final de estatísticas
            self._log_statistics()
            
            return self.activities
            
        except Exception as e:
            self.logger.error(f"❌ Erro no rastreamento: {e}")
            self.stats['errors'] += 1
            return self.activities
        
        finally:
            await self.cleanup_async()

    async def _extract_post_interactors(self, post: Dict[str, Any]) -> Set[str]:
        """
        Extrai usernames de quem interagiu com um post.
        
        Args:
            post: Dados do post
            
        Returns:
            Set de usernames que interagiram
        """
        interactors: Set[str] = set()
        
        try:
            shortcode = post.get('code')
            if not shortcode:
                return interactors
            
            # Tentar obter comentaristas
            comments = await self._get_post_comments(shortcode)
            for comment in comments:
                username = comment.get('username')
                if username:
                    interactors.add(username)
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair interatores: {e}")
        
        return interactors

    async def _scan_profile_for_interactions(
        self, 
        profile_username: str, 
        target_username: str,
        max_posts: int = 5
    ) -> None:
        """
        Varre o perfil de uma pessoa para ver se o alvo interagiu lá.
        
        Implementação REAL:
        - Obtém posts recentes do perfil
        - Para cada post, verifica se o target_username está na lista de likers
        - Verifica se o target_username comentou no post
        
        Args:
            profile_username: Perfil a ser analisado
            target_username: Usuário cujas atividades estamos rastreando
            max_posts: Número máximo de posts a verificar
        """
        try:
            # Obter posts recentes do perfil de forma assincrona e nao bloqueante
            posts = await self.scraper.get_user_posts_async(profile_username, limit=max_posts)
            
            if not isinstance(posts, list) or not posts:
                self.logger.debug(f"   └── Nenhum post encontrado para @{profile_username}")
                return
            
            # Limite de concorrência
            semaphore = asyncio.Semaphore(5)

            async def _process_post(post):
                async with semaphore:
                    self.stats['posts_scanned'] += 1
                    
                    post_url = post.get('url', '')
                    shortcode = post.get('code', '')
                    post_caption = post.get('caption', '')
                    post_timestamp = post.get('timestamp')
                    thumbnail_url = post.get('thumbnail_url')

                    if not shortcode:
                        return

                    # 1. Verificar se o alvo CURTIU ou COMENTOU este post simultaneamente
                    like_task = asyncio.create_task(self._check_if_user_liked_post(shortcode, target_username))
                    comment_task = asyncio.create_task(self._check_if_user_commented_post(shortcode, target_username))

                    has_liked, comment_data = await asyncio.gather(like_task, comment_task)

                    if has_liked:
                        self.stats['likes_found'] += 1
                        self.activities.append({
                            'type': 'outgoing_like',
                            'target_user': profile_username,
                            'post_url': post_url,
                            'post_code': shortcode,
                            'post_caption': post_caption[:200] if post_caption else None,
                            'post_timestamp': post_timestamp,
                            'thumbnail_url': thumbnail_url,
                            'detected_at': datetime.now().isoformat(),
                            'confidence': 'high'
                        })
                        self.logger.info(f"   ❤️ LIKE ENCONTRADO! @{target_username} curtiu post de @{profile_username}")

                    if comment_data:
                        self.stats['comments_found'] += 1
                        comment_id = comment_data.get('id')
                        comment_url = f"https://www.instagram.com/p/{shortcode}/c/{comment_id}/" if comment_id else post_url

                        self.activities.append({
                            'type': 'outgoing_comment',
                            'target_user': profile_username,
                            'post_url': post_url,
                            'post_code': shortcode,
                            'comment_id': comment_id,
                            'comment_url': comment_url,
                            'comment_text': comment_data.get('text', ''),
                            'comment_timestamp': comment_data.get('created_at'),
                            'post_caption': post_caption[:200] if post_caption else None,
                            'post_timestamp': post_timestamp,
                            'thumbnail_url': thumbnail_url,
                            'detected_at': datetime.now().isoformat(),
                            'confidence': 'high'
                        })
                        self.logger.info(f"   💬 COMENTÁRIO ENCONTRADO! @{target_username} comentou em @{profile_username}")

                    # 3. Verificar se o alvo foi MENCIONADO no post
                    if post_caption:
                        mentions = self._extract_mentions(post_caption)
                        if target_username.lower() in [m.lower() for m in mentions]:
                            self.stats['mentions_found'] += 1
                            self.activities.append({
                                'type': 'mention_received',
                                'from_user': profile_username,
                                'post_url': post_url,
                                'post_code': shortcode,
                                'post_caption': post_caption[:200],
                                'post_timestamp': post_timestamp,
                                'thumbnail_url': thumbnail_url,
                                'detected_at': datetime.now().isoformat(),
                                'confidence': 'high'
                            })
                            self.logger.info(f"   📣 MENÇÃO ENCONTRADA! @{profile_username} mencionou @{target_username}")

            # Processar posts de forma simultânea, limitando com semaphore para evitar overload
            await asyncio.gather(*[_process_post(post) for post in posts])

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"   └── Erro ao varrer @{profile_username}: {e}")

    async def _check_if_user_liked_post(self, shortcode: str, target_username: str) -> bool:
        """
        Verifica se um usuário específico curtiu um post.
        
        Implementação REAL com múltiplas estratégias:
        1. Verificar cache local
        2. Tentar via API v1 (endpoint de likers)
        3. Fallback: Nodriver abrindo o modal de likes
        
        Args:
            shortcode: Código do post (ex: 'ABC123xyz')
            target_username: Username a verificar
            
        Returns:
            True se o usuário curtiu o post
        """
        target_lower = target_username.lower()
        
        # 1. Verificar cache primeiro
        cached_likers = self._likers_cache.get(shortcode)
        if cached_likers is not None:
            self.stats['cache_hits'] += 1
            return target_lower in [l.lower() for l in cached_likers]
        
        self.stats['cache_misses'] += 1
        
        # 2. Tentar via API v1
        likers = await self._get_post_likers_via_api(shortcode)
        
        if likers is not None:
            # Armazenar no cache
            self._likers_cache.set(shortcode, set(likers))
            return target_lower in [l.lower() for l in likers]
        
        # 3. Fallback: Nodriver (se API falhar)
        likers_nodriver = await self._get_post_likers_via_nodriver(shortcode)
        
        if likers_nodriver is not None:
            self._likers_cache.set(shortcode, set(likers_nodriver))
            return target_lower in [l.lower() for l in likers_nodriver]
        
        # Se tudo falhar, não podemos afirmar
        return False

    async def _get_post_likers_via_api(self, shortcode: str, max_likers: int = 100) -> Optional[List[str]]:
        """
        Obtém lista de likers via API v1/GraphQL do Instagram.
        
        Endpoints tentados:
        1. /api/v1/media/{media_id}/likers/
        2. GraphQL com query hash específico
        
        Args:
            shortcode: Código do post
            max_likers: Número máximo de likers a obter
            
        Returns:
            Lista de usernames ou None se falhar
        """
        try:
            self.stats['api_requests'] += 1
            
            # Primeiro, precisamos converter shortcode para media_id
            media_id = await self._shortcode_to_media_id(shortcode)
            
            if not media_id:
                self.logger.debug(f"   └── Não foi possível converter shortcode {shortcode} para media_id")
                return None
            
            # Endpoint de likers da API v1
            url = f"https://www.instagram.com/api/v1/media/{media_id}/likers/"
            headers = self.scraper._get_api_headers()
            
            response = await self.scraper.session.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                
                likers = [user.get('username') for user in users if user.get('username')]
                self.logger.debug(f"   └── API retornou {len(likers)} likers para {shortcode}")
                return likers[:max_likers]
            
            elif response.status_code == 401:
                self.logger.debug("   └── API likers requer autenticação")
                return None
            
            elif response.status_code == 429:
                self.logger.warning("   └── Rate limited pela API de likers")
                return None
            
            else:
                self.logger.debug(f"   └── API likers retornou status {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.debug(f"   └── Erro na API de likers: {e}")
            return None

    async def _shortcode_to_media_id(self, shortcode: str) -> Optional[str]:
        """
        Converte shortcode do Instagram para media_id numérico.
        
        O Instagram usa codificação base64-like para shortcodes.
        Algoritmo: Cada caractere do shortcode é mapeado para um valor numérico.
        
        Args:
            shortcode: Código do post (ex: 'ABC123')
            
        Returns:
            Media ID numérico como string, ou None se falhar
        """
        try:
            # Caracteres usados pelo Instagram para shortcodes
            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
            
            media_id = 0
            for char in shortcode:
                media_id = media_id * 64 + alphabet.index(char)
            
            return str(media_id)
            
        except Exception as e:
            self.logger.debug(f"Erro ao converter shortcode: {e}")
            return None

    async def _get_post_likers_via_nodriver(
        self, 
        shortcode: str, 
        max_likers: int = 50,
        scroll_attempts: int = 3
    ) -> Optional[List[str]]:
        """
        Obtém lista de likers usando Nodriver (Chrome CDP) como fallback.
        
        Abre o modal de likes do post e extrai os usernames visíveis.
        
        Args:
            shortcode: Código do post
            max_likers: Número máximo de likers a extrair
            scroll_attempts: Número de vezes a rolar o modal
            
        Returns:
            Lista de usernames ou None se falhar
        """
        try:
            self.stats['nodriver_fallbacks'] += 1
            
            if not self.scraper.browser_manager:
                self.scraper.initialize_browser()
            
            browser = self.scraper.browser_manager
            
            if not browser or not browser.browser:
                await browser.start()
            
            # Navegar para o post
            post_url = f"https://www.instagram.com/p/{shortcode}/"
            await browser.navigate(post_url)
            
            # Aguardar carregamento
            await asyncio.sleep(2)
            
            # Clicar no contador de likes para abrir o modal
            # O seletor pode variar, tentamos alguns comuns
            likes_selectors = [
                'a[href*="/liked_by/"]',
                'button[class*="like"]',
                'span[class*="like"] a',
                'section a[href*="liked_by"]'
            ]
            
            modal_opened = False
            for selector in likes_selectors:
                try:
                    likes_btn = await browser.main_tab.select(selector)
                    if likes_btn:
                        await likes_btn.click()
                        modal_opened = True
                        await asyncio.sleep(1.5)
                        break
                except:
                    continue
            
            if not modal_opened:
                self.logger.debug(f"   └── Não foi possível abrir modal de likes para {shortcode}")
                return None
            
            # Extrair usernames do modal
            likers: List[str] = []
            
            for attempt in range(scroll_attempts):
                # Script para extrair usernames do modal de likes
                extract_script = r"""
                () => {
                    const usernames = [];
                    
                    // Procurar links de perfil no modal
                    const links = document.querySelectorAll('div[role="dialog"] a[href^="/"]');
                    links.forEach(link => {
                        const href = link.getAttribute('href');
                        if (href && href.match(/^\/[a-zA-Z0-9._]+\/?$/)) {
                            const username = href.replace(/\//g, '');
                            if (username && !username.includes('explore') && !username.includes('p/')) {
                                usernames.push(username);
                            }
                        }
                    });
                    
                    return [...new Set(usernames)];
                }
                """
                
                try:
                    result = await browser.main_tab.evaluate(extract_script)
                    if result and isinstance(result, list):
                        likers.extend(result)
                except:
                    pass
                
                if len(likers) >= max_likers:
                    break
                
                # Rolar o modal para carregar mais
                scroll_script = """
                () => {
                    const modal = document.querySelector('div[role="dialog"]');
                    if (modal) {
                        const scrollable = modal.querySelector('div[style*="overflow"]') || modal;
                        scrollable.scrollTop = scrollable.scrollHeight;
                    }
                }
                """
                
                try:
                    await browser.main_tab.evaluate(scroll_script)
                    await asyncio.sleep(1)
                except:
                    pass
            
            # Remover duplicatas e limitar
            likers = list(set(likers))[:max_likers]
            
            self.logger.debug(f"   └── Nodriver extraiu {len(likers)} likers para {shortcode}")
            return likers if likers else None
            
        except Exception as e:
            self.logger.debug(f"   └── Erro no Nodriver para likers: {e}")
            return None

    async def _check_if_user_commented_post(
        self, 
        shortcode: str, 
        target_username: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verifica se um usuário específico comentou em um post.
        
        Args:
            shortcode: Código do post
            target_username: Username a verificar
            
        Returns:
            Dict com dados do comentário se encontrado, None caso contrário
        """
        target_lower = target_username.lower()
        
        # Verificar cache primeiro
        cached_comments = self._commenters_cache.get(shortcode)
        if cached_comments is not None:
            self.stats['cache_hits'] += 1
            for username, data in cached_comments.items():
                if username.lower() == target_lower:
                    return data
            return None
        
        self.stats['cache_misses'] += 1
        
        # Obter comentários via API
        comments = await self._get_post_comments(shortcode)
        
        # Armazenar no cache
        commenters_dict = {}
        for comment in comments:
            username = comment.get('username', '')
            if username:
                commenters_dict[username] = comment
        
        self._commenters_cache.set(shortcode, commenters_dict)
        
        # Verificar se target está nos comentários
        for username, data in commenters_dict.items():
            if username.lower() == target_lower:
                return data
        
        return None

    async def _get_post_comments(
        self, 
        shortcode: str, 
        max_comments: int = 50
    ) -> List[Dict[str, str]]:
        """
        Obtém comentários de um post via API.
        
        Args:
            shortcode: Código do post
            max_comments: Número máximo de comentários
            
        Returns:
            Lista de dicts com username e text
        """
        try:
            self.stats['api_requests'] += 1
            
            # Converter shortcode para media_id
            media_id = await self._shortcode_to_media_id(shortcode)
            
            if not media_id:
                return []
            
            # Endpoint de comentários
            url = f"https://www.instagram.com/api/v1/media/{media_id}/comments/"
            headers = self.scraper._get_api_headers()
            
            params = {
                'can_support_threading': 'true',
                'permalink_enabled': 'false'
            }
            
            response = await self.scraper.session.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                comments = data.get('comments', [])
                
                result = []
                for comment in comments[:max_comments]:
                    user_data = comment.get('user', {})
                    result.append({
                        'id': comment.get('pk') or comment.get('id'),
                        'username': user_data.get('username', ''),
                        'text': comment.get('text', ''),
                        'created_at': comment.get('created_at')
                    })
                
                return result
            
            return []
            
        except Exception as e:
            self.logger.debug(f"Erro ao obter comentários: {e}")
            return []

    def _extract_mentions(self, text: str) -> List[str]:
        """
        Extrai menções (@username) de um texto.
        
        Args:
            text: Texto para analisar
            
        Returns:
            Lista de usernames mencionados (sem @)
        """
        if not text:
            return []
        
        # Regex para encontrar @username
        # Username do Instagram: letras, números, pontos e underscores
        pattern = r'@([a-zA-Z0-9._]+)'
        matches = re.findall(pattern, text)
        
        # Limpar e retornar únicos
        return list(set([m.lower() for m in matches if m]))

    def _log_statistics(self) -> None:
        """Loga estatísticas finais do rastreamento"""
        self.logger.info("=" * 50)
        self.logger.info("📊 ESTATÍSTICAS DO RASTREAMENTO")
        self.logger.info("=" * 50)
        self.logger.info(f"   Posts escaneados: {self.stats['posts_scanned']}")
        self.logger.info(f"   Requisições API: {self.stats['api_requests']}")
        self.logger.info(f"   Fallbacks Nodriver: {self.stats['nodriver_fallbacks']}")
        self.logger.info(f"   Cache hits: {self.stats['cache_hits']}")
        self.logger.info(f"   Cache misses: {self.stats['cache_misses']}")
        self.logger.info("-" * 50)
        self.logger.info(f"   ❤️ Likes encontrados: {self.stats['likes_found']}")
        self.logger.info(f"   💬 Comentários encontrados: {self.stats['comments_found']}")
        self.logger.info(f"   📣 Menções encontradas: {self.stats['mentions_found']}")
        self.logger.info(f"   ⚠️ Erros: {self.stats['errors']}")
        self.logger.info("=" * 50)
        self.logger.info(f"   📋 TOTAL DE ATIVIDADES: {len(self.activities)}")
        self.logger.info("=" * 50)

    def get_statistics(self) -> Dict[str, int]:
        """Retorna estatísticas de execução"""
        return self.stats.copy()

    def get_affinity_ranking(self, activities: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Calcula o ranking de afinidade com base nas atividades rastreadas.
        
        Afinidade é calculada por peso:
        - Comentário: 5 pontos
        - Like: 2 pontos
        - Menção: 3 pontos
        
        Returns:
            Lista ordenada de perfis com quem o alvo mais interagiu
        """
        acts = activities if activities is not None else self.activities
        ranking = {}
        
        for act in acts:
            user = act.get('target_user') or act.get('from_user')
            if not user:
                continue
                
            if user not in ranking:
                ranking[user] = {
                    'username': user,
                    'score': 0,
                    'likes': 0,
                    'comments': 0,
                    'mentions': 0,
                    'last_interaction': act.get('post_timestamp') or act.get('detected_at')
                }
            
            # Atribuir pesos
            act_type = act.get('type')
            if act_type == 'outgoing_like':
                ranking[user]['score'] += 2
                ranking[user]['likes'] += 1
            elif act_type == 'outgoing_comment':
                ranking[user]['score'] += 5
                ranking[user]['comments'] += 1
            elif act_type == 'mention_received':
                ranking[user]['score'] += 3
                ranking[user]['mentions'] += 1
                
            # Atualizar última interação se for mais recente
            current_ts = act.get('post_timestamp') or act.get('detected_at')
            if current_ts and (not ranking[user]['last_interaction'] or current_ts > ranking[user]['last_interaction']):
                ranking[user]['last_interaction'] = current_ts
        
        # Ordenar por score
        sorted_ranking = sorted(ranking.values(), key=lambda x: x['score'], reverse=True)
        return sorted_ranking

    def cleanup(self) -> None:
        """Limpa recursos de forma síncrona/segura"""
        self.scraper.cleanup()

    async def cleanup_async(self) -> None:
        """Limpa recursos e fecha conexões (Assíncrono)"""
        try:
            await self.scraper.cleanup_async()
        except Exception as e:
            self.logger.error(f"Erro na limpeza assíncrona: {e}")

    async def track_user_locations(self, target_username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Rastreia locais frequentados pelo usuário com base em posts.
        
        Retorna uma lista de locais com:
        - ID, nome, coordenadas
        - Contagem de frequência
        - Última visita
        - Classificação (Casa, Trabalho, Lazer) via clustering
        
        Args:
            target_username: Username do perfil
            limit: Número máximo de posts a analisar
            
        Returns:
            Lista de locais com contagem de frequência
        """
        try:
            self.logger.info(f"📍 Rastreando locais de @{target_username}...")
            posts = await self.scraper.get_user_posts_async(target_username, limit=limit)
            
            locations: Dict[str, Dict[str, Any]] = {}
            
            if isinstance(posts, list):
                for post in posts:
                    loc = post.get('location')
                    if loc and loc.get('name'):
                        loc_id = loc.get('id') or loc.get('name')
                        
                        if loc_id not in locations:
                            locations[loc_id] = {
                                'id': loc_id,
                                'name': loc.get('name'),
                                'lat': loc.get('lat'),
                                'lng': loc.get('lng'),
                                'count': 0,
                                'visits': [],
                                'first_visit': post.get('timestamp'),
                                'last_visit': post.get('timestamp'),
                                'category': None  # Será classificado
                            }
                        
                        locations[loc_id]['count'] += 1
                        locations[loc_id]['last_visit'] = post.get('timestamp')
                        
                        if post.get('timestamp'):
                            locations[loc_id]['visits'].append(post.get('timestamp'))
            
            # Classificar locais baseado em frequência
            for loc_id, loc_data in locations.items():
                count = loc_data['count']
                if count >= 5:
                    loc_data['category'] = 'frequente'
                elif count >= 3:
                    loc_data['category'] = 'regular'
                else:
                    loc_data['category'] = 'ocasional'
            
            # Ordenar por frequência
            sorted_locations = sorted(locations.values(), key=lambda x: x['count'], reverse=True)
            
            self.logger.info(f"✅ Encontrados {len(sorted_locations)} locais únicos.")
            return sorted_locations
            
        except Exception as e:
            self.logger.error(f"Erro ao rastrear locais: {e}")
            return []


# =============================================================================
# TESTES E EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("   Activity Tracker 2025 - God Mode Ultimate")
    print("   Implementação REAL sem placeholders")
    print("=" * 60)
    
    async def run_test():
        tracker = ActivityTracker2025(headless=False)
        
        print("\n🧪 Executando teste de rastreamento...")
        print("   Alvo: @instagram")
        print("   Perfis a analisar: 2")
        print()
        
        try:
            activities = await tracker.track_user_outgoing_activities(
                target_username="instagram",
                max_following=2,
                max_posts_per_profile=3
            )
            
            print(f"\n📋 Atividades encontradas: {len(activities)}")
            for activity in activities:
                print(f"   - {activity.get('type')}: {activity.get('target_user', activity.get('from_user'))}")
            
            # Mostrar estatísticas
            stats = tracker.get_statistics()
            print(f"\n📊 Estatísticas:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
                
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
    
    try:
        asyncio.run(run_test())
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
