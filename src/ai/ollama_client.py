"""
Ollama Client - Integração com Ollama (LLM Local)
Autor: Instagram Intelligence System 2026
Versão: 1.0.0

Este módulo gerencia a comunicação com uma instância local do Ollama,
fornecendo capacidades de análise de texto e geração de conteúdo offline.
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de Logs
logger = logging.getLogger(__name__)


@dataclass
class OllamaModel:
    """Informações de um modelo Ollama."""
    name: str
    size: int
    modified_at: str
    parameter_size: str
    quantization_level: str
    family: str


class OllamaClient:
    """
    Cliente robusto para integração com Ollama (LLM Local).
    Permite geração de conteúdo e análise sem depender de APIs externas.
    """

    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(self, base_url: Optional[str] = None, model_name: Optional[str] = None):
        """
        Inicializa o cliente Ollama.
        
        Args:
            base_url: URL base do Ollama. Se None, tenta ler de OLLAMA_API_BASE_URL no env ou usa localhost:11434.
            model_name: Nome do modelo específico a ser usado (opcional).
        """
        self.base_url = base_url or os.getenv("OLLAMA_API_BASE_URL", self.DEFAULT_BASE_URL)
        self.base_url = self.base_url.rstrip("/")  # Remover trailing slash
        
        self.is_configured = False
        self.available_models: List[OllamaModel] = []
        self.model_name: Optional[str] = None

        # Validar URL para evitar SSRF
        if not self._is_valid_url(self.base_url):
            logger.error(f"❌ URL do Ollama inválida ou insegura: {self.base_url}. Apenas localhost é permitido.")
            return

        # Verificar se Ollama está disponível
        if self._check_connection():
            self.is_configured = True
            self.available_models = self._fetch_models()
            
            if model_name:
                self.model_name = model_name
            elif self.available_models:
                self.model_name = self._select_best_model()
            
            if self.model_name:
                logger.info(f"✅ Ollama Client inicializado com sucesso (Modelo: {self.model_name})")
            else:
                logger.warning("⚠️ Ollama conectado, mas nenhum modelo disponível.")
                self.is_configured = False
        else:
            logger.warning(f"⚠️ Ollama não disponível em {self.base_url}. Funcionalidades de LLM local indisponíveis.")

    def _is_valid_url(self, url: str) -> bool:
        """
        Valida se a URL é segura (apenas localhost/IP local).
        Isso previne ataques de SSRF (Server-Side Request Forgery).
        """
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            # Permitir apenas localhost por padrão para segurança máxima
            allowed_hosts = ("localhost", "127.0.0.1", "::1")
            return hostname.lower() in allowed_hosts
        except Exception:
            return False

    def _check_connection(self) -> bool:
        """Verifica se o Ollama está acessível."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def _fetch_models(self) -> List[OllamaModel]:
        """Busca a lista de modelos disponíveis no Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code != 200:
                return []
            
            data = response.json()
            models = []
            
            for m in data.get("models", []):
                details = m.get("details", {})
                models.append(OllamaModel(
                    name=m.get("name", ""),
                    size=m.get("size", 0),
                    modified_at=m.get("modified_at", ""),
                    parameter_size=details.get("parameter_size", "unknown"),
                    quantization_level=details.get("quantization_level", "unknown"),
                    family=details.get("family", "unknown")
                ))
            
            logger.info(f"📋 Modelos Ollama encontrados: {[m.name for m in models]}")
            return models
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar modelos Ollama: {e}")
            return []

    def _select_best_model(self) -> Optional[str]:
        """
        Seleciona o melhor modelo disponível.
        Prioriza modelos maiores e mais recentes.
        """
        if not self.available_models:
            return None
        
        # Prioridades de modelos conhecidos
        priorities = [
            "llama3.2",
            "llama3.1",
            "llama3",
            "mistral",
            "mixtral",
            "codellama",
            "phi",
        ]
        
        model_names = [m.name.split(":")[0] for m in self.available_models]
        
        for p in priorities:
            for m in self.available_models:
                if p in m.name.lower():
                    logger.info(f"🎯 Modelo Ollama selecionado: {m.name}")
                    return m.name
        
        # Fallback: pegar o primeiro
        return self.available_models[0].name

    def list_available_models(self) -> List[Dict[str, Any]]:
        """Lista modelos disponíveis formatados para o frontend."""
        return [
            {
                "name": m.name,
                "displayName": f"{m.name} ({m.parameter_size})",
                "family": m.family,
                "size": m.size,
                "quantization": m.quantization_level
            }
            for m in self.available_models
        ]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True
    )
    def generate_content(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """
        Gera conteúdo a partir de um prompt usando Ollama.
        
        Args:
            prompt: Texto de entrada.
            temperature: Criatividade da resposta (0.0 a 1.0).
            
        Returns:
            Texto gerado ou None em caso de falha.
        """
        if not self.is_configured or not self.model_name:
            logger.error("❌ Tentativa de uso do Ollama sem configuração válida.")
            return None

        try:
            logger.debug(f"🤖 Enviando prompt para Ollama/{self.model_name} (len={len(prompt)})")
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_ctx": 4096
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # LLMs locais podem ser lentos
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Ollama retornou status {response.status_code}")
                return None
            
            data = response.json()
            result = data.get("response", "")
            
            if result:
                logger.debug("✅ Resposta recebida do Ollama")
                return result
            else:
                logger.warning("⚠️ Ollama retornou resposta vazia.")
                return None

        except Exception as e:
            logger.error(f"❌ Erro na geração de conteúdo Ollama: {e}")
            raise

    def analyze_profile_bio(self, bio_text: str, username: str) -> Dict[str, Any]:
        """
        Analisa a biografia de um perfil para extrair insights (via Ollama).
        """
        if not bio_text:
            return {"error": "Bio vazia"}

        prompt = f"""Analise a seguinte biografia de perfil do Instagram (@{username}) e retorne um JSON com:
