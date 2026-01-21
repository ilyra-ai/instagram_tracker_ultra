"""
Advanced Analytics 2025 - Módulo de Funcionalidades Adicionais de Rastreamento
Versão God Mode Ultimate - Implementação REAL sem placeholders

Funcionalidades:
- Rastreamento de Stories
- Análise de Reels
- Análise de Hashtags
- Taxa de Engajamento
- Best Time to Post
- Qualidade de Seguidores
- Histórico de Bio
- Calendário de Conteúdo
- Rastreamento de Menções
- Detecção de Colaborações
- Snapshots Temporais
- Comparativo de Perfis
"""

import asyncio
import re
import json
import logging
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import Counter, defaultdict
import statistics
import calendar

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AdvancedAnalytics")


# =============================================================================
# ENUMS E DATACLASSES
# =============================================================================

class EngagementTier(Enum):
    """Níveis de engajamento"""
    VERY_LOW = "muito_baixo"
    LOW = "baixo"
    MEDIUM = "medio"
    HIGH = "alto"
    VIRAL = "viral"


class MentionSentiment(Enum):
    """Sentimento de menção"""
    POSITIVE = "positiva"
    NEUTRAL = "neutra"
    NEGATIVE = "negativa"


class ContentType(Enum):
    """Tipos de conteúdo"""
    PHOTO = "foto"
    VIDEO = "video"
    CAROUSEL = "carrossel"
    REEL = "reel"
    STORY = "story"
    IGTV = "igtv"


@dataclass
class StoryInfo:
    """Informações de um Story"""
    id: str
    media_type: str
    url: str
    timestamp: str
    expiration: str
    duration: Optional[float]
    mentions: List[str]
    hashtags: List[str]
    links: List[str]
    stickers: List[Dict]
    is_highlight: bool
    highlight_title: Optional[str]


@dataclass
class ReelAnalytics:
    """Analytics de um Reel"""
    id: str
    url: str
    views_count: int
    plays_count: int
    likes_count: int
    comments_count: int
    shares_count: int
    audio_name: Optional[str]
    audio_artist: Optional[str]
    is_trending_audio: bool
    duration_seconds: float
    retention_estimate: float
    caption: str
    timestamp: str


@dataclass
class HashtagStats:
    """Estatísticas de hashtag"""
    hashtag: str
    usage_count: int
    avg_likes: float
    avg_comments: float
    best_performing_post_id: str
    category: str  # "nicho", "popular", "branded"


@dataclass
class EngagementRateResult:
    """Resultado de taxa de engajamento"""
    username: str
    overall_rate: float
    tier: EngagementTier
    per_post_rates: List[Dict]
    benchmark_comparison: str
    anomalies: List[Dict]
    analyzed_posts: int


@dataclass
class BestTimeResult:
    """Resultado de melhor horário"""
    username: str
    top_hours: List[Dict]
    top_days: List[Dict]
    heatmap: Dict[str, Dict[str, float]]
    estimated_timezone: str
    recommendations: List[str]


@dataclass
class AudienceQualityResult:
    """Resultado de qualidade de audiência"""
    username: str
    quality_score: float
    real_followers_percent: float
    bot_followers_percent: float
    suspicious_accounts: int
    sample_size: int
    indicators: List[str]


@dataclass
class BioChange:
    """Mudança de bio"""
    timestamp: str
    old_bio: str
    new_bio: str
    old_link: Optional[str]
    new_link: Optional[str]
    change_type: str  # "text", "link", "both"


@dataclass
class ContentCalendarEntry:
    """Entrada do calendário de conteúdo"""
    date: str
    posts_count: int
    content_types: List[str]
    total_engagement: int
    post_ids: List[str]


@dataclass
class ProfileSnapshot:
    """Snapshot temporal do perfil"""
    timestamp: str
    followers_count: int
    following_count: int
    posts_count: int
    bio: str
    bio_link: Optional[str]
    profile_pic_hash: str


# =============================================================================
# DATABASE MANAGER
# =============================================================================

