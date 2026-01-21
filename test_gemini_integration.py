import sys
import os
import logging
import json

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GeminiTest")

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from ai.gemini_client import get_gemini_client

def test_gemini():
    logger.info("🚀 Iniciando teste de integração com Google Gemini...")
    
    client = get_gemini_client()
    
    if not client.is_configured:
        logger.error("❌ Cliente não configurado. Verifique a API Key no .env")
        return

    # 0. Listar Modelos Disponíveis
    logger.info("\n📋 0. Listando Modelos Disponíveis...")
    models = client.list_available_models()
    for m in models:
        logger.info(f"   - {m['displayName']} ({m['name']})")
    
    logger.info(f"\n🎯 Modelo em uso: {client.model_name}")

    # 1. Teste de Geração Simples
    logger.info("\n🧪 1. Testando Geração de Conteúdo...")
    try:
        response = client.generate_content("Responda em 1 frase: O que é OSINT?")
        if response:
            logger.info(f"✅ Resposta recebida: {response}")
        else:
            logger.error("❌ Falha na geração (resposta vazia)")
    except Exception as e:
        logger.error(f"❌ Erro no teste 1: {e}")

    # 2. Teste de Análise de Bio
    logger.info("\n🧪 2. Testando Análise de Bio...")
    bio_exemplo = "Empreendedor digital 🚀 | Ajudo você a escalar seu negócio | CEO @empresa | 📍 São Paulo"
    try:
        analysis = client.analyze_profile_bio(bio_exemplo, "usuario_teste")
        logger.info(f"✅ Análise recebida:\n{json.dumps(analysis, indent=2, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"❌ Erro no teste 2: {e}")

    # 3. Teste de Análise de Sentimento
    logger.info("\n🧪 3. Testando Análise de Sentimento de Comentários...")
    comentarios = [
        "Adorei o produto! Muito bom!",
        "O atendimento foi péssimo, demorou muito.",
        "Preço justo, mas a qualidade poderia ser melhor.",
        "Recomendo a todos, excelente experiência."
    ]
    try:
        sentiment = client.analyze_comments_sentiment(comentarios)
        logger.info(f"✅ Sentimento recebido:\n{json.dumps(sentiment, indent=2, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"❌ Erro no teste 3: {e}")

if __name__ == "__main__":
    test_gemini()
