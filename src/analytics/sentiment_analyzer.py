"""
Analisador de Sentimento - Sistema de Inteligência Cognitiva
Implementa análise de sentimento com VADER + léxico PT-BR + emojis + nuances.

Autor: Instagram Intelligence System 2026
Versão: 1.0.0
Idioma: Português Brasileiro (pt-BR)
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


# Tentar importar VADER
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    SentimentIntensityAnalyzer = None

logger = logging.getLogger(__name__)


class SentimentCategory(Enum):
    """Categorias de sentimento"""
    MUITO_POSITIVO = "muito_positivo"
    POSITIVO = "positivo"
    NEUTRO = "neutro"
    NEGATIVO = "negativo"
    MUITO_NEGATIVO = "muito_negativo"


class EmotionalNuance(Enum):
    """Nuances emocionais detectáveis"""
    IRONIA = "ironia"
    SARCASMO = "sarcasmo"
    FLERTE = "flerte"
    AGRESSIVIDADE = "agressividade"
    ENTUSIASMO = "entusiasmo"
    TRISTEZA = "tristeza"
    RAIVA = "raiva"
    AMOR = "amor"
    MEDO = "medo"
    SURPRESA = "surpresa"
    NOJO = "nojo"
    NEUTRO = "neutro"


@dataclass
class SentimentResult:
    """Resultado completo da análise de sentimento"""
    texto_original: str
    polaridade: float  # -1.0 a 1.0
    subjetividade: float  # 0.0 a 1.0
    intensidade: float  # 0.0 a 1.0
    categoria: SentimentCategory
    nuances: List[EmotionalNuance] = field(default_factory=list)
    emojis_detectados: List[str] = field(default_factory=list)
    palavras_chave: List[str] = field(default_factory=list)
    confianca: float = 0.0  # 0.0 a 1.0
    detalhes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável"""
        return {
            'texto_original': self.texto_original[:100] + '...' if len(self.texto_original) > 100 else self.texto_original,
            'polaridade': round(self.polaridade, 3),
            'subjetividade': round(self.subjetividade, 3),
            'intensidade': round(self.intensidade, 3),
            'categoria': self.categoria.value,
            'nuances': [n.value for n in self.nuances],
            'emojis_detectados': self.emojis_detectados,
            'palavras_chave': self.palavras_chave,
            'confianca': round(self.confianca, 3),
            'detalhes': self.detalhes
        }


