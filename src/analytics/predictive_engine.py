"""
Motor Preditivo - Modelagem Comportamental e Análise de Séries Temporais
Implementa análise preditiva de padrões de atividade de usuários.

Autor: Instagram Intelligence System 2026
Versão: 1.0.0
Idioma: Português Brasileiro (pt-BR)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import math
import json

# Tentar importar bibliotecas de análise
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from scipy import stats
    from scipy.signal import find_peaks
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    stats = None

try:
    import statsmodels.api as sm
    from statsmodels.tsa.seasonal import seasonal_decompose
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    sm = None

logger = logging.getLogger(__name__)


@dataclass
class AtividadeTemporal:
    """Representa uma atividade com timestamp"""
    tipo: str  # 'post', 'like', 'comment', 'story'
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class PadraoHorario:
    """Padrão de atividade por hora"""
    hora: int  # 0-23
    frequencia: int  # Número de atividades
    probabilidade: float  # 0.0 a 1.0
    desvio_padrao: float = 0.0
    

@dataclass
class PadraoDiario:
    """Padrão de atividade por dia da semana"""
    dia_semana: int  # 0=Segunda, 6=Domingo
    nome_dia: str
    frequencia: int
    probabilidade: float
    media_atividades: float = 0.0


@dataclass
class PrevisaoAtividade:
    """Resultado de previsão de atividade"""
    data_hora: datetime
    probabilidade: float  # 0.0 a 1.0
    confianca: float  # 0.0 a 1.0
    tipo_previsto: Optional[str] = None


@dataclass
class AnalisePrevisibilidade:
    """Resultado completo da análise de previsibilidade"""
    username: str
    score_previsibilidade: float  # 0 a 100
    nivel_previsibilidade: str  # 'baixo', 'medio', 'alto', 'muito_alto'
    padroes_horarios: List[PadraoHorario] = field(default_factory=list)
    padroes_diarios: List[PadraoDiario] = field(default_factory=list)
    horarios_pico: List[int] = field(default_factory=list)
    dias_pico: List[str] = field(default_factory=list)
    intervalo_medio_posts: Optional[float] = None  # em horas
    proximas_previsoes: List[PrevisaoAtividade] = field(default_factory=list)
    tendencia: str = 'estavel'  # 'crescente', 'decrescente', 'estavel'
    sazonalidade_detectada: bool = False
    detalhes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável"""
        return {
            'username': self.username,
            'score_previsibilidade': round(self.score_previsibilidade, 2),
            'nivel_previsibilidade': self.nivel_previsibilidade,
            'padroes_horarios': [
                {'hora': p.hora, 'frequencia': p.frequencia, 'probabilidade': round(p.probabilidade, 3)}
                for p in self.padroes_horarios
            ],
            'padroes_diarios': [
                {'dia': p.nome_dia, 'frequencia': p.frequencia, 'probabilidade': round(p.probabilidade, 3)}
                for p in self.padroes_diarios
            ],
            'horarios_pico': self.horarios_pico,
            'dias_pico': self.dias_pico,
            'intervalo_medio_posts_horas': round(self.intervalo_medio_posts, 2) if self.intervalo_medio_posts else None,
            'proximas_previsoes': [
                {
                    'data_hora': p.data_hora.isoformat(),
                    'probabilidade': round(p.probabilidade, 3),
                    'confianca': round(p.confianca, 3)
                }
                for p in self.proximas_previsoes
            ],
            'tendencia': self.tendencia,
            'sazonalidade_detectada': self.sazonalidade_detectada,
            'detalhes': self.detalhes
        }


class AnalisadorTemporalBase:
    """
    Analisador base que funciona sem dependências externas.
    Usado como fallback quando numpy/scipy não estão disponíveis.
    """
    
    @staticmethod
    def calcular_media(valores: List[float]) -> float:
        """Calcula média aritmética"""
        if not valores:
            return 0.0
        return sum(valores) / len(valores)
    
    @staticmethod
    def calcular_desvio_padrao(valores: List[float]) -> float:
        """Calcula desvio padrão"""
        if len(valores) < 2:
            return 0.0
        media = sum(valores) / len(valores)
        variancia = sum((x - media) ** 2 for x in valores) / len(valores)
        return math.sqrt(variancia)
    
    @staticmethod
    def calcular_coeficiente_variacao(valores: List[float]) -> float:
        """Calcula coeficiente de variação (CV = desvio/media)"""
        if not valores:
            return 0.0
        media = sum(valores) / len(valores)
        if media == 0:
            return 0.0
        desvio = AnalisadorTemporalBase.calcular_desvio_padrao(valores)
        return desvio / media
    
    @staticmethod
    def encontrar_picos(valores: List[float], threshold: float = 0.5) -> List[int]:
        """Encontra índices de picos nos dados"""
        if len(valores) < 3:
            return []
        
        max_val = max(valores) if valores else 0
        if max_val == 0:
            return []
        
        threshold_abs = max_val * threshold
        picos = []
        
        for i in range(1, len(valores) - 1):
            if valores[i] > valores[i-1] and valores[i] > valores[i+1]:
                if valores[i] >= threshold_abs:
                    picos.append(i)
        
        return picos


