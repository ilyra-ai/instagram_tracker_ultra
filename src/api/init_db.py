"""
Inicialização do banco de dados SQLite para Instagram Tracker
"""

import sqlite3
import os
import logging

def init_database(db_name='instagram_tracker.db'):
    """Inicializa o banco de dados SQLite com as tabelas necessárias"""
    try:
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        # Conectar ao banco
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Criar tabela de histórico de posts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                post_code TEXT NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, post_code)
            )
        ''')
        
        # Criar tabela de configurações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Criar tabela de logs de rastreamento
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracking_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Criar índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_post_history_username ON post_history(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_post_history_code ON post_history(post_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_logs_username ON tracking_logs(username)')
        
        # Salvar mudanças
        conn.commit()
        
        logger.info(f"✅ Banco de dados {db_name} inicializado com sucesso")
        
        # Verificar tabelas criadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Tabelas criadas: {[table[0] for table in tables]}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de dados: {e}")
        return False

if __name__ == "__main__":
    init_database()