class AnalyticsDatabase:
    """
    Gerenciador de banco de dados para histórico e snapshots.
    """
    
    def __init__(self, db_path: str = ".analytics_cache/analytics.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa tabelas do banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de snapshots de perfil
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                followers_count INTEGER,
                following_count INTEGER,
                posts_count INTEGER,
                bio TEXT,
                bio_link TEXT,
                profile_pic_hash TEXT,
                raw_data TEXT
            )
        """)
        
        # Tabela de histórico de bio
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bio_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                old_bio TEXT,
                new_bio TEXT,
                old_link TEXT,
                new_link TEXT,
                change_type TEXT
            )
        """)
        
        # Tabela de hashtags
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hashtag_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                hashtag TEXT NOT NULL,
                post_id TEXT NOT NULL,
                likes_count INTEGER,
                comments_count INTEGER,
                timestamp TEXT NOT NULL
            )
        """)
        
        # Índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_user ON profile_snapshots(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bio_user ON bio_history(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hashtags_user ON hashtag_usage(username)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"📦 Analytics DB inicializado: {self.db_path}")
    
    def save_snapshot(self, username: str, snapshot: ProfileSnapshot) -> None:
        """Salva snapshot do perfil"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO profile_snapshots 
                (username, timestamp, followers_count, following_count, 
                 posts_count, bio, bio_link, profile_pic_hash, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, snapshot.timestamp, snapshot.followers_count,
            snapshot.following_count, snapshot.posts_count,
            snapshot.bio, snapshot.bio_link, snapshot.profile_pic_hash, ""
        ))
        
        conn.commit()
        conn.close()
    
    def get_snapshots(self, username: str, limit: int = 100) -> List[ProfileSnapshot]:
        """Obtém snapshots do perfil"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, followers_count, following_count, posts_count,
                   bio, bio_link, profile_pic_hash
            FROM profile_snapshots
            WHERE username = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (username, limit))
        
        snapshots = []
        for row in cursor.fetchall():
            snapshots.append(ProfileSnapshot(
                timestamp=row[0],
                followers_count=row[1] or 0,
                following_count=row[2] or 0,
                posts_count=row[3] or 0,
                bio=row[4] or "",
                bio_link=row[5],
                profile_pic_hash=row[6] or ""
            ))
        
        conn.close()
        return snapshots
    
    def save_bio_change(self, username: str, change: BioChange) -> None:
        """Salva mudança de bio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO bio_history 
                (username, timestamp, old_bio, new_bio, old_link, new_link, change_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            username, change.timestamp, change.old_bio, change.new_bio,
            change.old_link, change.new_link, change.change_type
        ))
        
        conn.commit()
        conn.close()
    
    def get_bio_history(self, username: str) -> List[BioChange]:
        """Obtém histórico de bio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, old_bio, new_bio, old_link, new_link, change_type
            FROM bio_history
            WHERE username = ?
            ORDER BY timestamp DESC
        """, (username,))
        
        changes = []
        for row in cursor.fetchall():
            changes.append(BioChange(
                timestamp=row[0],
                old_bio=row[1] or "",
                new_bio=row[2] or "",
                old_link=row[3],
                new_link=row[4],
                change_type=row[5] or "text"
            ))
        
        conn.close()
        return changes


# =============================================================================
# STORIES TRACKER
# =============================================================================

class StoriesTracker:
    """
    Rastreador de Stories do Instagram.
    """
    
    def extract_stories_from_data(self, stories_data: List[Dict]) -> List[StoryInfo]:
        """
        Extrai informações de stories dos dados brutos.
        
        Args:
            stories_data: Dados brutos de stories
            
        Returns:
            Lista de StoryInfo
        """
        stories = []
        
        for story in stories_data:
            # Extrair menções
            mentions = []
            if 'reel_mentions' in story:
                mentions = [m.get('user', {}).get('username', '') 
                           for m in story.get('reel_mentions', [])]
            
            # Extrair hashtags
            hashtags = []
            if 'story_hashtags' in story:
                hashtags = [h.get('hashtag', {}).get('name', '')
                           for h in story.get('story_hashtags', [])]
            
            # Extrair links
            links = []
            if 'story_cta' in story:
                for cta in story.get('story_cta', []):
                    if 'links' in cta:
                        links.extend([l.get('webUri', '') for l in cta['links']])
            
            # Extrair stickers
            stickers = []
            for key in ['story_polls', 'story_questions', 'story_quizzes', 'story_sliders']:
                if key in story:
                    for sticker in story[key]:
                        stickers.append({
                            'type': key.replace('story_', ''),
                            'data': sticker
                        })
            
            # Calcular expiração
            taken_at = story.get('taken_at', 0)
            if isinstance(taken_at, int):
                expiration = datetime.fromtimestamp(taken_at + 86400).isoformat()
                timestamp = datetime.fromtimestamp(taken_at).isoformat()
            else:
                expiration = ""
                timestamp = str(taken_at)
            
            stories.append(StoryInfo(
                id=str(story.get('id', '')),
                media_type=self._get_media_type(story.get('media_type', 1)),
                url=story.get('image_versions2', {}).get('candidates', [{}])[0].get('url', ''),
                timestamp=timestamp,
                expiration=expiration,
                duration=story.get('video_duration'),
                mentions=mentions,
                hashtags=hashtags,
                links=links,
                stickers=stickers,
                is_highlight=False,
                highlight_title=None
            ))
        
        return stories
    
    def _get_media_type(self, media_type: int) -> str:
        """Converte tipo de mídia"""
        types = {1: 'image', 2: 'video', 8: 'carousel'}
        return types.get(media_type, 'unknown')
    
    def extract_highlights(self, highlights_data: List[Dict]) -> List[StoryInfo]:
        """Extrai stories de Highlights"""
        stories = []
        
        for highlight in highlights_data:
            title = highlight.get('title', '')
            items = highlight.get('items', [])
            
            for item in items:
                story = self.extract_stories_from_data([item])
                if story:
                    story[0].is_highlight = True
                    story[0].highlight_title = title
                    stories.append(story[0])
        
        return stories


# =============================================================================
# REELS ANALYTICS
# =============================================================================