class PredictiveEngine:
    """
    Motor de análise preditiva comportamental.
    
    Funcionalidades:
    - Análise de padrões temporais de atividade
    - Detecção de horários e dias de pico
    - Cálculo de probabilidade de atividade
    - Score de previsibilidade de rotina
    - Previsão de próximas atividades
    """
    
    DIAS_SEMANA = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analisador_base = AnalisadorTemporalBase()
        
        # Log disponibilidade de bibliotecas
        if NUMPY_AVAILABLE:
            self.logger.info("✅ NumPy disponível para análise avançada")
        else:
            self.logger.warning("⚠️ NumPy não disponível. Usando análise básica.")
        
        if SCIPY_AVAILABLE:
            self.logger.info("✅ SciPy disponível para estatísticas")
        
        if STATSMODELS_AVAILABLE:
            self.logger.info("✅ Statsmodels disponível para séries temporais")
    
    def extrair_atividades_de_posts(self, posts: List[Dict]) -> List[AtividadeTemporal]:
        """
        Converte lista de posts em atividades temporais.
        
        Args:
            posts: Lista de posts do Instagram
            
        Returns:
            Lista de AtividadeTemporal
        """
        atividades = []
        
        for post in posts:
            timestamp_str = post.get('timestamp') or post.get('taken_at')
            
            if timestamp_str:
                try:
                    # Tentar diferentes formatos de timestamp
                    if isinstance(timestamp_str, (int, float)):
                        timestamp = datetime.fromtimestamp(timestamp_str)
                    elif isinstance(timestamp_str, str):
                        # ISO format
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        continue
                    
                    atividades.append(AtividadeTemporal(
                        tipo='post',
                        timestamp=timestamp,
                        metadata={
                            'code': post.get('code'),
                            'likes': post.get('like_count', 0),
                            'comments': post.get('comment_count', 0)
                        }
                    ))
                except Exception as e:
                    self.logger.debug(f"Erro ao parsear timestamp: {e}")
        
        # Ordenar por timestamp
        atividades.sort(key=lambda x: x.timestamp)
        
        return atividades
    
    def analisar_padroes_horarios(self, atividades: List[AtividadeTemporal]) -> List[PadraoHorario]:
        """
        Analisa padrões de atividade por hora do dia.
        
        Args:
            atividades: Lista de atividades
            
        Returns:
            Lista de PadraoHorario para cada hora (0-23)
        """
        # Contagem por hora
        contagem_hora = defaultdict(int)
        for atividade in atividades:
            hora = atividade.timestamp.hour
            contagem_hora[hora] += 1
        
        total = sum(contagem_hora.values())
        padroes = []
        
        for hora in range(24):
            freq = contagem_hora[hora]
            prob = freq / total if total > 0 else 0.0
            
            padroes.append(PadraoHorario(
                hora=hora,
                frequencia=freq,
                probabilidade=prob
            ))
        
        return padroes
    
    def analisar_padroes_diarios(self, atividades: List[AtividadeTemporal]) -> List[PadraoDiario]:
        """
        Analisa padrões de atividade por dia da semana.
        
        Args:
            atividades: Lista de atividades
            
        Returns:
            Lista de PadraoDiario para cada dia
        """
        # Contagem por dia da semana
        contagem_dia = defaultdict(int)
        for atividade in atividades:
            dia = atividade.timestamp.weekday()
            contagem_dia[dia] += 1
        
        total = sum(contagem_dia.values())
        padroes = []
        
        for dia in range(7):
            freq = contagem_dia[dia]
            prob = freq / total if total > 0 else 0.0
            
            padroes.append(PadraoDiario(
                dia_semana=dia,
                nome_dia=self.DIAS_SEMANA[dia],
                frequencia=freq,
                probabilidade=prob,
                media_atividades=freq
            ))
        
        return padroes
    
    def calcular_intervalo_medio(self, atividades: List[AtividadeTemporal]) -> Optional[float]:
        """
        Calcula o intervalo médio entre atividades em horas.
        
        Args:
            atividades: Lista de atividades ordenadas
            
        Returns:
            Intervalo médio em horas ou None se insuficiente
        """
        if len(atividades) < 2:
            return None
        
        intervalos = []
        for i in range(1, len(atividades)):
            diff = atividades[i].timestamp - atividades[i-1].timestamp
            intervalos.append(diff.total_seconds() / 3600)  # Converter para horas
        
        if not intervalos:
            return None
        
        return self.analisador_base.calcular_media(intervalos)
    
    def detectar_tendencia(self, atividades: List[AtividadeTemporal]) -> str:
        """
        Detecta tendência de frequência de atividade.
        
        Returns:
            'crescente', 'decrescente' ou 'estavel'
        """
        if len(atividades) < 10:
            return 'estavel'
        
        # Dividir em duas metades e comparar frequência
        meio = len(atividades) // 2
        primeira_metade = atividades[:meio]
        segunda_metade = atividades[meio:]
        
        if not primeira_metade or not segunda_metade:
            return 'estavel'
        
        # Calcular duração de cada metade
        duracao_primeira = (primeira_metade[-1].timestamp - primeira_metade[0].timestamp).total_seconds()
        duracao_segunda = (segunda_metade[-1].timestamp - segunda_metade[0].timestamp).total_seconds()
        
        if duracao_primeira == 0 or duracao_segunda == 0:
            return 'estavel'
        
        # Frequência por dia
        freq_primeira = len(primeira_metade) / (duracao_primeira / 86400)
        freq_segunda = len(segunda_metade) / (duracao_segunda / 86400)
        
        # Comparar
        razao = freq_segunda / freq_primeira if freq_primeira > 0 else 1.0
        
        if razao > 1.2:
            return 'crescente'
        elif razao < 0.8:
            return 'decrescente'
        else:
            return 'estavel'
    
    def calcular_score_previsibilidade(
        self, 
        padroes_horarios: List[PadraoHorario],
        padroes_diarios: List[PadraoDiario],
        intervalo_medio: Optional[float]
    ) -> Tuple[float, str]:
        """
        Calcula score de previsibilidade de rotina (0-100).
        
        Fatores considerados:
        - Concentração de atividade em horários específicos
        - Concentração de atividade em dias específicos
        - Consistência do intervalo entre posts
        
        Returns:
            Tuple[score, nivel]
        """
        score = 0.0
        
        # 1. Concentração horária (max 40 pontos)
        # Quanto mais concentrado em poucos horários, mais previsível
        probs_hora = [p.probabilidade for p in padroes_horarios]
        if probs_hora:
            # Coeficiente de variação alta = mais concentrado = mais previsível
            cv_hora = self.analisador_base.calcular_coeficiente_variacao(probs_hora)
            score_hora = min(40, cv_hora * 20)
            score += score_hora
        
        # 2. Concentração diária (max 30 pontos)
        probs_dia = [p.probabilidade for p in padroes_diarios]
        if probs_dia:
            cv_dia = self.analisador_base.calcular_coeficiente_variacao(probs_dia)
            score_dia = min(30, cv_dia * 15)
            score += score_dia
        
        # 3. Consistência do intervalo (max 30 pontos)
        if intervalo_medio and intervalo_medio > 0:
            # Intervalos mais regulares = nota maior
            # Penalizar intervalos muito longos ou irregulares
            if intervalo_medio < 24:  # Posta pelo menos 1x por dia
                score += 30
            elif intervalo_medio < 48:  # Posta a cada 2 dias
                score += 25
            elif intervalo_medio < 72:  # Posta a cada 3 dias
                score += 20
            elif intervalo_medio < 168:  # Posta semanalmente
                score += 15
            else:
                score += 10
        
        # Determinar nível
        if score >= 80:
            nivel = 'muito_alto'
        elif score >= 60:
            nivel = 'alto'
        elif score >= 40:
            nivel = 'medio'
        else:
            nivel = 'baixo'
        
        return (min(100, max(0, score)), nivel)
    
    def identificar_picos(
        self,
        padroes_horarios: List[PadraoHorario],
        padroes_diarios: List[PadraoDiario]
    ) -> Tuple[List[int], List[str]]:
        """
        Identifica horários e dias de pico.
        
        Returns:
            Tuple[horarios_pico, dias_pico]
        """
        # Horários de pico (probabilidade > média + 1 desvio)
        probs_hora = [p.probabilidade for p in padroes_horarios]
        media_hora = self.analisador_base.calcular_media(probs_hora)
        desvio_hora = self.analisador_base.calcular_desvio_padrao(probs_hora)
        threshold_hora = media_hora + desvio_hora
        
        horarios_pico = [
            p.hora for p in padroes_horarios 
            if p.probabilidade >= threshold_hora and p.frequencia > 0
        ]
        
        # Dias de pico
        probs_dia = [p.probabilidade for p in padroes_diarios]
        media_dia = self.analisador_base.calcular_media(probs_dia)
        desvio_dia = self.analisador_base.calcular_desvio_padrao(probs_dia)
        threshold_dia = media_dia + desvio_dia
        
        dias_pico = [
            p.nome_dia for p in padroes_diarios
            if p.probabilidade >= threshold_dia and p.frequencia > 0
        ]
        
        return (horarios_pico, dias_pico)
    
    def prever_proximas_atividades(
        self,
        padroes_horarios: List[PadraoHorario],
        padroes_diarios: List[PadraoDiario],
        intervalo_medio: Optional[float],
        ultima_atividade: Optional[datetime] = None,
        num_previsoes: int = 5
    ) -> List[PrevisaoAtividade]:
        """
        Gera previsões de próximas atividades.
        
        Args:
            padroes_horarios: Padrões por hora
            padroes_diarios: Padrões por dia
            intervalo_medio: Intervalo médio em horas
            ultima_atividade: Timestamp da última atividade
            num_previsoes: Número de previsões a gerar
            
        Returns:
            Lista de PrevisaoAtividade
        """
        previsoes = []
        
        if not intervalo_medio:
            intervalo_medio = 24  # Default: 1 dia
        
        base_time = ultima_atividade or datetime.now()
        
        for i in range(num_previsoes):
            # Próximo horário provável
            prox_hora = base_time + timedelta(hours=intervalo_medio * (i + 1))
            
            # Calcular probabilidade baseada em padrões
            hora = prox_hora.hour
            dia = prox_hora.weekday()
            
            prob_hora = padroes_horarios[hora].probabilidade if hora < len(padroes_horarios) else 0.1
            prob_dia = padroes_diarios[dia].probabilidade if dia < len(padroes_diarios) else 0.1
            
            # Probabilidade combinada (média ponderada)
            prob_combinada = (prob_hora * 0.6 + prob_dia * 0.4)
            
            # Confiança diminui com o tempo
            confianca = max(0.1, 1.0 - (i * 0.15))
            
            previsoes.append(PrevisaoAtividade(
                data_hora=prox_hora,
                probabilidade=prob_combinada,
                confianca=confianca,
                tipo_previsto='post'
            ))
        
        return previsoes
    
    def detectar_sazonalidade(self, atividades: List[AtividadeTemporal]) -> bool:
        """
        Detecta se há sazonalidade nos dados.
        
        Simplificado: verifica se há padrão repetitivo semanal
        """
        if len(atividades) < 14:  # Mínimo 2 semanas
            return False
        
        # Contar atividades por dia da semana
        contagem = defaultdict(int)
        for a in atividades:
            contagem[a.timestamp.weekday()] += 1
        
        # Se a distribuição não for uniforme, há sazonalidade
        valores = list(contagem.values())
        cv = self.analisador_base.calcular_coeficiente_variacao(valores)
        
        return cv > 0.3  # CV > 30% indica padrão não uniforme
    
    def analisar(self, posts: List[Dict], username: str = "") -> AnalisePrevisibilidade:
        """
        Realiza análise completa de previsibilidade.
        
        Args:
            posts: Lista de posts do Instagram
            username: Nome do usuário
            
        Returns:
            AnalisePrevisibilidade com resultados completos
        """
        # Extrair atividades
        atividades = self.extrair_atividades_de_posts(posts)
        
        if not atividades:
            return AnalisePrevisibilidade(
                username=username,
                score_previsibilidade=0,
                nivel_previsibilidade='indeterminado',
                detalhes={'erro': 'Nenhuma atividade encontrada'}
            )
        
        # Analisar padrões
        padroes_horarios = self.analisar_padroes_horarios(atividades)
        padroes_diarios = self.analisar_padroes_diarios(atividades)
        
        # Calcular intervalo médio
        intervalo_medio = self.calcular_intervalo_medio(atividades)
        
        # Detectar tendência
        tendencia = self.detectar_tendencia(atividades)
        
        # Detectar sazonalidade
        sazonalidade = self.detectar_sazonalidade(atividades)
        
        # Calcular score
        score, nivel = self.calcular_score_previsibilidade(
            padroes_horarios, padroes_diarios, intervalo_medio
        )
        
        # Identificar picos
        horarios_pico, dias_pico = self.identificar_picos(padroes_horarios, padroes_diarios)
        
        # Gerar previsões
        ultima_atividade = atividades[-1].timestamp if atividades else None
        previsoes = self.prever_proximas_atividades(
            padroes_horarios, padroes_diarios, intervalo_medio, ultima_atividade
        )
        
        return AnalisePrevisibilidade(
            username=username,
            score_previsibilidade=score,
            nivel_previsibilidade=nivel,
            padroes_horarios=padroes_horarios,
            padroes_diarios=padroes_diarios,
            horarios_pico=horarios_pico,
            dias_pico=dias_pico,
            intervalo_medio_posts=intervalo_medio,
            proximas_previsoes=previsoes,
            tendencia=tendencia,
            sazonalidade_detectada=sazonalidade,
            detalhes={
                'total_atividades': len(atividades),
                'periodo_analise': {
                    'inicio': atividades[0].timestamp.isoformat() if atividades else None,
                    'fim': atividades[-1].timestamp.isoformat() if atividades else None
                },
                'numpy_disponivel': NUMPY_AVAILABLE,
                'scipy_disponivel': SCIPY_AVAILABLE,
                'statsmodels_disponivel': STATSMODELS_AVAILABLE
            }
        )