class LexicoPTBR:
    """
    Léxico customizado para Português Brasileiro.
    Contém palavras com valência positiva/negativa específicas do PT-BR.
    """
    
    # Palavras positivas em PT-BR (valência de 1.0 a 3.0)
    PALAVRAS_POSITIVAS = {
        # Muito positivas (3.0)
        'incrível': 3.0, 'maravilhoso': 3.0, 'fantástico': 3.0, 'espetacular': 3.0,
        'sensacional': 3.0, 'extraordinário': 3.0, 'perfeito': 3.0, 'excelente': 3.0,
        'magnífico': 3.0, 'sublime': 3.0, 'divino': 3.0, 'fenomenal': 3.0,
        'arrasou': 3.0, 'demais': 2.5, 'top': 2.5, 'show': 2.5,
        
        # Positivas (2.0)
        'bom': 2.0, 'boa': 2.0, 'ótimo': 2.5, 'ótima': 2.5, 'legal': 2.0,
        'bacana': 2.0, 'massa': 2.0, 'maneiro': 2.0, 'dahora': 2.0,
        'fofo': 2.0, 'fofa': 2.0, 'lindo': 2.5, 'linda': 2.5,
        'bonito': 2.0, 'bonita': 2.0, 'gato': 2.0, 'gata': 2.0,
        'amor': 2.5, 'amei': 2.5, 'adorei': 2.5, 'curti': 2.0,
        'feliz': 2.5, 'alegre': 2.0, 'contente': 2.0,
        
        # Levemente positivas (1.0-1.5)
        'ok': 1.0, 'tranquilo': 1.5, 'suave': 1.5, 'de boa': 1.5,
        'interessante': 1.5, 'agradável': 1.5, 'simpático': 1.5,
        'obrigado': 1.5, 'obrigada': 1.5, 'valeu': 1.5, 'parabéns': 2.0,
    }
    
    # Palavras negativas em PT-BR (valência de -1.0 a -3.0)
    PALAVRAS_NEGATIVAS = {
        # Muito negativas (-3.0)
        'horrível': -3.0, 'terrível': -3.0, 'péssimo': -3.0, 'péssima': -3.0,
        'nojento': -3.0, 'nojenta': -3.0, 'asqueroso': -3.0, 'repugnante': -3.0,
        'lixo': -3.0, 'merda': -3.0, 'porcaria': -2.5, 'droga': -2.5,
        'odeio': -3.0, 'detesto': -3.0, 'desprezo': -3.0,
        
        # Negativas (-2.0)
        'ruim': -2.0, 'mau': -2.0, 'má': -2.0, 'feio': -2.0, 'feia': -2.0,
        'chato': -2.0, 'chata': -2.0, 'irritante': -2.0, 'insuportável': -2.5,
        'triste': -2.0, 'decepcionado': -2.0, 'decepcionada': -2.0,
        'frustrado': -2.0, 'frustrada': -2.0, 'raiva': -2.0,
        'odiei': -2.5, 'detestei': -2.5, 'horrendo': -2.5,
        
        # Levemente negativas (-1.0 a -1.5)
        'não': -0.5, 'nunca': -1.0, 'nada': -0.5, 'sem': -0.5,
        'difícil': -1.0, 'complicado': -1.0, 'problema': -1.5,
        'errado': -1.5, 'falha': -1.5, 'erro': -1.5,
        'cansado': -1.0, 'cansada': -1.0, 'entediado': -1.0, 'entediada': -1.0,
    }
    
    # Intensificadores
    INTENSIFICADORES = {
        'muito': 1.5, 'demais': 1.5, 'extremamente': 2.0, 'super': 1.5,
        'mega': 1.5, 'ultra': 1.5, 'hiper': 1.5, 'absurdamente': 2.0,
        'incrivelmente': 1.8, 'totalmente': 1.5, 'completamente': 1.5,
        'bastante': 1.3, 'bem': 1.2, 'tão': 1.3,
    }
    
    # Negadores (invertem o sentimento)
    NEGADORES = {
        'não', 'nunca', 'jamais', 'nem', 'nenhum', 'nenhuma',
        'nada', 'tampouco', 'sequer',
    }
    
    # Gírias e expressões brasileiras
    GIRIAS_POSITIVAS = {
        'top demais': 3.0, 'muito bom': 2.5, 'show de bola': 3.0,
        'da hora': 2.5, 'firmeza': 2.0, 'suave na nave': 2.0,
        'de boa': 1.5, 'na paz': 1.5, 'fechou': 2.0,
        'tá on': 2.0, 'brabo': 2.5, 'brabíssimo': 3.0,
        'mito': 2.5, 'fera': 2.5, 'craque': 2.5,
    }
    
    GIRIAS_NEGATIVAS = {
        'que merda': -3.0, 'uma bosta': -3.0, 'foda-se': -2.5,
        'que saco': -2.0, 'pé no saco': -2.0, 'mala': -2.0,
        'vacilão': -2.0, 'vacilona': -2.0, 'otário': -2.5, 'otária': -2.5,
        'babaca': -2.5, 'imbecil': -2.5, 'idiota': -2.5,
    }


