/**
 * APIService.js - Serviço de chamadas à API
 * 
 * Wrapper centralizado para todas as chamadas à API REST.
 * Inclui: error handling, retry automático, cache local, loading states.
 * 
 * @module APIService
 * @version 1.0.0
 */

export class APIService {
    /**
     * Cria uma instância do APIService
     * @param {Object} options - Opções de configuração
     * @param {string} options.baseURL - URL base da API
     * @param {number} options.timeout - Timeout em milissegundos
     * @param {number} options.retries - Número de tentativas
     */
    constructor(options = {}) {
        this.baseURL = options.baseURL || window.location.origin;
        this.timeout = options.timeout || 30000;
        this.retries = options.retries || 3;
        this.cache = new Map();
        this.cacheTimeout = options.cacheTimeout || 5 * 60 * 1000; // 5 minutos
        this.pendingRequests = new Map();
        this.listeners = new Map();

        // Bind methods
        this.get = this.get.bind(this);
        this.post = this.post.bind(this);
        this.request = this.request.bind(this);
    }

    /**
     * Registra um listener para eventos
     * @param {string} event - Nome do evento
     * @param {Function} callback - Callback
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
     * Emite um evento
     * @param {string} event - Nome do evento
     * @param {*} data - Dados do evento
     */
    emit(event, data) {
        const callbacks = this.listeners.get(event) || [];
        callbacks.forEach(cb => cb(data));
    }

    /**
     * Gera uma chave de cache única
     * @param {string} method - Método HTTP
     * @param {string} url - URL
     * @param {Object} params - Parâmetros
     * @returns {string} Chave de cache
     */
    getCacheKey(method, url, params = {}) {
        return `${method}:${url}:${JSON.stringify(params)}`;
    }

