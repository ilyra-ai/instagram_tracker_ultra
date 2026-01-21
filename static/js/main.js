/**
 * main.js - Entry Point da Aplicação Frontend
 * 
 * Inicializa todos os módulos, configura dependências externas,
 * e prepara o ambiente para o dashboard.
 * 
 * @version 1.0.0
 */

// =============================================================================
// IMPORTS
// =============================================================================

import { getAPIService } from './core/APIService.js';
import { getStateManager } from './core/StateManager.js';
import { getNotificationService } from './core/NotificationService.js';
import { getDashboard } from './components/Dashboard.js';

// =============================================================================
// CONFIGURAÇÃO GLOBAL
// =============================================================================

const CONFIG = {
    API_BASE_URL: window.location.origin,
    API_TIMEOUT: 30000,
    CACHE_TIMEOUT: 5 * 60 * 1000, // 5 minutos
    MAX_RETRIES: 3,
    THEME: localStorage.getItem('theme') || 'light',
    DEBUG: window.location.hostname === 'localhost'
};

// =============================================================================
// INICIALIZAÇÃO
// =============================================================================

/**
 * Logger com prefixo
 */
const logger = {
    log: (...args) => CONFIG.DEBUG && console.log('[App]', ...args),
    warn: (...args) => console.warn('[App]', ...args),
    error: (...args) => console.error('[App]', ...args)
};

/**
 * Inicializa a aplicação
 */
async function initApp() {
    logger.log('🚀 Iniciando Instagram Intelligence System 2026...');

    try {
        // 1. Inicializar serviços core
        const api = getAPIService({
            baseURL: CONFIG.API_BASE_URL,
            timeout: CONFIG.API_TIMEOUT,
            retries: CONFIG.MAX_RETRIES,
            cacheTimeout: CONFIG.CACHE_TIMEOUT
        });

        const state = getStateManager();
        const notifications = getNotificationService();

        // 2. Aplicar tema salvo
        applyTheme(CONFIG.THEME);

        // 3. Verificar status da API
        logger.log('📡 Verificando conexão com API...');
        const status = await api.getStatus().catch(() => null);

        if (status) {
            state.set('system.status', 'online');
            state.set('system.version', status.version);
            logger.log('✅ API online:', status.version);
        } else {
            state.set('system.status', 'offline');
            logger.warn('⚠️ API offline ou inacessível');
        }

        // 4. Inicializar dashboard
        const dashboard = getDashboard(document.getElementById('app'));
        await dashboard.init();

        // 5. Configurar handlers globais
        setupGlobalHandlers(api, state, notifications);

        // 6. Verificar hash da URL para navegação direta
        handleURLHash(dashboard);

        // 7. Expor globalmente para debug
        if (CONFIG.DEBUG) {
            window.__app = { api, state, notifications, dashboard, CONFIG };
        }

        logger.log('✅ Aplicação inicializada com sucesso!');

    } catch (error) {
        logger.error('❌ Erro na inicialização:', error);
        showCriticalError(error);
    }
}

/**
 * Aplica tema (light/dark)
 * @param {string} theme - Nome do tema
 */
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    // Atualizar meta theme-color para mobile
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
        metaThemeColor.content = theme === 'dark' ? '#1a1a2e' : '#667eea';
    }

    // Atualizar ícone do tema
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        if (theme === 'dark') {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        } else {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
        }
    }
}

/**
 * Toggle de tema
 */
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);

    // Atualizar estado
    getStateManager().set('ui.theme', newTheme);
}

/**
 * Configura handlers globais
 * @param {APIService} api - Serviço de API
 * @param {StateManager} state - Gerenciador de estado
 * @param {NotificationService} notifications - Serviço de notificações
 */
function setupGlobalHandlers(api, state, notifications) {
    // Handler de erros não tratados
    window.addEventListener('unhandledrejection', (event) => {
        logger.error('Unhandled Promise Rejection:', event.reason);
        notifications.error(
            event.reason?.message || 'Ocorreu um erro inesperado',
            'Erro'
        );
    });

    // Handler de erros de script
    window.addEventListener('error', (event) => {
        logger.error('JavaScript Error:', event.error);
    });

    // Handler de navegação por hash
    window.addEventListener('hashchange', () => {
        handleURLHash(window.__app?.dashboard);
    });

    // Handler de visibilidade da página
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            // Revalidar status quando volta à aba
            api.getStatus().then(status => {
                state.set('system.status', 'online');
            }).catch(() => {
                state.set('system.status', 'offline');
            });
        }
    });

    // Handler de resize para responsividade
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            document.dispatchEvent(new CustomEvent('app:resize', {
                detail: {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            }));
        }, 250);
    });

    // Handler de teclas de atalho
    document.addEventListener('keydown', (e) => {
        // Ctrl+K para abrir busca
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="username"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }

        // Escape para fechar modais/sidebar mobile
        if (e.key === 'Escape') {
            const sidebar = document.querySelector('.sidebar.open');
            if (sidebar) {
                sidebar.classList.remove('open');
                document.querySelector('.sidebar-overlay')?.classList.remove('active');
            }
        }
    });

    // Handler de toggle tema (Ctrl+Shift+T)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
            e.preventDefault();
            toggleTheme();
        }
    });

    // Expor toggle de tema globalmente
    window.toggleTheme = toggleTheme;
}