class EmojiSentimentMapper:
    """
    Mapeamento de emojis para sentimento.
    Cada emoji tem uma valência associada.
    """
    
    # Emojis positivos
    EMOJIS_POSITIVOS = {
        # Rostos felizes
        '😀': 2.5, '😃': 2.5, '😄': 2.5, '😁': 2.5, '😆': 2.5,
        '😊': 2.0, '🙂': 1.5, '☺️': 2.0, '😇': 2.0, '🥰': 3.0,
        '😍': 3.0, '🤩': 3.0, '😘': 2.5, '😗': 2.0, '😚': 2.0, '😙': 2.0,
        
        # Amor/Coração
        '❤️': 3.0, '🧡': 2.5, '💛': 2.5, '💚': 2.5, '💙': 2.5, '💜': 2.5,
        '🖤': 2.0, '🤍': 2.0, '🤎': 2.0, '💕': 3.0, '💞': 3.0, '💓': 2.5,
        '💗': 2.5, '💖': 3.0, '💘': 2.5, '💝': 2.5,
        
        # Gestos positivos
        '👍': 2.0, '👏': 2.5, '🙌': 2.5, '🤝': 2.0, '✌️': 2.0,
        '🤟': 2.0, '🤘': 2.0, '👌': 2.0, '💪': 2.0,
        
        # Celebração
        '🎉': 3.0, '🎊': 3.0, '🎈': 2.0, '🎁': 2.5, '🏆': 3.0,
        '🥇': 3.0, '⭐': 2.5, '🌟': 2.5, '✨': 2.0,
        
        # Risos
        '😂': 2.5, '🤣': 2.5, '😹': 2.5,
    }
    
    # Emojis negativos
    EMOJIS_NEGATIVOS = {
        # Rostos tristes/irritados
        '😢': -2.0, '😭': -2.5, '😞': -2.0, '😔': -2.0, '😟': -1.5,
        '🙁': -1.5, '☹️': -2.0, '😣': -2.0, '😖': -2.0, '😫': -2.0,
        '😩': -2.0, '🥺': -1.5, '😤': -2.0, '😠': -2.5, '😡': -3.0,
        '🤬': -3.0, '😈': -2.0, '👿': -2.5,
        
        # Gestos negativos
        '👎': -2.0, '🖕': -3.0,
        
        # Outros negativos
        '💔': -2.5, '😱': -2.0, '😰': -2.0, '😨': -2.0, '😥': -2.0,
        '🤢': -2.5, '🤮': -3.0, '💀': -2.0, '☠️': -2.0,
    }
    
    # Emojis de flerte
    EMOJIS_FLERTE = {
        '😏': 2.0, '😉': 2.0, '😜': 2.0, '😘': 2.5, '🥰': 2.5,
        '😍': 3.0, '🔥': 2.5, '💋': 2.5, '😈': 1.5,
    }
    
    # Emojis irônicos/sarcásticos
    EMOJIS_IRONICOS = {
        '😏': 1.0, '🙄': -1.0, '😒': -1.5, '🤷': 0.0,
        '👀': 0.5, '💅': 1.0,
    }

    @classmethod
    def get_emoji_sentiment(cls, emoji: str) -> Tuple[float, Optional[str]]:
        """
        Retorna a valência de um emoji e seu tipo.
        
        Returns:
            Tuple[valência, tipo] onde tipo pode ser 'positivo', 'negativo', 'flerte', 'ironico'
        """
        if emoji in cls.EMOJIS_POSITIVOS:
            return (cls.EMOJIS_POSITIVOS[emoji], 'positivo')
        elif emoji in cls.EMOJIS_NEGATIVOS:
            return (cls.EMOJIS_NEGATIVOS[emoji], 'negativo')
        elif emoji in cls.EMOJIS_FLERTE:
            return (cls.EMOJIS_FLERTE[emoji], 'flerte')
        elif emoji in cls.EMOJIS_IRONICOS:
            return (cls.EMOJIS_IRONICOS[emoji], 'ironico')
        return (0.0, None)


