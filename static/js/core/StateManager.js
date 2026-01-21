/**
 * StateManager.js - Gerenciamento de Estado Global
 * 
 * Implementa padrão Pub/Sub para gerenciamento de estado reativo.
 * Similar a um Redux simplificado ou Vuex.
 * 
 * @module StateManager
 * @version 1.0.0
 */

export class StateManager {
    /**
     * Cria uma instância do StateManager
     * @param {Object} initialState - Estado inicial
     */
    constructor(initialState = {}) {
        this.state = {
            // Status do sistema
            system: {
                status: 'offline',
                version: null,
                lastCheck: null
            },

            // Usuário atual sendo analisado
            currentUser: null,

            // Perfil do usuário
            profile: null,

            // Posts do usuário
            posts: [],

            // Atividades rastreadas
            activities: [],

            // Análise de sentimento
            sentiment: null,

            // Previsões comportamentais
            predictions: null,

            // Análise visual
            visualAnalysis: null,

            // Grafo de rede
            networkGraph: null,

            // Localizações
            locations: [],

            // Analytics
            analytics: {
                engagementRate: null,
                bestTime: null,
                hashtags: null,
                audienceQuality: null,
                contentCalendar: null,
                mentions: null,
                collaborations: null
            },

            // OSINT
            osint: {
                accountHealth: null,
                breachCheck: null,
                crossPlatform: null
            },

            // Histórico
            history: {
                bio: [],
                snapshots: []
            },

            // Tasks
            tasks: [],

            // UI State
            ui: {
                loading: false,
                loadingMessage: '',
                activeTab: 'overview',
                sidebarOpen: true,
                theme: 'light',
                notifications: []
            },

            // Erros
            errors: [],

            // Override com estado inicial
            ...initialState
        };

        this.subscribers = new Map();
        this.history = [];
        this.maxHistory = 50;

        // Bind methods
        this.get = this.get.bind(this);
        this.set = this.set.bind(this);
        this.subscribe = this.subscribe.bind(this);
    }

    /**
     * Obtém valor do estado por caminho
     * @param {string} path - Caminho do estado (ex: "ui.loading")
     * @param {*} defaultValue - Valor padrão se não encontrado
     * @returns {*} Valor do estado
     */
    get(path, defaultValue = null) {
        if (!path) return this.state;

        const keys = path.split('.');
        let value = this.state;

        for (const key of keys) {
            if (value === null || value === undefined) {
                return defaultValue;
            }
            value = value[key];
        }

        return value !== undefined ? value : defaultValue;
    }

    /**
     * Define valor no estado
     * @param {string} path - Caminho do estado
     * @param {*} value - Novo valor
     * @param {boolean} silent - Se true, não notifica subscribers
     */
    set(path, value, silent = false) {
        const keys = path.split('.');
        const lastKey = keys.pop();

        // Salvar estado anterior para histórico
        const previousValue = this.get(path);

        // Navegar até o objeto pai
        let current = this.state;
        for (const key of keys) {
            if (current[key] === undefined) {
                current[key] = {};
            }
            current = current[key];
        }

        // Definir novo valor
        current[lastKey] = value;

        // Adicionar ao histórico
        this.history.push({
            path,
            previousValue,
            newValue: value,
            timestamp: Date.now()
        });

        // Manter histórico limitado
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        }

        // Notificar subscribers
        if (!silent) {
            this.notify(path, value, previousValue);
        }