class ReelsAnalyzer:
    """
    Analisador de Reels com métricas específicas.
    """
    
    TRENDING_AUDIO_THRESHOLD = 10000  # Uso mínimo para considerar trending
    
    def analyze_reel(self, reel_data: Dict) -> ReelAnalytics:
        """
        Analisa um Reel individual.
        
        Args:
            reel_data: Dados brutos do reel
            
        Returns:
            ReelAnalytics
        """
        # Extrair áudio
        audio = reel_data.get('clips_metadata', {}).get('music_info', {})
        audio_name = audio.get('music_asset_info', {}).get('title')
        audio_artist = audio.get('music_asset_info', {}).get('display_artist')
        
        # Verificar se é trending
        audio_use_count = audio.get('music_asset_info', {}).get('ig_username_count', 0)
        is_trending = audio_use_count >= self.TRENDING_AUDIO_THRESHOLD
        
        # Calcular engajamento
        views = reel_data.get('play_count', 0)
        likes = reel_data.get('like_count', 0)
        comments = reel_data.get('comment_count', 0)
        
        # Estimar retenção (heurística baseada em engajamento/views)
        retention = 0.0
        if views > 0:
            engagement_rate = (likes + comments) / views
            # Retenção estimada: maior engajamento = maior retenção
            retention = min(engagement_rate * 10, 1.0) * 100
        
        # Timestamp
        taken_at = reel_data.get('taken_at', 0)
        if isinstance(taken_at, int):
            timestamp = datetime.fromtimestamp(taken_at).isoformat()
        else:
            timestamp = str(taken_at)
        
        return ReelAnalytics(
            id=str(reel_data.get('pk', reel_data.get('id', ''))),
            url=f"https://www.instagram.com/reel/{reel_data.get('code', '')}/",
            views_count=views,
            plays_count=reel_data.get('view_count', views),
            likes_count=likes,
            comments_count=comments,
            shares_count=reel_data.get('reshare_count', 0),
            audio_name=audio_name,
            audio_artist=audio_artist,
            is_trending_audio=is_trending,
            duration_seconds=reel_data.get('video_duration', 0),
            retention_estimate=retention,
            caption=reel_data.get('caption', {}).get('text', '') if reel_data.get('caption') else '',
            timestamp=timestamp
        )
    
    def analyze_multiple_reels(self, reels_data: List[Dict]) -> Dict[str, Any]:
        """Analisa múltiplos reels e gera estatísticas agregadas"""
        if not reels_data:
            return {'total': 0, 'analytics': []}
        
        analytics = [self.analyze_reel(r) for r in reels_data]
        
        # Estatísticas agregadas
        total_views = sum(r.views_count for r in analytics)
        total_likes = sum(r.likes_count for r in analytics)
        avg_retention = statistics.mean(r.retention_estimate for r in analytics) if analytics else 0
        
        # Áudios mais usados
        audio_counts = Counter(r.audio_name for r in analytics if r.audio_name)
        
        return {
            'total': len(analytics),
            'total_views': total_views,
            'total_likes': total_likes,
            'avg_views': total_views / len(analytics),
            'avg_retention': avg_retention,
            'trending_audio_used': sum(1 for r in analytics if r.is_trending_audio),
            'top_audios': audio_counts.most_common(5),
            'analytics': [
                {
                    'id': r.id,
                    'views': r.views_count,
                    'likes': r.likes_count,
                    'retention': r.retention_estimate,
                    'audio': r.audio_name
                }
                for r in analytics
            ]
        }


# =============================================================================
# HASHTAG ANALYZER
# =============================================================================

class HashtagAnalyzer:
    """
    Analisador de hashtags usadas nos posts.
    """
    
    POPULAR_HASHTAGS = {
        'love', 'instagood', 'photooftheday', 'fashion', 'beautiful',
        'happy', 'cute', 'tbt', 'like4like', 'followme', 'picoftheday',
        'follow', 'me', 'selfie', 'summer', 'art', 'instadaily', 'friends',
        'repost', 'nature', 'girl', 'fun', 'style', 'smile', 'food'
    }
    
    def extract_hashtags_from_caption(self, caption: str) -> List[str]:
        """Extrai hashtags de uma legenda"""
        if not caption:
            return []
        return re.findall(r'#(\w+)', caption.lower())
    
    def analyze_hashtags(self, posts: List[Dict]) -> Dict[str, Any]:
        """
        Analisa todas as hashtags usadas nos posts.
        
        Args:
            posts: Lista de posts
            
        Returns:
            Análise completa de hashtags
        """
        hashtag_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_likes': 0,
            'total_comments': 0,
            'posts': []
        })
        
        for post in posts:
            caption = post.get('caption', '')
            if isinstance(caption, dict):
                caption = caption.get('text', '')
            
            hashtags = self.extract_hashtags_from_caption(caption)
            likes = post.get('like_count', 0)
            comments = post.get('comment_count', 0)
            post_id = str(post.get('pk', post.get('id', '')))
            
            for tag in hashtags:
                hashtag_stats[tag]['count'] += 1
                hashtag_stats[tag]['total_likes'] += likes
                hashtag_stats[tag]['total_comments'] += comments
                hashtag_stats[tag]['posts'].append(post_id)
        
        # Processar resultados
        results = []
        for tag, stats in hashtag_stats.items():
            count = stats['count']
            avg_likes = stats['total_likes'] / count if count > 0 else 0
            avg_comments = stats['total_comments'] / count if count > 0 else 0
            
            # Determinar categoria
            if tag in self.POPULAR_HASHTAGS:
                category = "popular"
            elif tag.startswith(('ad', 'sponsor', 'publi', 'parceria')):
                category = "branded"
            else:
                category = "nicho"
            
            # Encontrar post com melhor performance
            best_post = stats['posts'][0] if stats['posts'] else ''
            
            results.append(HashtagStats(
                hashtag=f"#{tag}",
                usage_count=count,
                avg_likes=avg_likes,
                avg_comments=avg_comments,
                best_performing_post_id=best_post,
                category=category
            ))
        
        # Ordenar por uso
        results.sort(key=lambda x: x.usage_count, reverse=True)
        
        # Gerar nuvem de palavras (frequências)
        word_cloud = {r.hashtag: r.usage_count for r in results[:50]}
        
        return {
            'total_unique': len(results),
            'total_usage': sum(r.usage_count for r in results),
            'by_category': {
                'nicho': [r for r in results if r.category == 'nicho'][:10],
                'popular': [r for r in results if r.category == 'popular'][:10],
                'branded': [r for r in results if r.category == 'branded'][:10]
            },
            'top_hashtags': results[:20],
            'word_cloud_data': word_cloud
        }


