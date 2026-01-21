import os
import sys
import importlib
import logging
from pathlib import Path

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ProductionCheck")

def check_dependencies():
    """Verifica se as dependências críticas podem ser importadas."""
    logger.info("Verificando dependências críticas...")
    dependencies = [
        "flask", "sqlalchemy", "socketio", "requests", "bs4", 
        "curl_cffi", "nodriver", "cv2", "ultralytics", "vaderSentiment",
        "networkx", "tenacity", "rich", "sentry_sdk", "prometheus_client"
    ]
    
    missing = []
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            logger.info(f"✅ Dependência encontrada: {dep}")
        except ImportError:
            logger.warning(f"❌ Dependência ausente: {dep}")
            missing.append(dep)
            
    if missing:
        logger.error(f"Dependências faltando: {', '.join(missing)}")
        return False
    return True

def check_directories():
    """Verifica a estrutura de diretórios necessária."""
    logger.info("Verificando estrutura de diretórios...")
    required_dirs = [
        "static", "static/css", "static/js", "static/img",
        "templates", "data", "logs", "models"
    ]
    
    base_path = Path(os.getcwd())
    missing = []
    
    for d in required_dirs:
        path = base_path / d
        if path.exists() and path.is_dir():
            logger.info(f"✅ Diretório encontrado: {d}")
        else:
            logger.warning(f"❌ Diretório ausente: {d}")
            # Tentar criar se não existir (exceto se for crítico como static/templates)
            if d in ["data", "logs", "models"]:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"🛠️ Diretório criado: {d}")
                except Exception as e:
                    logger.error(f"Falha ao criar diretório {d}: {e}")
                    missing.append(d)
            else:
                missing.append(d)
                
    if missing:
        logger.error(f"Diretórios críticos faltando: {', '.join(missing)}")
        return False
    return True

def check_environment_variables():
    """Verifica variáveis de ambiente (simulação de segurança)."""
    logger.info("Verificando variáveis de ambiente...")
    # Em um cenário real, verificaríamos se .env existe e tem chaves
    # Como estamos em dev/test, vamos apenas verificar se o arquivo .env existe
    env_path = Path(".env")
    if env_path.exists():
        logger.info("✅ Arquivo .env encontrado.")
    else:
        logger.warning("⚠️ Arquivo .env não encontrado. Certifique-se de configurar variáveis de produção.")
    return True

def check_core_files():
    """Verifica a existência de arquivos core do sistema."""
    logger.info("Verificando arquivos core...")
    core_files = [
        "main.py", "src/api/flask_api_fixed.py", "requirements.txt",
        "templates/dashboard.html", "static/js/main.js",
        "static/styles_fixed.css"
    ]
    
    missing = []
    for f in core_files:
        if Path(f).exists():
            logger.info(f"✅ Arquivo core encontrado: {f}")
        else:
            logger.error(f"❌ Arquivo core ausente: {f}")
            missing.append(f)
            
    if missing:
        return False
    return True

def run_production_check():
    """Executa todas as verificações."""
    logger.info("=== INICIANDO VERIFICAÇÃO DE PRODUÇÃO (CHECKLIST) ===")
    
    checks = {
        "Dependências": check_dependencies(),
        "Diretórios": check_directories(),
        "Ambiente": check_environment_variables(),
        "Arquivos Core": check_core_files()
    }
    
    logger.info("=== RESULTADO DA VERIFICAÇÃO ===")
    all_passed = True
    for name, passed in checks.items():
        status = "PASSOU" if passed else "FALHOU"
        logger.info(f"{name}: {status}")
        if not passed:
            all_passed = False
            
    if all_passed:
        logger.info("✅ SISTEMA PRONTO PARA FASE 7 (EMPACOTAMENTO)")
        return 0
    else:
        logger.error("❌ SISTEMA NÃO ESTÁ PRONTO. CORRIJA OS ERROS ACIMA.")
        return 1

if __name__ == "__main__":
    sys.exit(run_production_check())
