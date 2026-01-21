"""
Gemini Client - Integração com Google Generative AI
Autor: Instagram Intelligence System 2026
Versão: 1.0.0

Este módulo gerencia a comunicação com a API do Google Gemini, fornecendo
capacidades de análise de texto, sentimento e geração de conteúdo.
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any, Union
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de Logs
logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Cliente robusto para a API do Google Gemini.
    Implementa retries, tratamento de erros e métodos especializados.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Inicializa o cliente Gemini.
        
        Args:
            api_key: Chave de API do Google Gemini. Se None, tenta ler de GOOGLE_GEMINI_API_KEY no env.
            model_name: Nome do modelo específico a ser usado (opcional).
        """
        self.api_key = api_key or os.getenv("GOOGLE_GEMINI_API_KEY")
        
        if not self.api_key:
            logger.warning("⚠️ GOOGLE_GEMINI_API_KEY não encontrada. Funcionalidades de IA generativa estarão indisponíveis.")
            self.is_configured = False
            return

        try:
            genai.configure(api_key=self.api_key)
            
            # Seleção automática de modelo se não especificado
            if not model_name:
                self.model_name = self._select_best_model()
            else:
                self.model_name = model_name
                
            self.model = genai.GenerativeModel(self.model_name)
            self.is_configured = True
            logger.info(f"✅ Gemini Client inicializado com sucesso (Modelo: {self.model_name})")
        except Exception as e:
            logger.error(f"❌ Erro ao configurar Gemini Client: {e}")
            self.is_configured = False

    def _select_best_model(self) -> str:
        """
        Seleciona o melhor modelo disponível na API Key fornecida.
        Prioriza modelos Flash (rápidos/baratos) e Pro (robustos).
        """
        try:
            logger.info("🔍 Buscando modelos disponíveis na API...")
            available_models = [
                m for m in genai.list_models() 
                if 'generateContent' in m.supported_generation_methods
            ]
            
            model_map = {m.name.replace('models/', ''): m for m in available_models}
            logger.debug(f"Modelos encontrados: {list(model_map.keys())}")
            
            # Ordem de prioridade baseada na sugestão do usuário (Estabilidade + Performance)
            priorities = [
                'gemini-1.5-flash', # Rápido, barato, contexto alto (1M)
                'gemini-1.5-pro',   # Mais robusto, contexto alto (2M)
                'gemini-2.0-flash', # Versão mais nova (se disponível)
                'gemini-pro',       # Legacy
            ]
            
            for p in priorities:
                if p in model_map:
                    logger.info(f"🎯 Modelo selecionado automaticamente: {p}")
                    return p
            
            # Fallback: pegar o primeiro que não seja experimental se possível
            stable_models = [name for name in model_map.keys() if 'exp' not in name]
            if stable_models:
                return stable_models[0]
                
            if model_map:
                return list(model_map.keys())[0]
                
            logger.warning("⚠️ Nenhum modelo de geração de conteúdo encontrado. Tentando 'gemini-1.5-flash' como fallback cego.")
            return 'gemini-1.5-flash'
            
        except Exception as e:
            logger.warning(f"⚠️ Falha ao listar modelos ({e}). Usando 'gemini-1.5-flash' como default.")
            return 'gemini-1.5-flash'

    def list_available_models(self) -> List[Dict[str, Any]]:
        """Lista modelos disponíveis formatados para o frontend."""
        if not self.is_configured:
            return []
        try:
            models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models.append({
                        'name': m.name.replace('models/', ''),
                        'displayName': m.display_name,
                        'description': m.description,
                        'inputTokenLimit': m.input_token_limit,
                        'outputTokenLimit': m.output_token_limit
                    })
            return models
        except Exception as e:
            logger.error(f"❌ Erro ao listar modelos: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def generate_content(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """
        Gera conteúdo genérico a partir de um prompt.
        
        Args:
            prompt: Texto de entrada.
            temperature: Criatividade da resposta (0.0 a 1.0).
            
        Returns:
            Texto gerado ou None em caso de falha.
        """
        if not self.is_configured:
            logger.error("❌ Tentativa de uso do Gemini sem configuração válida.")
            return None

        try:
            logger.debug(f"🤖 Enviando prompt para Gemini (len={len(prompt)})")
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=2048,
            )
            
            # Configurações de segurança para evitar bloqueios desnecessários em análises legítimas
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            if response.text:
                logger.debug("✅ Resposta recebida do Gemini")
                return response.text
            else:
                logger.warning("⚠️ Gemini retornou resposta vazia ou bloqueada.")
                return None

        except Exception as e:
            logger.error(f"❌ Erro na geração de conteúdo Gemini: {e}")
            raise

    def analyze_profile_bio(self, bio_text: str, username: str) -> Dict[str, Any]:
        """
        Analisa a biografia de um perfil para extrair insights.
        
        Args:
            bio_text: Texto da biografia.
            username: Nome de usuário.
            
        Returns:
            Dicionário com insights (categoria, tom, interesses, etc).
        """
        if not bio_text:
            return {"error": "Bio vazia"}

        prompt = f"""
        Analise a seguinte biografia de perfil do Instagram (@{username}) e retorne um JSON estrito com as seguintes chaves:
        - category: Categoria provável do perfil (ex: Creator, Business, Personal, Fanpage).
        - tone: Tom da comunicação (ex: Profissional, Descontraído, Inspiracional).
        - interests: Lista de principais interesses/tópicos identificados.
        - contact_info: Se houver email ou telefone visível (True/False).
        - language: Idioma principal detectado (código ISO, ex: pt-BR).
        - summary: Um resumo de 1 frase sobre o perfil.

        Bio: "{bio_text}"
        
        Responda APENAS o JSON.
        """
        
        try:
            response_text = self.generate_content(prompt, temperature=0.2)
            if response_text:
                # Limpar markdown ```json ... ``` se houver
                cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
                return json.loads(cleaned_text)
            return {"error": "Falha na geração"}
        except json.JSONDecodeError:
            logger.error("❌ Erro ao decodificar JSON do Gemini")
            return {"error": "Erro de parse JSON", "raw_response": response_text}
        except Exception as e:
            logger.error(f"❌ Erro na análise de bio: {e}")
            return {"error": str(e)}

    def analyze_comments_sentiment(self, comments: List[str]) -> Dict[str, Any]:
        """
        Analisa uma lista de comentários para determinar o sentimento geral e destaques.
        
        Args:
            comments: Lista de textos de comentários.
            
        Returns:
            Dicionário com análise de sentimento agregada.
        """
        if not comments:
            return {"error": "Lista de comentários vazia"}
            
        # Limitar para evitar estouro de tokens (pegar os primeiros 50 ou amostra)
        sample_comments = comments[:50]
        comments_block = "\n".join([f"- {c}" for c in sample_comments])
        
        prompt = f"""
        Analise a seguinte lista de comentários do Instagram e retorne um JSON estrito com:
        - sentiment_score: De -1.0 (muito negativo) a 1.0 (muito positivo).
        - dominant_emotion: Emoção predominante (ex: Alegria, Raiva, Curiosidade, Inveja, Admiração).
        - main_topics: Lista dos 3 principais assuntos discutidos.
        - spam_detected: Se há indícios fortes de spam/bots (True/False).
        - summary: Resumo executivo da percepção do público em 1 parágrafo curto.

        Comentários:
        {comments_block}
        
        Responda APENAS o JSON.
        """
        
        try:
            response_text = self.generate_content(prompt, temperature=0.3)
            if response_text:
                cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
                return json.loads(cleaned_text)
            return {"error": "Falha na geração"}
        except json.JSONDecodeError:
            logger.error("❌ Erro ao decodificar JSON de sentimento")
            return {"error": "Erro de parse JSON"}
        except Exception as e:
            logger.error(f"❌ Erro na análise de comentários: {e}")
            return {"error": str(e)}

# Instância Global Singleton
_gemini_client_instance: Optional[GeminiClient] = None

def get_gemini_client() -> GeminiClient:
    """Retorna a instância singleton do GeminiClient."""
    global _gemini_client_instance
    if _gemini_client_instance is None:
        _gemini_client_instance = GeminiClient()
    return _gemini_client_instance