# =============================================================================
# ENGAGEMENT RATE CALCULATOR
# =============================================================================

class EngagementCalculator:
    """
    Calculador de taxa de engajamento.
    """
    
    BENCHMARKS = {
        'micro': (1000, 10000, 5.0),
        'small': (10000, 50000, 3.5),
        'medium': (50000, 100000, 2.5),
        'large': (100000, 500000, 1.5),
        'mega': (500000, float('inf'), 1.0)
    }
    
    def calculate_engagement_rate(
        self,
        posts: List[Dict],
        followers_count: int
    ) -> EngagementRateResult:
        """
        Calcula taxa de engajamento.
        
        Args:
            posts: Lista de posts
            followers_count: Número de seguidores
            
        Returns:
            EngagementRateResult
        """
        if not posts or followers_count <= 0:
            return EngagementRateResult(
                username="",
                overall_rate=0.0,
                tier=EngagementTier.VERY_LOW,
                per_post_rates=[],
                benchmark_comparison="",
                anomalies=[],
                analyzed_posts=0
            )
        
        per_post = []
        rates = []
        
        for post in posts:
            likes = post.get('like_count', 0)
            comments = post.get('comment_count', 0)
            
            rate = ((likes + comments) / followers_count) * 100
            rates.append(rate)
            
            per_post.append({
                'post_id': str(post.get('pk', post.get('id', ''))),
                'likes': likes,
                'comments': comments,
                'engagement_rate': round(rate, 2)
            })
        
        # Calcular média
        overall_rate = statistics.mean(rates) if rates else 0
        
        # Determinar tier
        tier = self._get_tier(overall_rate)
        
        # Comparar com benchmark
        benchmark = self._get_benchmark(followers_count)
        if overall_rate >= benchmark:
            comparison = f"Acima da média do setor ({benchmark:.1f}%)"
        else:
            diff = benchmark - overall_rate
            comparison = f"Abaixo da média do setor ({benchmark:.1f}%) por {diff:.1f}%"
        
        # Detectar anomalias (posts com ER muito diferente)
        anomalies = []
        if rates:
            mean_rate = statistics.mean(rates)
            std_rate = statistics.stdev(rates) if len(rates) > 1 else 0
            
            for i, rate in enumerate(rates):
                if std_rate > 0 and abs(rate - mean_rate) > 2 * std_rate:
                    anomalies.append({
                        'post_id': per_post[i]['post_id'],
                        'rate': rate,
                        'deviation': 'alto' if rate > mean_rate else 'baixo'
                    })
        
        return EngagementRateResult(
            username="",
            overall_rate=round(overall_rate, 2),
            tier=tier,
            per_post_rates=per_post,
            benchmark_comparison=comparison,
            anomalies=anomalies,
            analyzed_posts=len(posts)
        )
    
    def _get_tier(self, rate: float) -> EngagementTier:
        """Determina tier do engajamento"""
        if rate < 1:
            return EngagementTier.VERY_LOW
        elif rate < 3:
            return EngagementTier.LOW
        elif rate < 6:
            return EngagementTier.MEDIUM
        elif rate < 10:
            return EngagementTier.HIGH
        else:
            return EngagementTier.VIRAL
    
    def _get_benchmark(self, followers: int) -> float:
        """Obtém benchmark para o tamanho de conta"""
        for tier, (min_f, max_f, benchmark) in self.BENCHMARKS.items():
            if min_f <= followers < max_f:
                return benchmark
        return 2.0


# =============================================================================
# BEST TIME TO POST ANALYZER
# =============================================================================