/**
 * Trata navegação por hash da URL
 * @param {Dashboard} dashboard - Instância do dashboard
 */
function handleURLHash(dashboard) {
    if (!dashboard) return;

    const hash = window.location.hash.slice(1); // Remove o #

    if (hash) {
        // Verificar se é uma tab válida
        const validTabs = ['overview', 'activities', 'intelligence', 'network', 'osint', 'history'];

        if (validTabs.includes(hash)) {
            dashboard.switchTab(hash);
        } else if (hash.startsWith('user/')) {
            // Navegação para usuário específico: #user/username
            const username = hash.split('/')[1];
            if (username) {
                getStateManager().set('currentUser', username);
            }
        }
    }
}

/**
 * Mostra erro crítico na UI
 * @param {Error} error - Erro ocorrido
 */
function showCriticalError(error) {
    const container = document.getElementById('app') || document.body;

    container.innerHTML = `
        <div class="critical-error">
            <div class="critical-error__content">
                <i class="fas fa-exclamation-triangle"></i>
                <h1>Erro ao Carregar Aplicação</h1>
                <p>${error.message || 'Ocorreu um erro inesperado.'}</p>
                <button onclick="location.reload()" class="btn btn-primary">
                    <i class="fas fa-redo"></i> Tentar Novamente
                </button>
            </div>
        </div>
        <style>
            .critical-error {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
            }
            .critical-error__content {
                background: white;
                padding: 40px;
                border-radius: 20px;
                text-align: center;
                max-width: 400px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            .critical-error__content i {
                font-size: 4rem;
                color: #dc3545;
                margin-bottom: 20px;
            }
            .critical-error__content h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 1.5rem;
            }
            .critical-error__content p {
                color: #666;
                margin-bottom: 20px;
            }
        </style>
    `;
}

// =============================================================================
// UTILITÁRIOS GLOBAIS
// =============================================================================

/**
 * Formata número para exibição
 * @param {number} num - Número
 * @param {Object} options - Opções de formatação
 * @returns {string}
 */
window.formatNumber = function (num, options = {}) {
    if (num === null || num === undefined) return '-';

    const { compact = true, decimals = 1 } = options;

    if (compact) {
        if (num >= 1000000) return (num / 1000000).toFixed(decimals) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(decimals) + 'K';
    }

    return num.toLocaleString('pt-BR');
};

/**
 * Formata data para exibição
 * @param {string|Date} date - Data
 * @param {Object} options - Opções de formatação
 * @returns {string}
 */
window.formatDate = function (date, options = {}) {
    if (!date) return '-';

    const d = new Date(date);
    const { relative = false, full = false } = options;

    if (relative) {
        const now = new Date();
        const diff = now - d;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (seconds < 60) return 'agora';
        if (minutes < 60) return `${minutes}min atrás`;
        if (hours < 24) return `${hours}h atrás`;
        if (days < 7) return `${days}d atrás`;
    }

    if (full) {
        return d.toLocaleDateString('pt-BR', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    return d.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
};

/**
 * Copia texto para clipboard
 * @param {string} text - Texto a copiar
 * @returns {Promise<boolean>}
 */
window.copyToClipboard = async function (text) {
    try {
        await navigator.clipboard.writeText(text);
        getNotificationService().success('Copiado para a área de transferência!');
        return true;
    } catch (error) {
        getNotificationService().error('Falha ao copiar');
        return false;
    }
};

/**
 * Download de dados como arquivo
 * @param {Object|string} data - Dados
 * @param {string} filename - Nome do arquivo
 * @param {string} type - Tipo MIME
 */
window.downloadFile = function (data, filename, type = 'application/json') {
    const content = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    getNotificationService().success(`Arquivo "${filename}" baixado!`);
};

/**
 * Exporta dados do estado atual
 * @param {string} format - Formato (json, csv)
 */
window.exportData = function (format = 'json') {
    const state = getStateManager();
    const data = {
        exportedAt: new Date().toISOString(),
        currentUser: state.get('currentUser'),
        profile: state.get('profile'),
        activities: state.get('activities'),
        sentiment: state.get('sentiment'),
        predictions: state.get('predictions')
    };

    const timestamp = new Date().toISOString().slice(0, 10);

    if (format === 'json') {
        downloadFile(data, `instagram-analysis-${timestamp}.json`);
    } else if (format === 'csv') {
        // Converter atividades para CSV
        const activities = state.get('activities', []);
        const headers = ['Tipo', 'Usuário Alvo', 'Texto', 'Data', 'URL'];
        const rows = activities.map(a => [
            a.type,
            a.target_user || '',
            a.comment_text || '',
            a.timestamp || '',
            a.post_url || ''
        ]);

        const csv = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
        downloadFile(csv, `instagram-activities-${timestamp}.csv`, 'text/csv');
    }
};

// =============================================================================
// INICIALIZAÇÃO QUANDO DOM ESTIVER PRONTO
// =============================================================================

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Export para módulos
export { initApp, applyTheme, toggleTheme, CONFIG };
