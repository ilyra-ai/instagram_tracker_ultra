"""
Analytics Module - Análise de dados e métricas

Exporta:
- SentimentAnalyzer: Análise de sentimento
- PredictiveEngine: Predição comportamental
- AdvancedAnalytics: Analytics avançado
"""

from .sentiment_analyzer import SentimentAnalyzer, get_sentiment_analyzer
from .predictive_engine import PredictiveEngine, get_predictive_engine
from .advanced_analytics import AdvancedAnalytics

__all__ = [
    'SentimentAnalyzer',
    'get_sentiment_analyzer',
    'PredictiveEngine',
    'get_predictive_engine',
    'AdvancedAnalytics'
]