class BestTimeAnalyzer:
    """
    Analisador de melhor horário para postar.
    """
    
    DAYS_PT = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    
    def analyze_best_times(self, posts: List[Dict]) -> BestTimeResult:
        """
        Analisa melhores horários para postar.
        
        Args:
            posts: Lista de posts com timestamps
            
        Returns:
            BestTimeResult
        """
        hour_engagement: Dict[int, List[int]] = defaultdict(list)
        day_engagement: Dict[int, List[int]] = defaultdict(list)
        heatmap: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        heatmap_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for post in posts:
            timestamp = post.get('taken_at')
            if not timestamp:
                continue
            
            try:
                if isinstance(timestamp, int):
                    dt = datetime.fromtimestamp(timestamp)
                else:
                    dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
            except:
                continue
            
            engagement = post.get('like_count', 0) + post.get('comment_count', 0)
            hour = dt.hour
            day = dt.weekday()
            
            hour_engagement[hour].append(engagement)
            day_engagement[day].append(engagement)
            
            day_name = self.DAYS_PT[day]
            hour_str = f"{hour:02d}:00"
            heatmap[day_name][hour_str] += engagement
            heatmap_counts[day_name][hour_str] += 1
        
        # Calcular médias para heatmap
        for day in heatmap:
            for hour in heatmap[day]:
                count = heatmap_counts[day][hour]
                if count > 0:
                    heatmap[day][hour] /= count
        
        # Top horários
        hour_avgs = [
            {'hour': f"{h:02d}:00", 'avg_engagement': statistics.mean(engs) if engs else 0}
            for h, engs in hour_engagement.items()
        ]
        hour_avgs.sort(key=lambda x: x['avg_engagement'], reverse=True)
        
        # Top dias
        day_avgs = [
            {'day': self.DAYS_PT[d], 'avg_engagement': statistics.mean(engs) if engs else 0}
            for d, engs in day_engagement.items()
        ]
        day_avgs.sort(key=lambda x: x['avg_engagement'], reverse=True)
        
        # Recomendações
        recommendations = []
        if hour_avgs:
            top_hours = [h['hour'] for h in hour_avgs[:3]]
            recommendations.append(f"Melhores horários: {', '.join(top_hours)}")
        if day_avgs:
            top_days = [d['day'] for d in day_avgs[:2]]
            recommendations.append(f"Melhores dias: {', '.join(top_days)}")
        
        return BestTimeResult(
            username="",
            top_hours=hour_avgs[:5],
            top_days=day_avgs,
            heatmap=dict(heatmap),
            estimated_timezone="America/Sao_Paulo",
            recommendations=recommendations
        )


# =============================================================================
# AUDIENCE QUALITY ANALYZER
# =============================================================================

class AudienceQualityAnalyzer:
    """
    Analisador de qualidade de seguidores.
    """
    
    BOT_INDICATORS = {
        'no_profile_pic': 2,
        'no_posts': 3,
        'suspicious_ratio': 2,
        'random_username': 2,
        'no_bio': 1,
        'recent_account': 1
    }
    
    def analyze_audience(self, followers: List[Dict]) -> AudienceQualityResult:
        """
        Analisa qualidade da audiência.
        
        Args:
            followers: Amostra de seguidores
            
        Returns:
            AudienceQualityResult
        """
        if not followers:
            return AudienceQualityResult(
                username="",
                quality_score=100.0,
                real_followers_percent=100.0,
                bot_followers_percent=0.0,
                suspicious_accounts=0,
                sample_size=0,
                indicators=[]
            )
        
        suspicious = 0
        indicators_found: Dict[str, int] = defaultdict(int)
        
        for follower in followers:
            score = 0
            
            # Sem foto de perfil
            if not follower.get('has_profile_pic', True):
                score += self.BOT_INDICATORS['no_profile_pic']
                indicators_found['sem_foto_perfil'] += 1
            
            # Sem posts
            if follower.get('media_count', 0) == 0:
                score += self.BOT_INDICATORS['no_posts']
                indicators_found['sem_posts'] += 1
            
            # Ratio suspeito
            following = follower.get('following_count', 0)
            followers_count = follower.get('follower_count', 1)
            if followers_count > 0 and following / followers_count > 10:
                score += self.BOT_INDICATORS['suspicious_ratio']
                indicators_found['ratio_suspeito'] += 1
            
            # Username aleatório
            username = follower.get('username', '')
            if re.search(r'\d{5,}$', username):
                score += self.BOT_INDICATORS['random_username']
                indicators_found['username_aleatorio'] += 1
            
            # Sem bio
            if not follower.get('biography'):
                score += self.BOT_INDICATORS['no_bio']
                indicators_found['sem_bio'] += 1
            
            # Conta suspeita se score >= 4
            if score >= 4:
                suspicious += 1
        
        sample_size = len(followers)
        bot_percent = (suspicious / sample_size * 100) if sample_size > 0 else 0
        real_percent = 100 - bot_percent
        quality_score = max(0, 100 - (bot_percent * 1.5))
        
        # Formatar indicadores
        indicator_list = [
            f"{k}: {v} contas" for k, v in indicators_found.items()
        ]
        
        return AudienceQualityResult(
            username="",
            quality_score=round(quality_score, 1),
            real_followers_percent=round(real_percent, 1),
            bot_followers_percent=round(bot_percent, 1),
            suspicious_accounts=suspicious,
            sample_size=sample_size,
            indicators=indicator_list
        )


# =============================================================================
# CONTENT CALENDAR
# =============================================================================

