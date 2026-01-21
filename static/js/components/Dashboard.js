/**
 * Dashboard.js - Componente Principal do Dashboard
 * 
 * Gerencia o dashboard completo, integrando todos os widgets,
 * sidebar, navegação e exibição de resultados.
 * 
 * @module Dashboard
 * @version 2.0.0
 */

// Core Services
import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';
import { IntelligenceProgress } from './IntelligenceProgress.js';
import { getCacheService } from '../core/CacheService.js';
import { getWebSocketService } from '../core/WebSocketService.js';

// Core UI Managers
import { getTabsManager } from '../core/TabsManager.js';
import { createSearchAdvanced } from '../core/SearchAdvanced.js';
import { getExportService } from '../core/ExportService.js';
import { getLoadingStates } from '../core/LoadingStates.js';
import { getResponsiveLayout } from '../core/ResponsiveLayout.js';

// Widget Components
import { createProfileCard } from './ProfileCard.js';
import { createActivityFeed } from './ActivityFeed.js';
import { createSentimentWidget } from './SentimentWidget.js';
import { createGraphVisualizer } from './GraphVisualizer.js';
import { createGeoHeatmap } from './GeoHeatmap.js';
import { createPredictiveWidget } from './PredictiveWidget.js';
import { createVisionWidget } from './VisionWidget.js';
import { createEngagementChart } from './EngagementChart.js';
import { createOSINTToolbar } from './OSINTToolbar.js';
import { createAIInsightsPanel } from './AIInsightsPanel.js';
import { createCalendarView } from './CalendarView.js';
import { createTopInteractionsWidget } from './TopInteractionsWidget.js';
import { createBreachCheckWidget } from './BreachCheckWidget.js';
import { createChatWidget } from './ChatWidget.js';

export class Dashboard {
    /**
     * Cria uma instância do Dashboard
     * @param {HTMLElement} container - Container principal
     */
    constructor(container) {
        this.container = container || document.getElementById('app');

        // Core Services
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();
        this.cache = getCacheService();
        this.ws = getWebSocketService();

        // UI Managers
        this.loadingStates = getLoadingStates();
        this.exportService = getExportService();
        this.responsiveLayout = getResponsiveLayout();

        // Componentes filhos
        this.components = new Map();
        this.widgets = new Map();
        
        // Progress Tracker 2026
        this.progressTracker = new IntelligenceProgress('intelligence-progress-container');

        // Tabs Manager (será inicializado no init)
        this.tabsManager = null;

        // Search Component
        this.searchComponent = null;

        // Bind methods
        this.init = this.init.bind(this);
        this.render = this.render.bind(this);
        this.handleSearch = this.handleSearch.bind(this);
        this.initializeWidgets = this.initializeWidgets.bind(this);
    }

    /**
     * Inicializa o dashboard
     */
    async init() {
        console.log('[Dashboard] Inicializando v2.0...');

        // Mostrar loading inicial
        this.loadingStates.showProgress('Inicializando dashboard...');

        // Inicializar estado de notificações
        this.state.set('notifications.chat', 0);
        this.state.set('notifications.breach', 0);

        // Inicializar layout responsivo
        this.responsiveLayout.onChange((info) => {
            console.log('[Dashboard] Breakpoint alterado:', info.breakpoint);
            this.handleBreakpointChange(info);
        });

        // Verificar status da API
        this.loadingStates.updateProgress(20, 'Verificando conexão...');
        await this.checkSystemStatus();

        // Inicializar TabsManager
        this.loadingStates.updateProgress(40, 'Carregando navegação...');
        const tabsContainer = document.getElementById('tabs-container');
        const contentContainer = document.getElementById('main-content');

        if (tabsContainer) {
            this.tabsManager = getTabsManager({
                container: tabsContainer,
                contentContainer: contentContainer
            });
            this.tabsManager.init();

            // Callback de mudança de tab
            this.tabsManager.onChange((tabId, tab) => {
                this.handleTabChange(tabId, tab);
            });
        }

        // Inicializar Search
        this.loadingStates.updateProgress(50, 'Configurando busca...');
        const searchContainer = document.getElementById('search-container');
        if (searchContainer) {
            this.searchComponent = createSearchAdvanced(searchContainer);
            searchContainer.addEventListener('search', (e) => {
                this.handleSearch(e.detail);
            });
        }

        // Setup event listeners
        this.loadingStates.updateProgress(60, 'Configurando eventos...');
        this.setupEventListeners();

        // Restaurar estado
        this.loadingStates.updateProgress(70, 'Restaurando estado...');
        this.state.restore();

        // Inicializar widgets
        this.loadingStates.updateProgress(80, 'Carregando widgets...');
        await this.initializeWidgets();

        // Render inicial
        this.loadingStates.updateProgress(90, 'Renderizando...');
        this.render();

        // Verificar se há usuário atual
        const currentUser = this.state.get('currentUser');
        if (currentUser) {
            this.loadUserData(currentUser);
        }

        // Finalizar loading
        this.loadingStates.hideProgress();
        console.log('[Dashboard] Inicializado com sucesso!');
    }