class NuanceDetector:
    """
    Detector de nuances emocionais no texto.
    Identifica ironia, sarcasmo, flerte, agressividade, etc.
    """
    
    # Padrões de ironia/sarcasmo
    PADROES_IRONIA = [
        r'(?i)\bótimo\b.*\bnão\b',
        r'(?i)\bque\s+(?:legal|maravilha|ótimo)\b.*(?:né|hein|viu)',
        r'(?i)\bparabéns\b.*(?:pelo|por)\s+(?:nada|fracasso)',
        r'(?i)\badorei\b.*(?:mesmo|muito)\s+(?:não|nunca)',
        r'(?i)\bclaro\s+que\s+(?:sim|não)\b',
        r'(?i)\bsó\s+que\s+não\b',
        r'(?i)\bquem\s+(?:diria|imaginaria)\b',
        r'(?i)\b(?:realmente|certamente)\b.*\bironia\b',
    ]
    
    # Padrões de flerte
    PADROES_FLERTE = [
        r'(?i)\b(?:lindo|linda|gato|gata|bonito|bonita)\b',
        r'(?i)\b(?:te\s+amo|te\s+adoro|meu\s+amor|minha\s+vida)\b',
        r'(?i)\b(?:saudade|quero\s+te\s+ver)\b',
        r'(?i)\b(?:gostoso|gostosa|delícia)\b',
        r'(?i)(?:😍|🥰|😘|💋|🔥|❤️)',
    ]
    
    # Padrões de agressividade
    PADROES_AGRESSIVIDADE = [
        r'(?i)\b(?:odeio|detesto|desprezo)\b',
        r'(?i)\b(?:idiota|imbecil|babaca|otário|cretino)\b',
        r'(?i)\b(?:vai\s+(?:se\s+foder|tomar)|foda-se)\b',
        r'(?i)\b(?:matar|morrer|destruir|acabar\s+com)\b',
        r'(?i)(?:🤬|😡|👿|🖕)',
    ]
    
    # Padrões de entusiasmo
    PADROES_ENTUSIASMO = [
        r'(?i)\b(?:incrível|maravilhoso|fantástico|sensacional)\b',
        r'(?i)!{2,}',  # Múltiplas exclamações
        r'(?i)\b(?:demais|muito\s+bom|perfeito)\b',
        r'(?i)(?:🎉|🎊|🙌|✨|🔥)',
    ]
    
    # Padrões de tristeza
    PADROES_TRISTEZA = [
        r'(?i)\b(?:triste|deprimido|deprimida|arrasado|arrasada)\b',
        r'(?i)\b(?:chorar|chorando|lágrimas)\b',
        r'(?i)\b(?:saudade|falta|sinto\s+falta)\b',
        r'(?i)\b(?:sozinho|sozinha|abandonado|abandonada)\b',
        r'(?i)(?:😢|😭|💔|😞)',
    ]
    
    @classmethod
    def detect_nuances(cls, texto: str, emojis: List[str]) -> List[EmotionalNuance]:
        """
        Detecta nuances emocionais no texto.
        
        Args:
            texto: Texto a analisar
            emojis: Lista de emojis encontrados
            
        Returns:
            Lista de nuances detectadas
        """
        nuances = []
        texto_lower = texto.lower()
        
        # Verificar ironia
        for padrao in cls.PADROES_IRONIA:
            if re.search(padrao, texto):
                nuances.append(EmotionalNuance.IRONIA)
                break
        
        # Se há muitos emojis irônicos
        emojis_ironicos = sum(1 for e in emojis if e in EmojiSentimentMapper.EMOJIS_IRONICOS)
        if emojis_ironicos >= 2:
            if EmotionalNuance.IRONIA not in nuances:
                nuances.append(EmotionalNuance.SARCASMO)
        
        # Verificar flerte
        for padrao in cls.PADROES_FLERTE:
            if re.search(padrao, texto):
                nuances.append(EmotionalNuance.FLERTE)
                break
        
        # Verificar agressividade
        for padrao in cls.PADROES_AGRESSIVIDADE:
            if re.search(padrao, texto):
                nuances.append(EmotionalNuance.AGRESSIVIDADE)
                break
        
        # Verificar entusiasmo
        for padrao in cls.PADROES_ENTUSIASMO:
            if re.search(padrao, texto):
                nuances.append(EmotionalNuance.ENTUSIASMO)
                break
        
        # Verificar tristeza
        for padrao in cls.PADROES_TRISTEZA:
            if re.search(padrao, texto):
                nuances.append(EmotionalNuance.TRISTEZA)
                break
        
        # Se nenhuma nuance foi detectada
        if not nuances:
            nuances.append(EmotionalNuance.NEUTRO)
        
        return nuances