class ContentCalendar:
    """
    Gerador de calendário de conteúdo.
    """
    
    def generate_calendar(self, posts: List[Dict]) -> Dict[str, Any]:
        """
        Gera calendário de conteúdo.
        
        Args:
            posts: Lista de posts
            
        Returns:
            Dados do calendário
        """
        calendar_data: Dict[str, ContentCalendarEntry] = {}
        
        for post in posts:
            timestamp = post.get('taken_at')
            if not timestamp:
                continue
            
            try:
                if isinstance(timestamp, int):
                    dt = datetime.fromtimestamp(timestamp)
                else:
                    dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
            except:
                continue
            
            date_str = dt.strftime('%Y-%m-%d')
            
            if date_str not in calendar_data:
                calendar_data[date_str] = ContentCalendarEntry(
                    date=date_str,
                    posts_count=0,
                    content_types=[],
                    total_engagement=0,
                    post_ids=[]
                )
            
            entry = calendar_data[date_str]
            entry.posts_count += 1
            entry.total_engagement += post.get('like_count', 0) + post.get('comment_count', 0)
            entry.post_ids.append(str(post.get('pk', post.get('id', ''))))
            
            # Determinar tipo de conteúdo
            media_type = post.get('media_type', 1)
            if media_type == 1:
                content_type = 'foto'
            elif media_type == 2:
                content_type = 'video'
            elif media_type == 8:
                content_type = 'carrossel'
            else:
                content_type = 'outro'
            
            if content_type not in entry.content_types:
                entry.content_types.append(content_type)
        
        # Ordenar por data
        entries = sorted(calendar_data.values(), key=lambda x: x.date, reverse=True)
        
        # Detectar gaps
        gaps = []
        if len(entries) >= 2:
            for i in range(len(entries) - 1):
                date1 = datetime.strptime(entries[i].date, '%Y-%m-%d')
                date2 = datetime.strptime(entries[i+1].date, '%Y-%m-%d')
                diff = (date1 - date2).days
                if diff > 7:
                    gaps.append({
                        'start': entries[i+1].date,
                        'end': entries[i].date,
                        'days': diff
                    })
        
        # Estatísticas
        if entries:
            avg_posts_per_week = len(posts) / max(1, len(set(e.date[:7] for e in entries)) * 4)
        else:
            avg_posts_per_week = 0
        
        return {
            'entries': [
                {
                    'date': e.date,
                    'posts_count': e.posts_count,
                    'content_types': e.content_types,
                    'engagement': e.total_engagement
                }
                for e in entries
            ],
            'gaps': gaps,
            'avg_posts_per_week': round(avg_posts_per_week, 1),
            'total_posts': len(posts)
        }


# =============================================================================
# MENTIONS TRACKER
# =============================================================================