    /**
     * Inicializa todos os widgets
     */
    async initializeWidgets() {
        console.log('[Dashboard] Inicializando widgets...');

        // Profile Card
        const profileContainer = document.getElementById('profile-card');
        if (profileContainer) {
            this.widgets.set('profile', createProfileCard(profileContainer));
        }

        // Activity Feed (usar o container existente)
        const activityContainer = document.getElementById('activities-list');
        if (activityContainer) {
            this.widgets.set('activityFeed', createActivityFeed(activityContainer));
        }

        // Sentiment Widget
        const sentimentContainer = document.getElementById('sentiment-widget');
        if (sentimentContainer) {
            this.widgets.set('sentiment', createSentimentWidget(sentimentContainer));
        }

        // Predictive Widget
        const predictiveContainer = document.getElementById('predictive-widget');
        if (predictiveContainer) {
            this.widgets.set('predictive', createPredictiveWidget(predictiveContainer));
        }

        // Vision Widget
        const visionContainer = document.getElementById('vision-widget');
        if (visionContainer) {
            this.widgets.set('vision', createVisionWidget(visionContainer));
        }

        // Graph Visualizer (usar ID existente)
        const graphContainer = document.getElementById('network-graph');
        if (graphContainer) {
            this.widgets.set('graph', createGraphVisualizer(graphContainer));
        }

        // Geo Heatmap (usar ID existente)
        const geoContainer = document.getElementById('location-map');
        if (geoContainer) {
            this.widgets.set('geoHeatmap', createGeoHeatmap(geoContainer));
        }

        // Engagement Chart (criar se necessário ou usar existente)
        const engagementContainer = document.getElementById('engagement-chart');
        if (engagementContainer) {
            this.widgets.set('engagement', createEngagementChart(engagementContainer));
        }

        // Calendar View
        const calendarContainer = document.getElementById('calendar-view');
        if (calendarContainer) {
            this.widgets.set('calendar', createCalendarView(calendarContainer));
        }

        // Top Interactions Widget (Outgoing)
        const topOutgoingContainer = document.getElementById('top-outgoing-widget');
        if (topOutgoingContainer) {
            this.widgets.set('topOutgoing', createTopInteractionsWidget(topOutgoingContainer, { type: 'outgoing' }));
        }

        // Top Interactions Widget (Incoming)
        const topIncomingContainer = document.getElementById('top-incoming-widget');
        if (topIncomingContainer) {
            this.widgets.set('topIncoming', createTopInteractionsWidget(topIncomingContainer, { type: 'incoming' }));
        }

        // OSINT Toolbar (usar container da tab)
        const osintContainer = document.getElementById('platform-results');
        if (osintContainer) {
            this.widgets.set('osint', createOSINTToolbar(osintContainer));
        }

        // Breach Check Widget
        const breachContainer = document.getElementById('breach-results');
        if (breachContainer) {
            this.widgets.set('breachCheck', createBreachCheckWidget(breachContainer));
        }

        // Chat Widget
        const chatContainer = document.getElementById('chat-widget-container');
        if (chatContainer) {
            this.widgets.set('chat', createChatWidget(chatContainer));
        }

        // AI Insights Panel (será usado sob demanda)
        // Pode ser inserido em qualquer tab de IA quando necessário

        console.log(`[Dashboard] ${this.widgets.size} widgets inicializados`);
    }

    /**
     * Handler de mudança de tab
     * @param {string} tabId - ID da tab
     * @param {Object} tab - Definição da tab
     */
    handleTabChange(tabId, tab) {
        console.log('[Dashboard] Tab alterada:', tabId);

        // Atualizar state
        this.state.set('ui.activeTab', tabId);

        // Carregar dados específicos da tab se necessário
        const currentUser = this.state.get('currentUser');
        if (!currentUser) return;

        switch (tabId) {
            case 'intelligence':
                this.loadAIAnalysis(currentUser);
                break;
            case 'network':
                this.loadNetworkData(currentUser);
                break;
            case 'osint':
                // OSINT carrega dados sob demanda
                break;
            case 'history':
                this.loadHistoryData(currentUser);
                break;
        }
    }