        // Persistir se necessário
        this.persist();
    }

    /**
     * Atualiza múltiplos valores de uma vez
     * @param {Object} updates - Objeto com path: value
     */
    batch(updates) {
        for (const [path, value] of Object.entries(updates)) {
            this.set(path, value, true);
        }

        // Notificar uma vez para cada path
        for (const path of Object.keys(updates)) {
            this.notify(path, this.get(path));
        }
    }

    /**
     * Adiciona item a um array no estado
     * @param {string} path - Caminho do array
     * @param {*} item - Item a adicionar
     */
    push(path, item) {
        const array = this.get(path, []);
        this.set(path, [...array, item]);
    }

    /**
     * Remove item de um array no estado
     * @param {string} path - Caminho do array
     * @param {Function} predicate - Função para encontrar o item
     */
    remove(path, predicate) {
        const array = this.get(path, []);
        this.set(path, array.filter((item, index) => !predicate(item, index)));
    }

    /**
     * Inscreve-se para mudanças em um caminho do estado
     * @param {string} path - Caminho para observar (ou '*' para tudo)
     * @param {Function} callback - Callback chamado em mudanças
     * @returns {Function} Função para cancelar inscrição
     */
    subscribe(path, callback) {
        if (!this.subscribers.has(path)) {
            this.subscribers.set(path, new Set());
        }

        this.subscribers.get(path).add(callback);

        // Retorna função para unsubscribe
        return () => {
            this.subscribers.get(path)?.delete(callback);
        };
    }

    /**
     * Notifica subscribers sobre mudança
     * @param {string} path - Caminho alterado
     * @param {*} newValue - Novo valor
     * @param {*} previousValue - Valor anterior
     */
    notify(path, newValue, previousValue) {
        // Notificar subscribers do caminho exato
        const callbacks = this.subscribers.get(path);
        if (callbacks) {
            callbacks.forEach(cb => cb(newValue, previousValue, path));
        }

        // Notificar subscribers de caminhos pai
        const parts = path.split('.');
        for (let i = parts.length - 1; i > 0; i--) {
            const parentPath = parts.slice(0, i).join('.');
            const parentCallbacks = this.subscribers.get(parentPath);
            if (parentCallbacks) {
                parentCallbacks.forEach(cb => cb(this.get(parentPath), null, path));
            }
        }

        // Notificar subscribers globais
        const globalCallbacks = this.subscribers.get('*');
        if (globalCallbacks) {
            globalCallbacks.forEach(cb => cb(this.state, null, path));
        }
    }

    /**
     * Persiste estado no localStorage
     */
    persist() {
        try {
            // Persistir apenas dados selecionados
            const toPersist = {
                ui: {
                    theme: this.state.ui.theme,
                    sidebarOpen: this.state.ui.sidebarOpen
                },
                currentUser: this.state.currentUser
            };

            localStorage.setItem('instagramTracker_state', JSON.stringify(toPersist));
        } catch (e) {
            console.warn('[StateManager] Falha ao persistir estado:', e);
        }
    }

    /**
     * Restaura estado do localStorage
     */
    restore() {
        try {
            const saved = localStorage.getItem('instagramTracker_state');
            if (saved) {
                const parsed = JSON.parse(saved);

                // Restaurar apenas dados seguros
                if (parsed.ui?.theme) {
                    this.set('ui.theme', parsed.ui.theme, true);
                }
                if (parsed.ui?.sidebarOpen !== undefined) {
                    this.set('ui.sidebarOpen', parsed.ui.sidebarOpen, true);
                }
                if (parsed.currentUser) {
                    this.set('currentUser', parsed.currentUser, true);
                }
            }
        } catch (e) {
            console.warn('[StateManager] Falha ao restaurar estado:', e);
        }
    }

    /**
     * Reseta estado para inicial
     * @param {string} path - Caminho para resetar (ou null para tudo)
     */
    reset(path = null) {
        if (path) {
            // Encontrar valor inicial para o path
            const initialState = new StateManager().state;
            const keys = path.split('.');
            let value = initialState;

            for (const key of keys) {
                value = value?.[key];
            }

            this.set(path, value);
        } else {
            // Reset completo
            this.state = new StateManager().state;
            this.notify('*', this.state);
        }
    }

    /**
     * Adiciona notificação na UI
     * @param {Object} notification - Objeto de notificação
     */
    addNotification(notification) {
        const id = Date.now().toString();
        const fullNotification = {
            id,
            type: 'info',
            title: '',
            message: '',
            duration: 5000,
            ...notification
        };

        this.push('ui.notifications', fullNotification);

        // Auto-remover após duration
        if (fullNotification.duration > 0) {
            setTimeout(() => {
                this.removeNotification(id);
            }, fullNotification.duration);
        }

        return id;
    }

    /**
     * Remove notificação
     * @param {string} id - ID da notificação
     */
    removeNotification(id) {
        this.remove('ui.notifications', n => n.id === id);
    }

    /**
     * Define loading state
     * @param {boolean} loading - Se está carregando
     * @param {string} message - Mensagem de loading
     */
    setLoading(loading, message = '') {
        this.batch({
            'ui.loading': loading,
            'ui.loadingMessage': message
        });
    }

    /**
     * Adiciona erro
     * @param {Error|string} error - Erro ocorrido
     * @param {string} context - Contexto do erro
     */
    addError(error, context = '') {
        const errorObj = {
            id: Date.now().toString(),
            message: error.message || String(error),
            context,
            timestamp: Date.now(),
            stack: error.stack
        };

        this.push('errors', errorObj);

        // Também adicionar como notificação
        this.addNotification({
            type: 'error',
            title: 'Erro',
            message: errorObj.message
        });
    }

    /**
     * Limpa erros
     */
    clearErrors() {
        this.set('errors', []);
    }

    /**
     * Obtém snapshot do estado atual
     * @returns {Object} Estado completo
     */
    getSnapshot() {
        return JSON.parse(JSON.stringify(this.state));
    }

    /**
     * Obtém histórico de mudanças
     * @param {number} limit - Limite de itens
     * @returns {Array} Histórico
     */
    getHistory(limit = 10) {
        return this.history.slice(-limit);
    }

    // ==========================================================================
    // COMPUTED PROPERTIES (Valores derivados)
    // ==========================================================================

    /**
     * Verifica se está pronto para análise
     * @returns {boolean}
     */
    isReadyForAnalysis() {
        return this.get('system.status') === 'online' &&
            this.get('currentUser') !== null;
    }

    /**
     * Obtém total de atividades
     * @returns {Object} Contagem por tipo
     */
    getActivityCounts() {
        const activities = this.get('activities', []);
        return {
            total: activities.length,
            likes: activities.filter(a => a.type === 'outgoing_like').length,
            comments: activities.filter(a => a.type === 'outgoing_comment').length,
            mentions: activities.filter(a => a.type === 'mention').length
        };
    }

    /**
     * Obtém resumo do perfil atual
     * @returns {Object|null}
     */
    getProfileSummary() {
        const profile = this.get('profile');
        if (!profile) return null;

        return {
            username: profile.username,
            fullName: profile.full_name,
            followers: profile.followers_count,
            following: profile.following_count,
            posts: profile.media_count,
            isPrivate: profile.is_private,
            isVerified: profile.is_verified,
            profilePic: profile.profile_pic_url
        };
    }

    /**
     * Verifica se há dados carregados
     * @returns {Object} Status de cada seção
     */
    getDataLoadStatus() {
        return {
            profile: this.get('profile') !== null,
            posts: this.get('posts', []).length > 0,
            activities: this.get('activities', []).length > 0,
            sentiment: this.get('sentiment') !== null,
            predictions: this.get('predictions') !== null,
            visualAnalysis: this.get('visualAnalysis') !== null,
            networkGraph: this.get('networkGraph') !== null,
            locations: this.get('locations', []).length > 0
        };
    }
}

// Singleton global
let stateManager = null;

/**
 * Obtém instância única do StateManager
 * @param {Object} initialState - Estado inicial
 * @returns {StateManager}
 */
export function getStateManager(initialState = {}) {
    if (!stateManager) {
        stateManager = new StateManager(initialState);
        stateManager.restore();
    }
    return stateManager;
}

// Export default
export default StateManager;