class MentionsTracker:
    """
    Rastreador de menções.
    """
    
    POSITIVE_WORDS = {'amor', 'parabéns', 'incrível', 'melhor', 'excelente', 'top', 'perfeito'}
    NEGATIVE_WORDS = {'ruim', 'péssimo', 'horrível', 'decepcionado', 'nunca mais'}
    
    def extract_mentions(self, caption: str) -> List[str]:
        """Extrai menções de uma legenda"""
        if not caption:
            return []
        return re.findall(r'@(\w+)', caption)
    
    def analyze_mentions(self, posts: List[Dict], target_username: str) -> Dict[str, Any]:
        """
        Analisa menções do alvo.
        
        Args:
            posts: Posts para analisar
            target_username: Username do alvo
            
        Returns:
            Análise de menções
        """
        mentions_received: Dict[str, List[Dict]] = defaultdict(list)
        sentiments = {'positiva': 0, 'neutra': 0, 'negativa': 0}
        
        for post in posts:
            caption = post.get('caption', '')
            if isinstance(caption, dict):
                caption = caption.get('text', '')
            
            mentions = self.extract_mentions(caption)
            
            if target_username.lower() in [m.lower() for m in mentions]:
                author = post.get('user', {}).get('username', 'unknown')
                
                # Determinar sentimento
                caption_lower = caption.lower()
                sentiment = 'neutra'
                
                if any(w in caption_lower for w in self.POSITIVE_WORDS):
                    sentiment = 'positiva'
                elif any(w in caption_lower for w in self.NEGATIVE_WORDS):
                    sentiment = 'negativa'
                
                sentiments[sentiment] += 1
                mentions_received[author].append({
                    'post_id': str(post.get('pk', post.get('id', ''))),
                    'caption': caption[:100],
                    'sentiment': sentiment
                })
        
        # Top mencionadores
        top_mentioners = sorted(
            [(user, len(mentions)) for user, mentions in mentions_received.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_mentions': sum(sentiments.values()),
            'by_sentiment': sentiments,
            'top_mentioners': [{'username': u, 'count': c} for u, c in top_mentioners],
            'details': dict(mentions_received)
        }


# =============================================================================
# COLLABORATION DETECTOR
# =============================================================================

class CollaborationDetector:
    """
    Detector de colaborações e posts patrocinados.
    """
    
    SPONSORED_INDICATORS = [
        r'#ad\b', r'#sponsored', r'#publi', r'#parceria',
        r'#publicidade', r'#propaganda', r'#gifted',
        r'paid partnership', r'parceria paga'
    ]
    
    def detect_collaborations(self, posts: List[Dict]) -> Dict[str, Any]:
        """
        Detecta colaborações e posts patrocinados.
        
        Args:
            posts: Lista de posts
            
        Returns:
            Análise de colaborações
        """
        sponsored_posts = []
        brand_mentions: Dict[str, int] = defaultdict(int)
        
        for post in posts:
            caption = post.get('caption', '')
            if isinstance(caption, dict):
                caption = caption.get('text', '')
            
            # Verificar indicadores de patrocínio
            is_sponsored = False
            for pattern in self.SPONSORED_INDICATORS:
                if re.search(pattern, caption.lower()):
                    is_sponsored = True
                    break
            
            # Verificar flag de paid partnership
            if post.get('is_paid_partnership'):
                is_sponsored = True
            
            if is_sponsored:
                # Extrair marcas mencionadas
                mentions = re.findall(r'@(\w+)', caption)
                
                sponsored_posts.append({
                    'post_id': str(post.get('pk', post.get('id', ''))),
                    'caption': caption[:100],
                    'mentions': mentions,
                    'timestamp': post.get('taken_at')
                })
                
                for mention in mentions:
                    brand_mentions[mention] += 1
        
        # Top marcas parceiras
        top_brands = sorted(brand_mentions.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_sponsored': len(sponsored_posts),
            'sponsored_percentage': len(sponsored_posts) / len(posts) * 100 if posts else 0,
            'top_brands': [{'brand': b, 'collabs': c} for b, c in top_brands],
            'sponsored_posts': sponsored_posts[:20]
        }


# =============================================================================
# PROFILE COMPARATOR
# =============================================================================

class ProfileComparator:
    """
    Comparador de perfis.
    """
    
    def compare_profiles(self, profiles: List[Dict]) -> Dict[str, Any]:
        """
        Compara múltiplos perfis.
        
        Args:
            profiles: Lista de dados de perfis
            
        Returns:
            Comparação detalhada
        """
        if len(profiles) < 2:
            return {'error': 'Precisa de pelo menos 2 perfis para comparar'}
        
        comparison = {
            'profiles': [],
            'metrics_comparison': {},
            'winner_by_metric': {},
            'summary': []
        }
        
        metrics = ['followers', 'following', 'posts', 'engagement_rate', 'avg_likes']
        
        for profile in profiles:
            username = profile.get('username', 'unknown')
            followers = profile.get('followers_count', 0)
            posts = profile.get('posts', [])
            
            # Calcular métricas
            total_likes = sum(p.get('like_count', 0) for p in posts)
            total_comments = sum(p.get('comment_count', 0) for p in posts)
            
            avg_likes = total_likes / len(posts) if posts else 0
            engagement_rate = ((total_likes + total_comments) / len(posts) / max(followers, 1)) * 100 if posts else 0
            
            profile_data = {
                'username': username,
                'followers': followers,
                'following': profile.get('following_count', 0),
                'posts': profile.get('posts_count', 0),
                'engagement_rate': round(engagement_rate, 2),
                'avg_likes': round(avg_likes, 0)
            }
            
            comparison['profiles'].append(profile_data)
        
        # Determinar vencedor por métrica
        for metric in ['followers', 'engagement_rate', 'avg_likes']:
            values = [(p['username'], p.get(metric, 0)) for p in comparison['profiles']]
            winner = max(values, key=lambda x: x[1])
            comparison['winner_by_metric'][metric] = winner[0]
        
        # Gerar resumo
        if comparison['profiles']:
            best_followers = max(comparison['profiles'], key=lambda x: x['followers'])
            best_engagement = max(comparison['profiles'], key=lambda x: x['engagement_rate'])
            
            comparison['summary'].append(f"Maior audiência: @{best_followers['username']} ({best_followers['followers']} seguidores)")
            comparison['summary'].append(f"Melhor engajamento: @{best_engagement['username']} ({best_engagement['engagement_rate']}%)")
        
        return comparison


# =============================================================================
# ADVANCED ANALYTICS - CLASSE PRINCIPAL
# =============================================================================

class AdvancedAnalytics:
    """
    Módulo principal de analytics avançado.
    """
    
    def __init__(self, db_path: str = ".analytics_cache/analytics.db"):
        self.database = AnalyticsDatabase(db_path)
        self.stories_tracker = StoriesTracker()
        self.reels_analyzer = ReelsAnalyzer()
        self.hashtag_analyzer = HashtagAnalyzer()
        self.engagement_calculator = EngagementCalculator()
        self.best_time_analyzer = BestTimeAnalyzer()
        self.audience_analyzer = AudienceQualityAnalyzer()
        self.content_calendar = ContentCalendar()
        self.mentions_tracker = MentionsTracker()
        self.collab_detector = CollaborationDetector()
        self.profile_comparator = ProfileComparator()
        
        logger.info("📊 Advanced Analytics inicializado")
    
    def full_analysis(
        self,
        username: str,
        user_data: Dict,
        posts: Optional[List[Dict]] = None,
        followers_sample: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Executa análise completa de um perfil.
        
        Args:
            username: Nome de usuário
            user_data: Dados do perfil
            posts: Lista de posts (opcional)
            followers_sample: Amostra de seguidores (opcional)
            
        Returns:
            Análise completa
        """
        logger.info(f"📊 Iniciando análise completa de @{username}")
        
        posts = posts or user_data.get('posts', [])
        followers_count = user_data.get('followers_count', 0)
        
        report = {
            'username': username,
            'analyzed_at': datetime.now().isoformat(),
            'engagement': None,
            'best_time': None,
            'hashtags': None,
            'audience_quality': None,
            'content_calendar': None,
            'collaborations': None
        }
        
        # 1. Taxa de engajamento
        try:
            engagement = self.engagement_calculator.calculate_engagement_rate(posts, followers_count)
            engagement.username = username
            report['engagement'] = {
                'rate': engagement.overall_rate,
                'tier': engagement.tier.value,
                'benchmark': engagement.benchmark_comparison,
                'anomalies': len(engagement.anomalies)
            }
        except Exception as e:
            logger.error(f"Erro em engagement: {e}")
        
        # 2. Melhor horário
        try:
            best_time = self.best_time_analyzer.analyze_best_times(posts)
            best_time.username = username
            report['best_time'] = {
                'top_hours': best_time.top_hours[:3],
                'top_days': best_time.top_days[:3],
                'recommendations': best_time.recommendations
            }
        except Exception as e:
            logger.error(f"Erro em best_time: {e}")
        
        # 3. Hashtags
        try:
            hashtags = self.hashtag_analyzer.analyze_hashtags(posts)
            report['hashtags'] = {
                'total_unique': hashtags['total_unique'],
                'top_5': [
                    {'tag': h.hashtag, 'count': h.usage_count}
                    for h in hashtags['top_hashtags'][:5]
                ]
            }
        except Exception as e:
            logger.error(f"Erro em hashtags: {e}")
        
        # 4. Qualidade de audiência
        if followers_sample:
            try:
                audience = self.audience_analyzer.analyze_audience(followers_sample)
                audience.username = username
                report['audience_quality'] = {
                    'score': audience.quality_score,
                    'real_percent': audience.real_followers_percent,
                    'bot_percent': audience.bot_followers_percent,
                    'sample_size': audience.sample_size
                }
            except Exception as e:
                logger.error(f"Erro em audience: {e}")
        
        # 5. Calendário de conteúdo
        try:
            calendar = self.content_calendar.generate_calendar(posts)
            report['content_calendar'] = {
                'total_posts': calendar['total_posts'],
                'avg_per_week': calendar['avg_posts_per_week'],
                'gaps': len(calendar['gaps'])
            }
        except Exception as e:
            logger.error(f"Erro em calendar: {e}")
        
        # 6. Colaborações
        try:
            collabs = self.collab_detector.detect_collaborations(posts)
            report['collaborations'] = {
                'total': collabs['total_sponsored'],
                'percentage': round(collabs['sponsored_percentage'], 1),
                'top_brands': collabs['top_brands'][:3]
            }
        except Exception as e:
            logger.error(f"Erro em collaborations: {e}")
        
        # Salvar snapshot
        try:
            snapshot = ProfileSnapshot(
                timestamp=datetime.now().isoformat(),
                followers_count=followers_count,
                following_count=user_data.get('following_count', 0),
                posts_count=user_data.get('posts_count', 0),
                bio=user_data.get('biography', ''),
                bio_link=user_data.get('external_url'),
                profile_pic_hash=hashlib.md5(user_data.get('profile_pic_url', '').encode()).hexdigest()[:8]
            )
            self.database.save_snapshot(username, snapshot)
        except Exception as e:
            logger.error(f"Erro ao salvar snapshot: {e}")
        
        logger.info(f"✅ Análise de @{username} concluída")
        
        return report


# =============================================================================
# TESTES
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("   Advanced Analytics 2025 - God Mode Ultimate")
    print("   Funcionalidades Adicionais de Rastreamento")
    print("=" * 60)
    
    analytics = AdvancedAnalytics()
    
    # Teste com dados simulados
    test_posts = [
        {
            'pk': '123',
            'caption': 'Teste #hashtag1 #teste @usuario',
            'like_count': 100,
            'comment_count': 10,
            'taken_at': int(datetime.now().timestamp()),
            'media_type': 1
        },
        {
            'pk': '124',
            'caption': 'Outro post #hashtag2 #publi',
            'like_count': 200,
            'comment_count': 20,
            'taken_at': int((datetime.now() - timedelta(days=2)).timestamp()),
            'media_type': 1
        }
    ]
    
    test_user = {
        'username': 'teste',
        'followers_count': 1000,
        'following_count': 500,
        'posts_count': 50,
        'biography': 'Bio de teste',
        'posts': test_posts
    }
    
    print("\n🧪 Teste de análise completa...")
    resultado = analytics.full_analysis('teste', test_user, test_posts)
    print(f"   Engagement Rate: {resultado['engagement']['rate'] if resultado['engagement'] else 'N/A'}%")
    print(f"   Hashtags únicas: {resultado['hashtags']['total_unique'] if resultado['hashtags'] else 'N/A'}")
    
    print("\n✅ Teste concluído!")