    /**
     * Handler de mudança de breakpoint
     * @param {Object} info - Informações do breakpoint
     */
    handleBreakpointChange(info) {
        // Atualizar state
        this.state.set('ui.breakpoint', info.breakpoint);
        this.state.set('ui.isMobile', info.isMobile);

        // Ajustar widgets se necessário
        if (info.isMobile) {
            // Fechar sidebar se aberta
            this.closeMobileSidebar();
        }

        // Re-render widgets que precisam se ajustar
        this.widgets.forEach((widget, key) => {
            if (widget && typeof widget.handleResize === 'function') {
                widget.handleResize();
            }
        });
    }

    /**
     * Carrega dados de rede social
     * @param {string} username - Nome de usuário
     */
    async loadNetworkData(username) {
        const graphWidget = this.widgets.get('graph');
        if (!graphWidget) return;

        const graphData = this.state.get('networkGraph');
        if (graphData) {
            // Já tem dados em cache
            graphWidget.setData(graphData);
            return;
        }

        // Buscar dados da API
        try {
            const result = await this.api.getNetworkGraph(username);
            if (result.success) {
                this.state.set('networkGraph', result.graph);
                graphWidget.setData(result.graph);
            }
        } catch (error) {
            console.error('[Dashboard] Erro ao carregar grafo:', error);
        }
    }

    /**
     * Carrega dados históricos
     * @param {string} username - Nome de usuário
     */
    async loadHistoryData(username) {
        const calendarWidget = this.widgets.get('calendar');
        if (!calendarWidget) return;

        try {
            const result = await this.api.getActivityHistory(username);
            if (result.success) {
                calendarWidget.setData(result.activities);
            }
        } catch (error) {
            console.error('[Dashboard] Erro ao carregar histórico:', error);
        }
    }

    /**
     * Verifica status do sistema
     */
    async checkSystemStatus() {
        try {
            const status = await this.api.getStatus();
            this.state.batch({
                'system.status': 'online',
                'system.version': status.version,
                'system.lastCheck': Date.now()
            });
        } catch (error) {
            this.state.set('system.status', 'offline');
            this.notifications.error('Não foi possível conectar à API', 'Erro de Conexão');
        }
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Sidebar toggle
        document.addEventListener('click', (e) => {
            if (e.target.closest('.sidebar__toggle')) {
                this.toggleSidebar();
            }

            if (e.target.closest('.mobile-menu-toggle')) {
                this.toggleMobileSidebar();
            }

            if (e.target.closest('.sidebar-overlay')) {
                this.closeMobileSidebar();
            }
        });

        // Navegação de tabs
        document.addEventListener('click', (e) => {
            const tabBtn = e.target.closest('.tab-btn, .sidebar__link[data-tab]');
            if (tabBtn) {
                const tab = tabBtn.dataset.tab;
                if (tab) {
                    this.switchTab(tab);
                }
            }
        });

        // Form de busca
        const searchForm = document.getElementById('search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', this.handleSearch);
        }

        // Tracking form
        const trackingForm = document.getElementById('tracking-form');
        if (trackingForm) {
            trackingForm.addEventListener('submit', (e) => this.handleTrackingSubmit(e));
        }

        // Subscribe to state changes
        this.state.subscribe('currentUser', (user) => {
            if (user) {
                this.loadUserData(user);
            }
        });

        this.state.subscribe('ui.loading', (loading) => {
            this.updateLoadingState(loading);
        });

        this.state.subscribe('ui.activeTab', (tab) => {
            this.updateActiveTab(tab);
        });

        // API loading events
        this.api.on('loading:start', () => {
            this.state.set('ui.loading', true);
        });

        this.api.on('loading:end', () => {
            this.state.set('ui.loading', false);
        });

        // Listeners de Notificações
        this.state.subscribe('notifications.chat', (count) => {
            this.updateBadge('chat-badge', count);
        });