# =============================================================================
# INSTÂNCIA GLOBAL (SINGLETON)
# =============================================================================

_engine_instance: Optional[PredictiveEngine] = None


def get_predictive_engine() -> PredictiveEngine:
    """Retorna instância singleton do motor preditivo"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = PredictiveEngine()
    return _engine_instance


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    engine = get_predictive_engine()
    
    # Dados de teste simulando posts
    posts_teste = []
    base_time = datetime.now() - timedelta(days=30)
    
    # Simular padrão: posts às 9h e 18h, mais frequente em dias de semana
    for dia in range(30):
        data_base = base_time + timedelta(days=dia)
        
        # Post da manhã (9h-11h)
        if dia % 2 == 0:  # Dias alternados
            hora = 9 + (dia % 3)
            posts_teste.append({
                'timestamp': (data_base.replace(hour=hora, minute=0)).isoformat(),
                'code': f'post_{dia}_manha',
                'like_count': 100 + dia * 10,
                'comment_count': 10 + dia
            })
        
        # Post da tarde (17h-19h)
        if data_base.weekday() < 5:  # Dias úteis
            hora = 17 + (dia % 3)
            posts_teste.append({
                'timestamp': (data_base.replace(hour=hora, minute=30)).isoformat(),
                'code': f'post_{dia}_tarde',
                'like_count': 150 + dia * 5,
                'comment_count': 15 + dia
            })
    
    print("\n" + "="*60)
    print("TESTE DO MOTOR PREDITIVO")
    print("="*60 + "\n")
    
    resultado = engine.analisar(posts_teste, "usuario_teste")
    
    print(f"Username: {resultado.username}")
    print(f"Score de Previsibilidade: {resultado.score_previsibilidade:.1f}/100")
    print(f"Nível: {resultado.nivel_previsibilidade}")
    print(f"Tendência: {resultado.tendencia}")
    print(f"Sazonalidade: {'Sim' if resultado.sazonalidade_detectada else 'Não'}")
    print(f"Intervalo Médio: {resultado.intervalo_medio_posts:.1f}h")
    print(f"Horários de Pico: {resultado.horarios_pico}")
    print(f"Dias de Pico: {resultado.dias_pico}")
    print(f"\nPróximas Previsões:")
    for p in resultado.proximas_previsoes[:3]:
        print(f"  - {p.data_hora.strftime('%d/%m %H:%M')} (prob: {p.probabilidade:.2f}, conf: {p.confianca:.2f})")
    
    print(f"\nPadrões por Hora:")
    for p in resultado.padroes_horarios:
        if p.frequencia > 0:
            print(f"  {p.hora:02d}h: {p.frequencia} posts ({p.probabilidade*100:.1f}%)")
    
    print(f"\nPadrões por Dia:")
    for p in resultado.padroes_diarios:
        print(f"  {p.nome_dia}: {p.frequencia} posts ({p.probabilidade*100:.1f}%)")
