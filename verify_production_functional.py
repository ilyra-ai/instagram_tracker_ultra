import sys
import os
import asyncio
import logging
import json
from datetime import datetime

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ProdVerify")

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

async def verify_core_functionality():
    logger.info("🔬 [CORE] Verificando funcionalidades principais...")
    results = {}
    
    # 1. Verificar Endpoints (via import da API)
    try:
        from api.flask_api_fixed import app
        logger.info("✅ API Flask importada com sucesso")
        results['api_import'] = True
    except ImportError as e:
        logger.error(f"❌ Falha ao importar API: {e}")
        results['api_import'] = False

    # 2. Verificar Cache Manager
    try:
        from core.cache_manager import get_cache_manager
        cache = get_cache_manager()
        cache.set("test_prod_check", "valid", ttl=10)
        val = cache.get("test_prod_check")
        if val == "valid":
            logger.info("✅ Cache L1/L2 operando corretamente")
            results['cache'] = True
        else:
            logger.error("❌ Falha no Cache L1/L2")
            results['cache'] = False
    except Exception as e:
        logger.error(f"❌ Erro no Cache: {e}")
        results['cache'] = False

    # 3. Verificar Task Queue
    try:
        from core.task_queue import get_task_queue, TaskPriority
        queue = get_task_queue()
        await queue.start()  # Iniciar workers
        
        task_id = queue.enqueue("test_task", {"data": "check"}, TaskPriority.LOW) # Usar handler de teste
        
        # Aguardar processamento (max 5s)
        success = False
        for _ in range(10):
            status = queue.get_task_status(task_id)
            if status and status['status'] == 'completed':
                success = True
                break
            await asyncio.sleep(0.5)
            
        await queue.stop() # Parar workers
        
        if success:
            logger.info("✅ Task Queue processando tarefas")
            results['task_queue'] = True
        else:
            logger.error("❌ Task Queue: Tarefa não concluída a tempo")
            results['task_queue'] = False
            
    except Exception as e:
        logger.error(f"❌ Erro na Task Queue: {e}")
        results['task_queue'] = False

    return results

async def verify_ai_modules():
    logger.info("🧠 [AI] Verificando módulos de Inteligência...")
    results = {}

    # 1. Análise de Sentimento
    try:
        from analytics.sentiment_analyzer import get_sentiment_analyzer
        analyzer = get_sentiment_analyzer()
        score = analyzer.analyze("Este produto é incrível e maravilhoso!")
        # O resultado é um objeto SentimentResult, acessamos a polaridade
        if score.polaridade > 0.5:
            logger.info(f"✅ Análise de Sentimento PT-BR funcional (Score: {score.polaridade})")
            results['sentiment'] = True
        else:
            logger.warning(f"⚠️ Análise de Sentimento com score baixo: {score.polaridade}")
            results['sentiment'] = False
    except Exception as e:
        logger.error(f"❌ Erro no Sentiment Analyzer: {e}")
        results['sentiment'] = False

    # 2. YOLOv8 (Visão Computacional)
    try:
        # Apenas verificar importação para não carregar modelo pesado agora se não tiver GPU
        import ultralytics
        logger.info("✅ YOLOv8 (ultralytics) importável")
        results['vision'] = True
    except ImportError:
        logger.error("❌ ultralytics não instalado")
        results['vision'] = False
    except Exception as e:
        logger.error(f"❌ Erro ao verificar YOLO: {e}")
        results['vision'] = False

    return results

async def verify_security_stealth():
    logger.info("🛡️ [SECURITY] Verificando segurança e stealth...")
    results = {}

    # 1. Verificar .env
    if os.path.exists(".env"):
        logger.info("✅ Arquivo .env presente")
        results['env_file'] = True
    else:
        logger.warning("⚠️ Arquivo .env ausente (Credenciais hardcoded?)")
        results['env_file'] = False

    # 2. Verificar Nodriver (Anti-detecção)
    try:
        import nodriver
        logger.info("✅ Nodriver instalado (Anti-detecção base)")
        results['nodriver'] = True
    except ImportError:
        logger.error("❌ Nodriver ausente")
        results['nodriver'] = False

    return results

async def main():
    logger.info("=== INICIANDO VERIFICAÇÃO FUNCIONAL DE PRODUÇÃO ===")
    
    core_res = await verify_core_functionality()
    ai_res = await verify_ai_modules()
    sec_res = await verify_security_stealth()
    
    all_results = {**core_res, **ai_res, **sec_res}
    
    logger.info("\n=== RELATÓRIO FINAL ===")
    success_count = sum(1 for v in all_results.values() if v)
    total_count = len(all_results)
    
    for k, v in all_results.items():
        logger.info(f"{k.ljust(20)}: {'✅ PASSOU' if v else '❌ FALHOU'}")
        
    logger.info(f"\nTaxa de Sucesso: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        logger.info("🚀 SISTEMA PRONTO PARA FASE 7")
        sys.exit(0)
    else:
        logger.error("⚠️ PENDÊNCIAS ENCONTRADAS")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