        this.state.subscribe('notifications.breach', (count) => {
            this.updateBadge('breach-badge', count);
        });
    }

    /**
     * Atualiza um badge na sidebar
     * @param {string} badgeId - ID do elemento badge
     * @param {number} count - Contagem a exibir
     */
    updateBadge(badgeId, count) {
        const badge = document.getElementById(badgeId);
        if (badge) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
            
            // Adicionar animação de pulso se houver novas notificações
            if (count > 0) {
                badge.classList.add('pulse');
                setTimeout(() => badge.classList.remove('pulse'), 2000);
            }
        }
    }

    /**
     * Renderiza o dashboard
     */
    render() {
        // Atualizar indicador de status
        this.updateStatusIndicator();

        // Atualizar sidebar
        this.updateSidebar();

        // Atualizar conteúdo principal baseado na tab ativa
        this.updateMainContent();
    }

    /**
     * Atualiza indicador de status
     */
    updateStatusIndicator() {
        const statusDot = document.querySelector('.status-indicator__dot');
        const statusText = document.querySelector('.status-indicator__text');

        if (!statusDot) return;

        const status = this.state.get('system.status');

        statusDot.classList.remove('status-indicator__dot--online', 'status-indicator__dot--offline', 'status-indicator__dot--checking');
        statusDot.classList.add(`status-indicator__dot--${status}`);

        if (statusText) {
            statusText.textContent = status === 'online' ? 'Online' :
                status === 'checking' ? 'Verificando...' : 'Offline';
        }
    }

    /**
     * Atualiza a sidebar
     */
    updateSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;

        const isOpen = this.state.get('ui.sidebarOpen');
        sidebar.classList.toggle('sidebar--collapsed', !isOpen);

        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.classList.toggle('expanded', !isOpen);
        }
    }

    /**
     * Toggle da sidebar
     */
    toggleSidebar() {
        const current = this.state.get('ui.sidebarOpen');
        this.state.set('ui.sidebarOpen', !current);
        this.updateSidebar();
    }

    /**
     * Toggle sidebar mobile
     */
    toggleMobileSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.sidebar-overlay');

        if (sidebar) {
            sidebar.classList.toggle('open');
        }
        if (overlay) {
            overlay.classList.toggle('active');
        }
    }

    /**
     * Fecha sidebar mobile
     */
    closeMobileSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.sidebar-overlay');

        if (sidebar) sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
    }

    /**
     * Troca de tab
     * @param {string} tabId - ID da tab
     */
    switchTab(tabId) {
        this.state.set('ui.activeTab', tabId);

        // Zerar notificações ao entrar na aba
        if (tabId === 'chat') {
            this.state.set('notifications.chat', 0);
        } else if (tabId === 'breach') {
            this.state.set('notifications.breach', 0);
        }

        // Atualizar URL hash
        window.location.hash = tabId;

        // Fechar sidebar mobile
        this.closeMobileSidebar();
    }

    /**
     * Atualiza tab ativa na UI
     * @param {string} tabId - ID da tab
     */
    updateActiveTab(tabId) {
        // Atualizar botões de tab
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });

        // Atualizar links do sidebar
        document.querySelectorAll('.sidebar__link[data-tab]').forEach(link => {
            link.classList.toggle('sidebar__link--active', link.dataset.tab === tabId);
        });

        // Atualizar painéis de conteúdo
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `tab-${tabId}`);
        });
    }

    /**
     * Atualiza conteúdo principal
     */
    updateMainContent() {
        const activeTab = this.state.get('ui.activeTab');
        this.updateActiveTab(activeTab);
    }

    /**
     * Atualiza estado de loading
     * @param {boolean} loading - Se está carregando
     */
    updateLoadingState(loading) {
        const loadingOverlay = document.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = loading ? 'flex' : 'none';
        }

        // Desabilitar formulários durante loading
        document.querySelectorAll('form button[type="submit"]').forEach(btn => {
            btn.disabled = loading;
        });
    }

    /**
     * Handler de busca
     * @param {Event} e - Evento de submit
     */
    async handleSearch(e) {
        e.preventDefault();

        const input = e.target.querySelector('input[name="username"]');
        if (!input) return;

        const username = input.value.trim().replace('@', '');

        if (!username) {
            this.notifications.warning('Digite um nome de usuário', 'Campo obrigatório');
            return;
        }

        // Validar formato do username
        if (!/^[a-zA-Z0-9._]{1,30}$/.test(username)) {
            this.notifications.error('Nome de usuário inválido', 'Erro');
            return;
        }

        this.state.set('currentUser', username);
    }

    /**
     * Handler do form de rastreamento
     * @param {Event} e - Evento de submit
     */
    async handleTrackingSubmit(e) {
        e.preventDefault();

        const form = e.target;
        const formData = new FormData(form);

        const username = formData.get('username')?.trim().replace('@', '');
        const loginUsername = formData.get('login_username')?.trim();
        const loginPassword = formData.get('login_password');
        const maxFollowing = parseInt(formData.get('max_following')) || 20;
        const ignoredUsers = formData.get('ignored_users')?.split(',').map(u => u.trim()).filter(Boolean) || [];

        if (!username) {
            this.notifications.warning('Digite o nome de usuário alvo', 'Campo obrigatório');
            return;
        }

        // Iniciar rastreamento
        await this.startTracking({
            username,
            loginUsername,
            loginPassword,
            maxFollowing,
            ignoredUsers
        });
    }

    /**
     * Inicia rastreamento de atividades
     * @param {Object} options - Opções de rastreamento
     */
    async startTracking(options) {
        const loading = this.notifications.loading('Iniciando rastreamento...');
        this.progressTracker.show();
        this.progressTracker.update(5, 'Conectando ao Instagram...', 'Inicializando motor de rastreamento...');

        try {
            this.state.set('currentUser', options.username);
            this.progressTracker.update(15, 'Buscando perfil...', `Alvo: @${options.username}`);

            const result = await this.api.trackActivities(options.username, {
                loginUsername: options.loginUsername,
                loginPassword: options.loginPassword,
                maxFollowing: options.maxFollowing,
                ignoredUsers: options.ignoredUsers,
                onProgress: (data) => {
                    // Callback para progresso em tempo real se a API suportar
                    if (this.progressTracker) {
                        this.progressTracker.update(data.percent, data.status, data.log);
                    }
                }
            });

            if (result.success) {
                this.progressTracker.update(100, 'Rastreamento concluído!', 'Análise finalizada com sucesso.');
                setTimeout(() => this.progressTracker.hide(), 3000);

                this.state.set('activities', result.activities);
                this.state.set('affinity_ranking', result.affinity_ranking || []);

                // Notificar widget de feed se existir
                const feedWidget = this.widgets.get('activityFeed');
                if (feedWidget && typeof feedWidget.render === 'function') {
                    feedWidget.render();
                }

                loading.success(`${result.count || result.total_activities} atividades encontradas!`);

                // Mudar para aba de resultados
                this.switchTab('activities');

                // Renderizar resultados (fallback/sync)
                this.renderActivities(result.activities);
                this.renderActivityStats(result.activity_types || result.stats);
                
                // Renderizar ranking de afinidade
                if (result.affinity_ranking) {
                    this.renderTopInteractionsWidget(result.affinity_ranking, 'outgoing');
                }
            } else {
                loading.error(result.error || 'Erro no rastreamento');
            }
        } catch (error) {
            loading.error(error.message);
            this.state.addError(error, 'tracking');
        }
    }

    /**
     * Carrega dados do usuário
     * @param {string} username - Nome de usuário
     */
    async loadUserData(username) {
        const loading = this.notifications.loading(`Carregando dados de @${username}...`);

        try {
            // Carregar informações básicas
            loading.update('Buscando perfil...');
            const profileResult = await this.api.getUserInfo(username);

            if (profileResult.success) {
                this.state.set('profile', profileResult.user_info);
                this.renderProfileCard(profileResult.user_info);
            }

            // Carregar posts
            loading.update('Buscando posts recentes...');
            const postsResult = await this.api.getPosts(username, { limit: 20 });

            if (postsResult.success) {
                this.state.set('posts', postsResult.posts);
            }

            loading.success('Dados carregados!');

        } catch (error) {
            loading.error(`Erro ao carregar: ${error.message}`);
            this.state.addError(error, 'loadUserData');
        }
    }

    /**
     * Carrega análises de IA
     * @param {string} username - Nome de usuário
     */
    async loadAIAnalysis(username) {
        const loading = this.notifications.loading('Analisando com IA...');

        try {
            // Paralelo: Sentimento, Preditivo, Visual
            const [sentimentResult, predictiveResult, visualResult] = await Promise.allSettled([
                this.api.analyzeSentiment(username),
                this.api.getPredictions(username),
                this.api.analyzeVisual(username)
            ]);

            if (sentimentResult.status === 'fulfilled' && sentimentResult.value.success) {
                this.state.set('sentiment', sentimentResult.value);
                this.renderSentimentWidget(sentimentResult.value);
            }

            if (predictiveResult.status === 'fulfilled' && predictiveResult.value.success) {
                this.state.set('predictions', predictiveResult.value);
                this.renderPredictiveWidget(predictiveResult.value);
            }

            if (visualResult.status === 'fulfilled' && visualResult.value.success) {
                this.state.set('visualAnalysis', visualResult.value);
                this.renderVisionWidget(visualResult.value);
            }

            loading.success('Análise de IA concluída!');

        } catch (error) {
            loading.error(error.message);
        }
    }

    /**
     * Calcula top interações
     * @param {Array} activities - Lista de atividades
     */
    calculateTopInteractions(activities) {
        // Top pessoas que o rastreado mais interagiu
        const outgoingInteractions = {};
        activities.forEach(activity => {
            if (activity.target_user) {
                const user = activity.target_user;
                if (!outgoingInteractions[user]) {
                    outgoingInteractions[user] = { username: user, count: 0, types: [] };
                }
                outgoingInteractions[user].count++;
                if (!outgoingInteractions[user].types.includes(activity.type)) {
                    outgoingInteractions[user].types.push(activity.type);
                }
            }
        });

        const topOutgoing = Object.values(outgoingInteractions)
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);

        this.state.set('topInteractions.outgoing', topOutgoing);

        // Renderizar widget
        this.renderTopInteractionsWidget(topOutgoing, 'outgoing');
    }

    /**
     * Renderiza o widget de Top Interatores (Afinidade)
     * @param {Array} ranking - Ranking de afinidade vindo do backend
     * @param {string} type - Tipo (outgoing/incoming)
     */
    renderTopInteractionsWidget(ranking, type) {
        const container = document.getElementById('quick-top-interactions');
        const mainContainer = document.getElementById('affinity-widget');
        
        if (!ranking || ranking.length === 0) return;

        const html = `
            <div class="affinity-list">
                ${ranking.slice(0, 5).map((user, index) => `
                    <div class="affinity-item premium-item" style="--delay: ${index * 0.1}s">
                        <div class="affinity-rank">#${index + 1}</div>
                        <div class="affinity-info">
                            <span class="affinity-username">@${user.username}</span>
                            <div class="affinity-stats">
                                <span title="Likes"><i class="fas fa-heart"></i> ${user.likes}</span>
                                <span title="Comentários"><i class="fas fa-comment"></i> ${user.comments}</span>
                                <span title="Menções"><i class="fas fa-at"></i> ${user.mentions}</span>
                            </div>
                        </div>
                        <div class="affinity-score">
                            <div class="score-value">${user.score}</div>
                            <div class="score-label">pts</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        if (container) container.innerHTML = html;
        if (mainContainer) mainContainer.innerHTML = `
            <div class="widget affinity-widget-full">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-project-diagram"></i> Análise de Afinidade de Rede
                    </h3>
                </div>
                ${html}
            </div>
        `;
    }

    // ==========================================================================
    // MÉTODOS DE RENDERIZAÇÃO
    // ==========================================================================

    /**
     * Renderiza card de perfil
     * @param {Object} profile - Dados do perfil
     */
    renderProfileCard(profile) {
        const container = document.getElementById('profile-card');
        if (!container) return;

        container.innerHTML = `
            <div class="widget profile-widget">
                <div class="profile-header">
                    <img src="${profile.profile_pic_url || '/static/img/default-avatar.png'}" 
                         alt="${profile.username}" 
                         class="profile-avatar">
                    <div class="profile-info">
                        <h2 class="profile-name">
                            ${this.escapeHtml(profile.full_name || profile.username)}
                            ${profile.is_verified ? '<i class="fas fa-check-circle verified-badge"></i>' : ''}
                        </h2>
                        <span class="profile-username">@${profile.username}</span>
                    </div>
                </div>
                
                <div class="profile-stats">
                    <div class="stat-item">
                        <span class="stat-number">${this.formatNumber(profile.followers_count)}</span>
                        <span class="stat-label">Seguidores</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${this.formatNumber(profile.following_count)}</span>
                        <span class="stat-label">Seguindo</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${this.formatNumber(profile.media_count)}</span>
                        <span class="stat-label">Posts</span>
                    </div>
                </div>
                
                ${profile.biography ? `
                    <div class="profile-bio">
                        <p>${this.escapeHtml(profile.biography)}</p>
                    </div>
                ` : ''}
                
                <div class="profile-actions">
                    <button class="btn btn-primary" onclick="dashboard.loadAIAnalysis('${profile.username}')">
                        <i class="fas fa-brain"></i> Analisar com IA
                    </button>
                    <button class="btn btn-secondary" onclick="dashboard.startTracking({username: '${profile.username}'})">
                        <i class="fas fa-search"></i> Rastrear Atividades
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza lista de atividades
     * @param {Array} activities - Lista de atividades
     */
    renderActivities(activities) {
        const container = document.getElementById('activities-list');
        if (!container) return;

        if (!activities || activities.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>Nenhuma atividade encontrada</p>
                </div>
            `;
            return;
        }

        const html = activities.map(activity => this.renderActivityCard(activity)).join('');
        container.innerHTML = html;
    }

    /**
     * Renderiza card de atividade individual
     * @param {Object} activity - Dados da atividade
     * @returns {string} HTML
     */
    renderActivityCard(activity) {
        const typeConfig = {
            'outgoing_like': { icon: 'fa-heart', color: 'like', label: 'Curtiu' },
            'outgoing_comment': { icon: 'fa-comment', color: 'comment', label: 'Comentou' },
            'mention_received': { icon: 'fa-at', color: 'mention', label: 'Mencionou' }
        };

        const config = typeConfig[activity.type] || { icon: 'fa-circle', color: '', label: 'Atividade' };
        const timestamp = activity.comment_timestamp || activity.post_timestamp || activity.timestamp;
        const postUrl = activity.comment_url || activity.post_url;

        return `
            <div class="activity-card ${config.color} premium-card">
                <div class="activity-card__body">
                    <div class="activity-header">
                        <div class="activity-type">
                            <i class="fas ${config.icon}"></i>
                            <span>${config.label}</span>
                        </div>
                        <div class="activity-date" title="${new Date(timestamp).toLocaleString('pt-BR')}">
                            <i class="far fa-clock"></i>
                            ${this.formatDate ? this.formatDate(timestamp) : new Date(timestamp).toLocaleDateString()}
                        </div>
                    </div>
                    
                    <div class="activity-content">
                        ${activity.target_user ? `
                            <div class="activity-target">
                                <i class="fas fa-user"></i>
                                <a href="https://instagram.com/${activity.target_user}" target="_blank">
                                    @${activity.target_user}
                                </a>
                            </div>
                        ` : ''}
                        
                        ${activity.comment_text ? `
                            <div class="activity-text">
                                <i class="fas fa-quote-left"></i>
                                <span>"${this.escapeHtml(activity.comment_text)}"</span>
                            </div>
                        ` : ''}
                        
                        <div class="activity-actions">
                            ${postUrl ? `
                                <a href="${postUrl}" target="_blank" class="btn-link">
                                    <i class="fas fa-external-link-alt"></i> 
                                    ${activity.comment_url ? 'Ver Comentário' : 'Ver Post'}
                                </a>
                            ` : ''}
                        </div>
                    </div>
                </div>
                
                ${activity.thumbnail_url ? `
                    <div class="activity-preview">
                        <img src="${activity.thumbnail_url}" alt="Preview" loading="lazy">
                        ${activity.media_type === 'video' ? '<div class="play-overlay"><i class="fas fa-play"></i></div>' : ''}
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Renderiza estatísticas de atividades
     * @param {Object} stats - Estatísticas
     */
    renderActivityStats(stats) {
        const container = document.getElementById('activity-stats');
        if (!container) return;

        container.innerHTML = `
            <div class="results-stats">
                <div class="stat-card">
                    <div class="stat-number">${stats.outgoing_likes || 0}</div>
                    <div class="stat-label">Curtidas</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.outgoing_comments || 0}</div>
                    <div class="stat-label">Comentários</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.mentions || 0}</div>
                    <div class="stat-label">Menções</div>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza widget de sentimento
     * @param {Object} data - Dados de sentimento
     */
    renderSentimentWidget(data) {
        const container = document.getElementById('sentiment-widget');
        if (!container) return;

        const score = data.overall_sentiment?.compound || 0;
        const percentage = ((score + 1) / 2) * 100;
        const label = score > 0.05 ? 'Positivo' : score < -0.05 ? 'Negativo' : 'Neutro';
        const colorClass = score > 0.05 ? 'positive' : score < -0.05 ? 'negative' : 'neutral';

        container.innerHTML = `
            <div class="widget sentiment-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-smile"></i> Análise de Sentimento
                    </h3>
                </div>
                
                <div class="sentiment-gauge">
                    <div class="gauge-circle">
                        <svg viewBox="0 0 100 100">
                            <circle class="gauge-background" cx="50" cy="50" r="40"></circle>
                            <circle class="gauge-fill ${colorClass}" cx="50" cy="50" r="40"
                                    stroke-dasharray="251.2"
                                    stroke-dashoffset="${251.2 - (251.2 * percentage / 100)}">
                            </circle>
                        </svg>
                        <div class="gauge-value">
                            <div class="gauge-score">${(score * 100).toFixed(0)}%</div>
                            <div class="gauge-label">${label}</div>
                        </div>
                    </div>
                </div>
                
                ${data.nuances?.length ? `
                    <div class="nuances-list">
                        ${data.nuances.map(n => `
                            <span class="nuance-tag ${n.toLowerCase()}">${n}</span>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Renderiza widget preditivo
     * @param {Object} data - Dados preditivos
     */
    renderPredictiveWidget(data) {
        const container = document.getElementById('predictive-widget');
        if (!container) return;

        const score = data.previsibilidade_score || 0;

        container.innerHTML = `
            <div class="widget predictive-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-chart-line"></i> Previsibilidade
                    </h3>
                </div>
                
                <div class="predictive-score">
                    <div class="score-display">
                        <div class="score-number">${score}</div>
                        <div class="score-label">Score</div>
                    </div>
                    
                    <div class="heatmap-container">
                        <div class="heatmap-title">Padrão de Atividade Semanal</div>
                        <div class="heatmap-grid" id="activity-heatmap"></div>
                    </div>
                </div>
            </div>
        `;

        // Renderizar heatmap se houver dados
        if (data.heatmap_data) {
            this.renderHeatmap(data.heatmap_data);
        }
    }

    /**
     * Renderiza heatmap de atividade
     * @param {Array} heatmapData - Dados do heatmap
     */
    renderHeatmap(heatmapData) {
        const container = document.getElementById('activity-heatmap');
        if (!container) return;

        const days = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];

        let html = '<div></div>'; // Célula vazia para canto

        // Headers de hora (0-23)
        for (let h = 0; h < 24; h++) {
            if (h % 3 === 0) {
                html += `<div class="heatmap-hour-label">${h}</div>`;
            } else {
                html += '<div></div>';
            }
        }

        // Linhas por dia
        days.forEach((day, dayIndex) => {
            html += `<div class="heatmap-day-label">${day}</div>`;

            for (let hour = 0; hour < 24; hour++) {
                const value = heatmapData?.[dayIndex]?.[hour] || 0;
                const level = Math.min(4, Math.floor(value / 25));
                html += `<div class="heatmap-cell level-${level}" title="${day} ${hour}h: ${value}%"></div>`;
            }
        });

        container.innerHTML = html;
    }

    /**
     * Renderiza widget de visão computacional
     * @param {Object} data - Dados de análise visual
     */
    renderVisionWidget(data) {
        const container = document.getElementById('vision-widget');
        if (!container) return;

        const categories = data.categories || [];

        container.innerHTML = `
            <div class="widget vision-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-eye"></i> Análise Visual
                    </h3>
                </div>
                
                <div class="vision-content">
                    <div class="vision-chart" id="vision-chart">
                        <!-- Chart será renderizado aqui -->
                    </div>
                    
                    <div class="vision-categories">
                        ${categories.slice(0, 8).map((cat, i) => `
                            <div class="category-item">
                                <div class="category-color" style="background: ${this.getColorForIndex(i)}"></div>
                                <span class="category-name">${cat.name}</span>
                                <span class="category-count">${cat.count}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                ${data.tags?.length ? `
                    <div class="tags-cloud">
                        ${data.tags.map(tag => `
                            <span class="tag-item size-${tag.size || 'md'}">${tag.name}</span>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }


    // ==========================================================================
    // UTILITÁRIOS
    // ==========================================================================

    /**
     * Escapa HTML para prevenir XSS
     * @param {string} text - Texto
     * @returns {string} Texto escapado
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Formata número (ex: 1234 -> 1.2K)
     * @param {number} num - Número
     * @returns {string} Número formatado
     */
    formatNumber(num) {
        if (!num) return '0';
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    /**
     * Formata data
     * @param {string|Date} date - Data
     * @returns {string} Data formatada
     */
    formatDate(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Obtém cor para índice
     * @param {number} index - Índice
     * @returns {string} Cor
     */
    getColorForIndex(index) {
        const colors = [
            '#667eea', '#764ba2', '#28a745', '#ffc107',
            '#e91e63', '#2196f3', '#ff9800', '#9c27b0'
        ];
        return colors[index % colors.length];
    }
}

// Singleton global
let dashboard = null;

/**
 * Obtém instância do Dashboard
 * @param {HTMLElement} container - Container
 * @returns {Dashboard}
 */
export function getDashboard(container) {
    if (!dashboard) {
        dashboard = new Dashboard(container);
    }
    return dashboard;
}

// Expor globalmente para uso em HTML
window.dashboard = null;

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = getDashboard();
    window.dashboard.init();
});

export default Dashboard;