class SentimentAnalyzer:
    """
    Analisador de Sentimento principal.
    Combina VADER, léxico PT-BR, emojis e detecção de nuances.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Inicializar VADER se disponível
        if VADER_AVAILABLE:
            self.vader = SentimentIntensityAnalyzer()
            # Adicionar léxico PT-BR ao VADER
            self._extend_vader_lexicon()
            self.logger.info("✅ VADER inicializado com léxico PT-BR")
        else:
            self.vader = None
            self.logger.warning("⚠️ VADER não disponível. Usando análise baseada em léxico.")
        
        # Regex para extrair emojis
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # símbolos & pictogramas
            "\U0001F680-\U0001F6FF"  # transporte & mapas
            "\U0001F1E0-\U0001F1FF"  # bandeiras
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # outros
            "]+",
            flags=re.UNICODE
        )
    
    def _extend_vader_lexicon(self):
        """Adiciona palavras do léxico PT-BR ao VADER"""
        if not self.vader:
            return
        
        # Adicionar palavras positivas
        for palavra, valencia in LexicoPTBR.PALAVRAS_POSITIVAS.items():
            self.vader.lexicon[palavra] = valencia
        
        # Adicionar palavras negativas
        for palavra, valencia in LexicoPTBR.PALAVRAS_NEGATIVAS.items():
            self.vader.lexicon[palavra] = valencia
        
        # Adicionar gírias
        for expressao, valencia in LexicoPTBR.GIRIAS_POSITIVAS.items():
            self.vader.lexicon[expressao] = valencia
        
        for expressao, valencia in LexicoPTBR.GIRIAS_NEGATIVAS.items():
            self.vader.lexicon[expressao] = valencia
        
        self.logger.debug(f"Léxico VADER estendido com {len(LexicoPTBR.PALAVRAS_POSITIVAS) + len(LexicoPTBR.PALAVRAS_NEGATIVAS)} palavras PT-BR")
    
    def _extract_emojis(self, texto: str) -> List[str]:
        """Extrai todos os emojis do texto"""
        emojis = self.emoji_pattern.findall(texto)
        # Flatten: cada caractere emoji separado
        all_emojis = []
        for emoji_group in emojis:
            all_emojis.extend(list(emoji_group))
        return all_emojis
    
    def _calculate_emoji_sentiment(self, emojis: List[str]) -> Tuple[float, List[str]]:
        """
        Calcula sentimento baseado em emojis.
        
        Returns:
            Tuple[polaridade_emoji, tipos_detectados]
        """
        if not emojis:
            return (0.0, [])
        
        total_valence = 0.0
        tipos = []
        
        for emoji in emojis:
            valence, tipo = EmojiSentimentMapper.get_emoji_sentiment(emoji)
            total_valence += valence
            if tipo:
                tipos.append(tipo)
        
        # Média ponderada
        avg_valence = total_valence / len(emojis) if emojis else 0.0
        
        return (avg_valence, tipos)
    
    def _analyze_with_lexicon(self, texto: str) -> Dict[str, float]:
        """
        Análise baseada no léxico PT-BR (fallback quando VADER não disponível).
        """
        palavras = texto.lower().split()
        
        pos_score = 0.0
        neg_score = 0.0
        neu_count = 0
        intensificador_ativo = 1.0
        negador_ativo = False
        
        for i, palavra in enumerate(palavras):
            # Verificar intensificadores
            if palavra in LexicoPTBR.INTENSIFICADORES:
                intensificador_ativo = LexicoPTBR.INTENSIFICADORES[palavra]
                continue
            
            # Verificar negadores
            if palavra in LexicoPTBR.NEGADORES:
                negador_ativo = True
                continue
            
            # Verificar palavras positivas
            if palavra in LexicoPTBR.PALAVRAS_POSITIVAS:
                score = LexicoPTBR.PALAVRAS_POSITIVAS[palavra] * intensificador_ativo
                if negador_ativo:
                    neg_score += score
                    negador_ativo = False
                else:
                    pos_score += score
                intensificador_ativo = 1.0
                continue
            
            # Verificar palavras negativas
            if palavra in LexicoPTBR.PALAVRAS_NEGATIVAS:
                score = abs(LexicoPTBR.PALAVRAS_NEGATIVAS[palavra]) * intensificador_ativo
                if negador_ativo:
                    pos_score += score
                    negador_ativo = False
                else:
                    neg_score += score
                intensificador_ativo = 1.0
                continue
            
            neu_count += 1
            intensificador_ativo = 1.0
            negador_ativo = False
        
        # Normalizar scores
        total = pos_score + neg_score + neu_count
        if total == 0:
            return {'pos': 0.0, 'neg': 0.0, 'neu': 1.0, 'compound': 0.0}
        
        pos_normalized = pos_score / total
        neg_normalized = neg_score / total
        neu_normalized = neu_count / total
        
        # Compound score
        compound = (pos_score - neg_score) / (pos_score + neg_score + 1)
        compound = max(-1.0, min(1.0, compound))  # Limitar entre -1 e 1
        
        return {
            'pos': pos_normalized,
            'neg': neg_normalized,
            'neu': neu_normalized,
            'compound': compound
        }
    
    def _calculate_subjectivity(self, texto: str, scores: Dict[str, float]) -> float:
        """
        Calcula subjetividade do texto (0 = objetivo, 1 = subjetivo).
        """
        # Textos com mais palavras de sentimento são mais subjetivos
        subjectivity = 1.0 - scores.get('neu', 0.5)
        
        # Presença de pronomes pessoais aumenta subjetividade
        pronomes = ['eu', 'meu', 'minha', 'me', 'nós', 'nosso', 'nossa']
        pronome_count = sum(1 for p in pronomes if p in texto.lower())
        if pronome_count > 0:
            subjectivity = min(1.0, subjectivity + 0.1 * pronome_count)
        
        return subjectivity
    
    def _calculate_intensity(self, scores: Dict[str, float], emojis: List[str]) -> float:
        """
        Calcula intensidade emocional do texto.
        """
        # Compound absoluto indica intensidade
        compound_intensity = abs(scores.get('compound', 0))
        
        # Mais emojis = mais intensidade
        emoji_intensity = min(1.0, len(emojis) * 0.1)
        
        # Múltiplas exclamações/interrogações
        # (já considerado em outros lugares, aqui apenas combinamos)
        
        return min(1.0, (compound_intensity + emoji_intensity) / 2)
    
    def _categorize_sentiment(self, polaridade: float) -> SentimentCategory:
        """Categoriza o sentimento baseado na polaridade"""
        if polaridade >= 0.6:
            return SentimentCategory.MUITO_POSITIVO
        elif polaridade >= 0.2:
            return SentimentCategory.POSITIVO
        elif polaridade >= -0.2:
            return SentimentCategory.NEUTRO
        elif polaridade >= -0.6:
            return SentimentCategory.NEGATIVO
        else:
            return SentimentCategory.MUITO_NEGATIVO
    
    def _extract_keywords(self, texto: str) -> List[str]:
        """Extrai palavras-chave relacionadas a sentimento"""
        palavras = texto.lower().split()
        keywords = []
        
        all_sentiment_words = set(LexicoPTBR.PALAVRAS_POSITIVAS.keys()) | set(LexicoPTBR.PALAVRAS_NEGATIVAS.keys())
        
        for palavra in palavras:
            # Limpar pontuação
            palavra_limpa = re.sub(r'[^\w]', '', palavra)
            if palavra_limpa in all_sentiment_words:
                keywords.append(palavra_limpa)
        
        return keywords[:10]  # Limitar a 10 keywords
    
    def analyze(self, texto: str) -> SentimentResult:
        """
        Analisa o sentimento de um texto.
        
        Args:
            texto: Texto a ser analisado
            
        Returns:
            SentimentResult com análise completa
        """
        if not texto or not texto.strip():
            return SentimentResult(
                texto_original=texto or "",
                polaridade=0.0,
                subjetividade=0.0,
                intensidade=0.0,
                categoria=SentimentCategory.NEUTRO,
                confianca=0.0
            )
        
        # Extrair emojis
        emojis = self._extract_emojis(texto)
        emoji_sentiment, emoji_tipos = self._calculate_emoji_sentiment(emojis)
        
        # Analisar texto (VADER ou léxico)
        if self.vader:
            scores = self.vader.polarity_scores(texto)
        else:
            scores = self._analyze_with_lexicon(texto)
        
        # Combinar sentimento do texto com emojis
        text_compound = scores.get('compound', 0.0)
        if emojis:
            # Peso: texto 70%, emojis 30%
            combined_polaridade = (text_compound * 0.7) + (emoji_sentiment / 3.0 * 0.3)
        else:
            combined_polaridade = text_compound
        
        # Limitar entre -1 e 1
        combined_polaridade = max(-1.0, min(1.0, combined_polaridade))
        
        # Calcular subjetividade
        subjetividade = self._calculate_subjectivity(texto, scores)
        
        # Calcular intensidade
        intensidade = self._calculate_intensity(scores, emojis)
        
        # Categorizar
        categoria = self._categorize_sentiment(combined_polaridade)
        
        # Detectar nuances
        nuances = NuanceDetector.detect_nuances(texto, emojis)
        
        # Ajustar polaridade se ironia detectada
        if EmotionalNuance.IRONIA in nuances or EmotionalNuance.SARCASMO in nuances:
            # Ironia pode inverter o sentimento aparente
            combined_polaridade = combined_polaridade * 0.5  # Reduzir confiança
        
        # Extrair keywords
        keywords = self._extract_keywords(texto)
        
        # Calcular confiança
        confianca = self._calculate_confidence(texto, scores, emojis, nuances)
        
        return SentimentResult(
            texto_original=texto,
            polaridade=combined_polaridade,
            subjetividade=subjetividade,
            intensidade=intensidade,
            categoria=categoria,
            nuances=nuances,
            emojis_detectados=emojis,
            palavras_chave=keywords,
            confianca=confianca,
            detalhes={
                'vader_scores': scores,
                'emoji_sentiment': emoji_sentiment,
                'emoji_tipos': emoji_tipos,
                'vader_disponivel': VADER_AVAILABLE
            }
        )
    
    def _calculate_confidence(self, texto: str, scores: Dict, emojis: List, nuances: List) -> float:
        """Calcula confiança na análise"""
        confidence = 0.5  # Base
        
        # Texto mais longo = mais confiança
        word_count = len(texto.split())
        if word_count >= 10:
            confidence += 0.1
        if word_count >= 20:
            confidence += 0.1
        
        # VADER disponível aumenta confiança
        if VADER_AVAILABLE:
            confidence += 0.1
        
        # Presença de emojis ajuda
        if emojis:
            confidence += 0.1
        
        # Nuances de ironia reduzem confiança
        if EmotionalNuance.IRONIA in nuances:
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def analyze_batch(self, textos: List[str]) -> List[SentimentResult]:
        """
        Analisa múltiplos textos.
        
        Args:
            textos: Lista de textos
            
        Returns:
            Lista de SentimentResult
        """
        return [self.analyze(texto) for texto in textos]
    
    def get_aggregate_sentiment(self, results: List[SentimentResult]) -> Dict[str, Any]:
        """
        Calcula sentimento agregado de múltiplas análises.
        
        Args:
            results: Lista de SentimentResult
            
        Returns:
            Dicionário com métricas agregadas
        """
        if not results:
            return {
                'media_polaridade': 0.0,
                'media_subjetividade': 0.0,
                'media_intensidade': 0.0,
                'categoria_dominante': 'neutro',
                'total_analisados': 0
            }
        
        polaridades = [r.polaridade for r in results]
        subjetividades = [r.subjetividade for r in results]
        intensidades = [r.intensidade for r in results]
        
        # Contar categorias
        categoria_counts = {}
        for r in results:
            cat = r.categoria.value
            categoria_counts[cat] = categoria_counts.get(cat, 0) + 1
        
        categoria_dominante = max(categoria_counts, key=categoria_counts.get)
        
        # Contar nuances
        nuance_counts = {}
        for r in results:
            for n in r.nuances:
                nuance_counts[n.value] = nuance_counts.get(n.value, 0) + 1
        
        return {
            'media_polaridade': sum(polaridades) / len(polaridades),
            'media_subjetividade': sum(subjetividades) / len(subjetividades),
            'media_intensidade': sum(intensidades) / len(intensidades),
            'polaridade_min': min(polaridades),
            'polaridade_max': max(polaridades),
            'categoria_dominante': categoria_dominante,
            'distribuicao_categorias': categoria_counts,
            'distribuicao_nuances': nuance_counts,
            'total_analisados': len(results)
        }


# =============================================================================
# INSTÂNCIA GLOBAL (SINGLETON)
# =============================================================================

_analyzer_instance: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Retorna instância singleton do analisador"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SentimentAnalyzer()
    return _analyzer_instance


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    analyzer = get_sentiment_analyzer()
    
    # Textos de teste
    textos_teste = [
        "Adorei esse post! Muito lindo! 😍❤️",
        "Que merda, isso é horrível 😡",
        "Que legal... não mesmo 🙄",
        "Você é linda demais! 🔥😘",
        "Estou muito triste hoje 😢💔",
        "Ok, tranquilo",
        "INCRÍVEL!!! MELHOR COISA DO MUNDO!!! 🎉🎊✨",
        "Vai tomar no cu seu idiota 🤬",
        "Nossa que show demais, arrasou! 👏👏",
        "Saudade de você meu amor 🥺❤️",
    ]
    
    print("\n" + "="*60)
    print("TESTE DO ANALISADOR DE SENTIMENTO PT-BR")
    print("="*60 + "\n")
    
    results = []
    for texto in textos_teste:
        result = analyzer.analyze(texto)
        results.append(result)
        
        print(f"Texto: {texto}")
        print(f"  Polaridade: {result.polaridade:.2f}")
        print(f"  Categoria: {result.categoria.value}")
        print(f"  Nuances: {[n.value for n in result.nuances]}")
        print(f"  Emojis: {result.emojis_detectados}")
        print(f"  Confiança: {result.confianca:.2f}")
        print()
    
    # Análise agregada
    print("="*60)
    print("ANÁLISE AGREGADA")
    print("="*60)
    agregado = analyzer.get_aggregate_sentiment(results)
    for key, value in agregado.items():
        print(f"  {key}: {value}")
