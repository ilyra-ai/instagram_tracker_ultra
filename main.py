#!/usr/bin/env python3
"""
Instagram Intelligence System 2026 (God Mode Ultimate)
Ponto de entrada principal

Uso:
    python main.py              # Inicia API em modo desenvolvimento
    python main.py --port 8080  # Inicia em porta específica
    python main.py --test       # Executa testes de integração
"""

import sys
import os
import argparse
import logging
import importlib

# Adicionar src ao path para imports funcionarem
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("Main")


def run_api(host: str = "0.0.0.0", port: int = 5000, debug: bool = True):
    """Inicia a API Flask"""
    logger.info(f"🚀 Iniciando Instagram Intelligence System 2026...")
    logger.info(f"📡 Servidor: http://{host}:{port}")
    
    try:
        from api.flask_api_fixed import app, socketio
        socketio.run(app, host=host, port=port, debug=debug)
    except ImportError as e:
        logger.error(f"❌ Erro de import: {e}")
        logger.info("💡 Certifique-se de instalar as dependências: pip install -r requirements.txt")
        sys.exit(1)


def run_tests(base_url: str = "http://localhost:5000"):
    """Executa testes de integração"""
    logger.info("🧪 Executando testes de integração...")
    
    import asyncio
    try:
        from tests.integration_tests import run_full_test_suite
        asyncio.run(run_full_test_suite(base_url))
    except ImportError as e:
        logger.error(f"❌ Erro de import: {e}")
        sys.exit(1)


def show_status():
    """Mostra status dos módulos"""
    print("\n" + "=" * 60)
    print("   Instagram Intelligence System 2026")
    print("   God Mode Ultimate")
    print("=" * 60)
    
    modules = {
        'Core': ['instagram_scraper_2025', 'browser_manager', 'cache_manager', 'task_queue', 'activity_tracker_2025'],
        'Analytics': ['sentiment_analyzer', 'predictive_engine', 'advanced_analytics'],
        'Intelligence': ['ai_vision', 'graph_engine'],
        'OSINT': ['osint_toolkit', 'graphql_monitor'],
        'Stealth': ['anti_detection', 'stealth_ops'],
        'API': ['flask_api_fixed', 'init_db'],
        'Tests': ['integration_tests']
    }
    
    for category, mods in modules.items():
        print(f"\n📦 {category}:")
        for mod in mods:
            try:
                # Tenta importar usando importlib para melhor resolução de nomes
                module_path = f"{category.lower()}.{mod}"
                importlib.import_module(module_path)
                print(f"   ✅ {mod}")
            except Exception as e:
                print(f"   ❌ {mod}: {str(e)[:40]}")
    
    print("\n" + "=" * 60)


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Instagram Intelligence System 2026 (God Mode Ultimate)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host para o servidor (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Porta para o servidor (default: 5000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativar modo debug"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Executar testes de integração"
    )
    parser.add_argument(
        "--test-url",
        default="http://localhost:5000",
        help="URL base para testes (default: http://localhost:5000)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Mostrar status dos módulos"
    )
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    elif args.test:
        run_tests(args.test_url)
    else:
        run_api(args.host, args.port, args.debug)


if __name__ == "__main__":
    main()