    /**
     * Verifica se há cache válido
     * @param {string} key - Chave do cache
     * @returns {*} Valor em cache ou null
     */
    getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        return null;
    }

    /**
     * Salva no cache
     * @param {string} key - Chave do cache
     * @param {*} data - Dados
     */
    setCache(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Limpa o cache
     * @param {string} pattern - Padrão para limpar (opcional)
     */
    clearCache(pattern = null) {
        if (pattern) {
            for (const key of this.cache.keys()) {
                if (key.includes(pattern)) {
                    this.cache.delete(key);
                }
            }
        } else {
            this.cache.clear();
        }
    }

    /**
     * Faz uma requisição com retry automático
     * @param {string} url - URL relativa
     * @param {Object} options - Opções do fetch
     * @param {number} retryCount - Contador de tentativas
     * @returns {Promise<Object>} Resposta da API
     */
    async request(url, options = {}, retryCount = 0) {
        const fullURL = url.startsWith('http') ? url : `${this.baseURL}${url}`;
        const cacheKey = this.getCacheKey(options.method || 'GET', fullURL, options.body);

        // Verificar cache para GET requests
        if (options.method !== 'POST' && !options.skipCache) {
            const cached = this.getFromCache(cacheKey);
            if (cached) {
                console.log(`[APIService] Cache hit: ${url}`);
                return cached;
            }
        }

        // Evitar requisições duplicadas
        if (this.pendingRequests.has(cacheKey)) {
            return this.pendingRequests.get(cacheKey);
        }

        // Configuração padrão
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            ...options
        };

        // Emitir evento de loading
        this.emit('loading:start', { url, method: config.method });

        // Criar promise da requisição
        const requestPromise = new Promise(async (resolve, reject) => {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            try {
                console.log(`[APIService] ${config.method} ${url}`);

                const response = await fetch(fullURL, {
                    ...config,
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                // Verificar status
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    const error = new Error(errorData.error || `HTTP ${response.status}`);
                    error.status = response.status;
                    error.data = errorData;
                    throw error;
                }

                // Parsear resposta
                const data = await response.json();

                // Salvar no cache para GET
                if (config.method !== 'POST' && !options.skipCache) {
                    this.setCache(cacheKey, data);
                }

                // Emitir sucesso
                this.emit('loading:end', { url, method: config.method, success: true });
                this.emit('request:success', { url, data });

                resolve(data);

            } catch (error) {
                clearTimeout(timeoutId);

                // Retry em caso de erro de rede
                if (retryCount < this.retries && this.shouldRetry(error)) {
                    console.log(`[APIService] Retry ${retryCount + 1}/${this.retries}: ${url}`);
                    const delay = Math.pow(2, retryCount) * 1000 + Math.random() * 1000;

                    await new Promise(r => setTimeout(r, delay));

                    this.pendingRequests.delete(cacheKey);
                    resolve(this.request(url, options, retryCount + 1));
                    return;
                }

                // Emitir erro
                this.emit('loading:end', { url, method: config.method, success: false });
                this.emit('request:error', { url, error });

                console.error(`[APIService] Error: ${url}`, error);
                reject(error);
            }
        });

        this.pendingRequests.set(cacheKey, requestPromise);

        try {
            const result = await requestPromise;
            return result;
        } finally {
            this.pendingRequests.delete(cacheKey);
        }
    }

    /**
     * Verifica se deve fazer retry
     * @param {Error} error - Erro ocorrido
     * @returns {boolean}
     */
    shouldRetry(error) {
        // Retry em caso de erro de rede ou timeout
        if (error.name === 'AbortError') return true;
        if (error.name === 'TypeError') return true; // Network error
        if (error.status === 429) return true; // Rate limited
        if (error.status >= 500) return true; // Server error
        return false;
    }

    /**
     * GET request
     * @param {string} url - URL
     * @param {Object} params - Query parameters
     * @param {Object} options - Opções extras
     * @returns {Promise<Object>}
     */
    async get(url, params = {}, options = {}) {
        // Adicionar query params à URL
        const queryString = Object.entries(params)
            .filter(([_, v]) => v !== undefined && v !== null && v !== '')
            .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
            .join('&');

        const fullURL = queryString ? `${url}?${queryString}` : url;

        return this.request(fullURL, { method: 'GET', ...options });
    }

    /**
     * POST request
     * @param {string} url - URL
     * @param {Object} body - Body da requisição
     * @param {Object} options - Opções extras
     * @returns {Promise<Object>}
     */
    async post(url, body = {}, options = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(body),
            ...options
        });
    }

    // ==========================================================================
    // ENDPOINTS ESPECÍFICOS DA API
    // ==========================================================================

    /**
     * Verifica status da API
     * @returns {Promise<Object>}
     */
    async getStatus() {
        return this.get('/api/instagram/status');
    }

    /**
     * Obtém informações do usuário
     * @param {string} username - Nome de usuário
     * @param {Object} credentials - Credenciais opcionais
     * @returns {Promise<Object>}
     */
    async getUserInfo(username, credentials = {}) {
        return this.get('/api/instagram/user-info', {
            username,
            login_username: credentials.username,
            login_password: credentials.password
        });
    }

    /**
     * Obtém posts do usuário
     * @param {string} username - Nome de usuário
     * @param {Object} options - Opções (limit, start_date, end_date)
     * @returns {Promise<Object>}
     */
    async getPosts(username, options = {}) {
        return this.get('/api/instagram/posts', {
            username,
            limit: options.limit || 20,
            start_date: options.startDate,
            end_date: options.endDate,
            media_type: options.mediaType
        });
    }

    /**
     * Obtém lista de seguindo
     * @param {string} username - Nome de usuário
     * @param {number} limit - Limite
     * @returns {Promise<Object>}
     */
    async getFollowing(username, limit = 50) {
        return this.get('/api/instagram/following', { username, limit });
    }

    /**
     * Rastreia atividades do usuário
     * @param {string} username - Nome de usuário
     * @param {Object} options - Opções de rastreamento
     * @returns {Promise<Object>}
     */
    async trackActivities(username, options = {}) {
        return this.get('/api/instagram/track', {
            username,
            login_username: options.loginUsername,
            login_password: options.loginPassword,
            max_following: options.maxFollowing || 20,
            ignored_users: options.ignoredUsers?.join(',')
        }, { skipCache: true });
    }

    /**
     * Obtém localizações do usuário
     * @param {string} username - Nome de usuário
     * @param {number} limit - Limite
     * @returns {Promise<Object>}
     */
    async getLocations(username, limit = 50) {
        return this.get('/api/instagram/locations', { username, limit });
    }

    // ==========================================================================
    // ENDPOINTS DE INTELIGÊNCIA
    // ==========================================================================

    /**
     * Analisa sentimento do usuário
     * @param {string} username - Nome de usuário
     * @param {Object} options - Opções
     * @returns {Promise<Object>}
     */
    async analyzeSentiment(username, options = {}) {
        return this.get(`/api/intelligence/sentiment/${username}`, {
            include_bio: options.includeBio ?? true,
            include_posts: options.includePosts ?? true,
            max_posts: options.maxPosts || 20
        });
    }

    /**
     * Analisa sentimento de um texto específico
     * @param {string} text - Texto para analisar
     * @returns {Promise<Object>}
     */
    async analyzeSentimentText(text) {
        return this.post('/api/intelligence/sentiment/text', { text });
    }

    /**
     * Obtém previsões comportamentais
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async getPredictions(username) {
        return this.get(`/api/intelligence/prediction/${username}`);
    }

    /**
     * Analisa imagens do perfil
     * @param {string} username - Nome de usuário
     * @param {number} maxImages - Máximo de imagens
     * @returns {Promise<Object>}
     */
    async analyzeVisual(username, maxImages = 20) {
        return this.get(`/api/intelligence/visual/${username}`, { max_images: maxImages });
    }

    /**
     * Obtém grafo de rede social
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async getNetworkGraph(username) {
        return this.get(`/api/intelligence/network-graph/${username}`);
    }

    // ==========================================================================
    // ENDPOINTS DE ANALYTICS
    // ==========================================================================

    /**
     * Obtém taxa de engajamento
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async getEngagementRate(username) {
        return this.get(`/api/analytics/engagement-rate/${username}`);
    }

    /**
     * Obtém melhor horário para postar
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async getBestTime(username) {
        return this.get(`/api/analytics/best-time/${username}`);
    }

    /**
     * Analisa hashtags usadas
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async analyzeHashtags(username) {
        return this.get(`/api/analytics/hashtags/${username}`);
    }

    /**
     * Avalia qualidade da audiência
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async getAudienceQuality(username) {
        return this.get(`/api/analytics/audience-quality/${username}`);
    }

    /**
     * Obtém calendário de conteúdo
     * @param {string} username - Nome de usuário
     * @param {Object} options - Opções (year, month)
     * @returns {Promise<Object>}
     */
    async getContentCalendar(username, options = {}) {
        return this.get(`/api/analytics/content-calendar/${username}`, options);
    }

    /**
     * Obtém menções do usuário
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async getMentions(username) {
        return this.get(`/api/analytics/mentions/${username}`);
    }

    /**
     * Detecta colaborações
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async getCollaborations(username) {
        return this.get(`/api/analytics/collaborations/${username}`);
    }

    /**
     * Compara perfis
     * @param {string[]} usernames - Lista de usernames
     * @returns {Promise<Object>}
     */
    async compareProfiles(usernames) {
        return this.post('/api/analytics/compare', { usernames });
    }

    // ==========================================================================
    // ENDPOINTS OSINT
    // ==========================================================================

    /**
     * Verifica saúde da conta
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async getAccountHealth(username) {
        return this.get(`/api/osint/account-health/${username}`);
    }

    /**
     * Verifica vazamentos de dados
     * @param {string} identifier - Email ou username
     * @returns {Promise<Object>}
     */
    async checkBreach(identifier) {
        return this.get(`/api/osint/breach-check/${identifier}`);
    }

    /**
     * Busca em múltiplas plataformas
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async crossPlatformSearch(username) {
        return this.get(`/api/osint/cross-platform/${username}`);
    }

    // ==========================================================================
    // ENDPOINTS DE HISTÓRICO
    // ==========================================================================

    /**
     * Obtém histórico de bio
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async getBioHistory(username) {
        return this.get(`/api/history/bio/${username}`);
    }

    /**
     * Obtém snapshots do perfil
     * @param {string} username - Nome de usuário
     * @returns {Promise<Object>}
     */
    async getProfileSnapshots(username) {
        return this.get(`/api/history/profile-snapshots/${username}`);
    }

    // ==========================================================================
    // ENDPOINTS DE SISTEMA
    // ==========================================================================

    /**
     * Obtém saúde do GraphQL
     * @returns {Promise<Object>}
     */
    async getGraphQLHealth() {
        return this.get('/api/system/graphql-health');
    }

    /**
     * Obtém status de uma tarefa
     * @param {string} taskId - ID da tarefa
     * @returns {Promise<Object>}
     */
    async getTaskStatus(taskId) {
        return this.get(`/api/tasks/status/${taskId}`, {}, { skipCache: true });
    }

    /**
     * Lista tarefas
     * @param {string} status - Filtro de status
     * @returns {Promise<Object>}
     */
    async listTasks(status = null) {
        return this.get('/api/tasks/list', { status }, { skipCache: true });
    }

    /**
     * Enfileira uma tarefa
     * @param {string} taskType - Tipo da tarefa
     * @param {Object} metadata - Metadados
     * @param {string} priority - Prioridade
     * @returns {Promise<Object>}
     */
    async enqueueTask(taskType, metadata = {}, priority = 'normal') {
        return this.post('/api/tasks/enqueue', {
            task_type: taskType,
            metadata,
            priority
        });
    }

    /**
     * Cancela uma tarefa
     * @param {string} taskId - ID da tarefa
     * @returns {Promise<Object>}
     */
    async cancelTask(taskId) {
        return this.post(`/api/tasks/cancel/${taskId}`);
    }

    /**
     * Obtém estatísticas da fila
     * @returns {Promise<Object>}
     */
    async getQueueStats() {
        return this.get('/api/tasks/stats', {}, { skipCache: true });
    }

    /**
     * Testa o sistema
     * @returns {Promise<Object>}
     */
    async testSystem() {
        return this.get('/api/instagram/test', {}, { skipCache: true });
    }
}

// Singleton global
let apiService = null;

/**
 * Obtém instância única do APIService
 * @param {Object} options - Opções de configuração
 * @returns {APIService}
 */
export function getAPIService(options = {}) {
    if (!apiService) {
        apiService = new APIService(options);
    }
    return apiService;
}

// Export default
export default APIService;