- category: Categoria do perfil (Creator, Business, Personal, Fanpage)
- tone: Tom da comunicação (Profissional, Descontraído, Inspiracional)
- interests: Lista de interesses identificados
- contact_info: Se há email ou telefone (true/false)
- language: Idioma principal (código ISO, ex: pt-BR)
- summary: Resumo de 1 frase

Bio: "{bio_text}"

Responda APENAS o JSON válido, sem explicações."""
        
        try:
            response_text = self.generate_content(prompt, temperature=0.2)
            if response_text:
                cleaned_text = response_text.strip()
                # Tentar extrair JSON do texto
                if "```json" in cleaned_text:
                    cleaned_text = cleaned_text.split("```json")[1].split("```")[0]
                elif "```" in cleaned_text:
                    cleaned_text = cleaned_text.split("```")[1].split("```")[0]
                return json.loads(cleaned_text.strip())
            return {"error": "Falha na geração"}
        except json.JSONDecodeError:
            logger.error("❌ Erro ao decodificar JSON do Ollama")
            return {"error": "Erro de parse JSON", "raw_response": response_text if response_text else ""}
        except Exception as e:
            logger.error(f"❌ Erro na análise de bio via Ollama: {e}")
            return {"error": str(e)}

    def analyze_comments_sentiment(self, comments: List[str]) -> Dict[str, Any]:
        """
        Analisa uma lista de comentários para determinar o sentimento (via Ollama).
        """
        if not comments:
            return {"error": "Lista de comentários vazia"}
            
        sample_comments = comments[:30]  # Limitar para modelos menores
        comments_block = "\n".join([f"- {c}" for c in sample_comments])
        
        prompt = f"""Analise estes comentários do Instagram e retorne um JSON com:
- sentiment_score: De -1.0 (negativo) a 1.0 (positivo)
- dominant_emotion: Emoção predominante
- main_topics: Lista dos 3 principais assuntos
- spam_detected: Se há spam/bots (true/false)
- summary: Resumo curto da percepção do público

Comentários:
{comments_block}

Responda APENAS o JSON válido."""
        
        try:
            response_text = self.generate_content(prompt, temperature=0.3)
            if response_text:
                cleaned_text = response_text.strip()
                if "```json" in cleaned_text:
                    cleaned_text = cleaned_text.split("```json")[1].split("```")[0]
                elif "```" in cleaned_text:
                    cleaned_text = cleaned_text.split("```")[1].split("```")[0]
                return json.loads(cleaned_text.strip())
            return {"error": "Falha na geração"}
        except json.JSONDecodeError:
            logger.error("❌ Erro ao decodificar JSON de sentimento via Ollama")
            return {"error": "Erro de parse JSON"}
        except Exception as e:
            logger.error(f"❌ Erro na análise de comentários via Ollama: {e}")
            return {"error": str(e)}


# Instância Global Singleton
_ollama_client_instance: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Retorna a instância singleton do OllamaClient."""
    global _ollama_client_instance
    if _ollama_client_instance is None:
        _ollama_client_instance = OllamaClient()
    return _ollama_client_instance
