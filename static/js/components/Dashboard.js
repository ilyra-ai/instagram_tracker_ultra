/**
 * Dashboard.js - Componente Principal do Dashboard (Lyra Ultra)
 * 
 * Versão otimizada para integração com o novo layout Bento Grid e TabsManager.
 * 
 * @module Dashboard
 * @version 2.1.0
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
import { createBreachCheckWidget } from './BreachCheckWidget.js';
import { createCalendarView } from './CalendarView.js';
import { createTopInteractionsWidget } from './TopInteractionsWidget.js';

export class Dashboard {
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
        this.responsiveLayout = getResponsiveLayout();

        // Componentes e Widgets
        this.widgets = new Map();
        
        // Progress Tracker
        this.progressTracker = new IntelligenceProgress('intelligence-progress-container');

        // UI Helpers
        this.tabsManager = null;
        this.searchComponent = null;

        // Bind methods
        this.init = this.init.bind(this);
        this.handleSearch = this.handleSearch.bind(this);
    }

    async init() {
        console.log('[Lyra Dashboard] Inicializando v2.1...');

        this.loadingStates.showProgress('Inicializando...');

        // 1. Verificar Status do Sistema
        await this.checkSystemStatus();

        // 2. Inicializar Gerenciador de Abas
        const tabsContainer = document.getElementById('tabs-container');
        const contentContainer = document.getElementById('main-content');
        if (tabsContainer) {
            this.tabsManager = getTabsManager({
                container: tabsContainer,
                contentContainer: contentContainer,
                defaultTab: 'overview'
            });
            this.tabsManager.init();
            this.tabsManager.onChange((tabId) => this.handleTabChange(tabId));
        }

        // 3. Inicializar Busca Avançada
        const searchContainer = document.getElementById('search-container');
        if (searchContainer) {
            this.searchComponent = createSearchAdvanced(searchContainer);
            searchContainer.addEventListener('search', (e) => this.handleSearch(e.detail));
        }

        // 4. Configurar Event Listeners Globais
        this.setupEventListeners();

        // 5. Inicializar Widgets
        await this.initializeWidgets();

        // 6. Restaurar estado anterior
        this.state.restore();
        const lastUser = this.state.get('currentUser');
        if (lastUser) {
            this.loadUserData(lastUser);
        }

        this.loadingStates.hideProgress();
        console.log('[Lyra Dashboard] Pronto.');
    }

    async checkSystemStatus() {
        try {
            const status = await this.api.getStatus();
            this.state.set('system.status', 'online');
            this.updateStatusIndicator('online');
        } catch (error) {
            this.state.set('system.status', 'offline');
            this.updateStatusIndicator('offline');
            this.notifications.error('API Indisponível');
        }
    }

    updateStatusIndicator(status) {
        const dot = document.querySelector('.status-indicator__dot');
        const text = document.getElementById('current-status');
        if (dot) {
            dot.className = `status-indicator__dot inline-block w-2.5 h-2.5 rounded-full ${status === 'online' ? 'bg-green-500' : 'bg-red-500'}`;
        }
        if (text) {
            text.textContent = status === 'online' ? 'Sistema Online' : 'Sistema Offline';
        }
    }

    async initializeWidgets() {
        console.log('[Dashboard] Inicializando widgets Bento...');

        const containers = {
            profile: document.getElementById('profile-card'),
            activityFeed: document.getElementById('activities-list'),
            sentiment: document.getElementById('sentiment-widget'),
            predictive: document.getElementById('predictive-widget'),
            vision: document.getElementById('vision-widget'),
            graph: document.getElementById('network-graph'),
            geoHeatmap: document.getElementById('location-map'),
            engagement: document.getElementById('engagement-chart'),
            calendar: document.getElementById('calendar-view'),
            quickAffinity: document.getElementById('quick-top-interactions'),
            osint: document.getElementById('platform-results'),
            breach: document.getElementById('breach-results')
        };

        if (containers.profile) this.widgets.set('profile', createProfileCard(containers.profile));
        if (containers.activityFeed) this.widgets.set('activityFeed', createActivityFeed(containers.activityFeed));
        if (containers.sentiment) this.widgets.set('sentiment', createSentimentWidget(containers.sentiment));
        if (containers.predictive) this.widgets.set('predictive', createPredictiveWidget(containers.predictive));
        if (containers.vision) this.widgets.set('vision', createVisionWidget(containers.vision));
        if (containers.graph) this.widgets.set('graph', createGraphVisualizer(containers.graph));
        if (containers.geoHeatmap) this.widgets.set('geoHeatmap', createGeoHeatmap(containers.geoHeatmap));
        if (containers.engagement) this.widgets.set('engagement', createEngagementChart(containers.engagement));
        if (containers.calendar) this.widgets.set('calendar', createCalendarView(containers.calendar));
        if (containers.osint) this.widgets.set('osint', createOSINTToolbar(containers.osint));
        if (containers.breach) this.widgets.set('breach', createBreachCheckWidget(containers.breach));

        // Quick Affinity no dashboard
        if (containers.quickAffinity) {
            this.widgets.set('quickAffinity', createTopInteractionsWidget(containers.quickAffinity, { type: 'outgoing', limit: 3 }));
        }
    }

    setupEventListeners() {
        // Sidebar Mobile
        const mobileBtn = document.getElementById('mobile-menu-btn');
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.sidebar-overlay');

        if (mobileBtn && sidebar) {
            mobileBtn.addEventListener('click', () => {
                sidebar.classList.toggle('-translate-x-full');
                overlay.classList.toggle('hidden');
            });
        }

        if (overlay) {
            overlay.addEventListener('click', () => {
                sidebar.classList.add('-translate-x-full');
                overlay.classList.add('hidden');
            });
        }

        // Sidebar Links Integration with Tabs
        document.querySelectorAll('.sidebar__link[data-tab]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tabId = link.dataset.tab;
                if (this.tabsManager) {
                    this.tabsManager.setActiveTab(tabId);
                }

                // Fechar mobile
                if (window.innerWidth < 768) {
                    sidebar.classList.add('-translate-x-full');
                    overlay.classList.add('hidden');
                }

                // Active class sidebar
                document.querySelectorAll('.sidebar__link').forEach(l => {
                    l.classList.remove('bg-teal-50/50', 'text-teal-700', 'font-medium');
                    l.classList.add('text-gray-500');
                });
                link.classList.add('bg-teal-50/50', 'text-teal-700', 'font-medium');
                link.classList.remove('text-gray-500');
            });
        });

        // Form de Tracking
        const trackingForm = document.getElementById('tracking-form');
        if (trackingForm) {
            trackingForm.addEventListener('submit', (e) => this.handleTrackingSubmit(e));
        }

        const mainTrackBtn = document.getElementById('btn-toggle-tracking');
        if (mainTrackBtn) {
            mainTrackBtn.addEventListener('click', () => {
               const currentUser = this.state.get('currentUser');
               if (currentUser) {
                   this.startTracking({ username: currentUser });
               } else {
                   this.notifications.warning('Busque um usuário primeiro.');
               }
            });
        }
    }

    handleTabChange(tabId) {
        console.log('[Dashboard] Mudou para:', tabId);
        this.state.set('ui.activeTab', tabId);

        const user = this.state.get('currentUser');
        if (!user) return;

        // Gatilhos específicos por tab
        if (tabId === 'intelligence') this.loadAIAnalysis(user);
        if (tabId === 'network') this.loadNetworkData(user);
    }

    async handleSearch(data) {
        const username = typeof data === 'string' ? data : data.username;
        if (!username) return;

        const cleanUser = username.replace('@', '').trim();
        this.state.set('currentUser', cleanUser);
        await this.loadUserData(cleanUser);
    }

    async loadUserData(username) {
        this.loadingStates.showProgress(`Carregando @${username}...`);

        try {
            const profile = await this.api.getUserInfo(username);
            if (profile.success) {
                this.state.set('profile', profile.user_info);
                this.updateProfileWidgets(profile.user_info);
            }
        } catch (err) {
            this.notifications.error('Erro ao carregar perfil');
        } finally {
            this.loadingStates.hideProgress();
        }
    }

    updateProfileWidgets(info) {
        const profileWidget = this.widgets.get('profile');
        if (profileWidget && typeof profileWidget.setData === 'function') {
            profileWidget.setData(info);
        }

        // Atualizar contadores rápidos
        const setStat = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        };

        setStat('stat-likes', this.formatNumber(info.total_likes || 0));
        setStat('stat-comments', this.formatNumber(info.total_comments || 0));
        setStat('stat-mentions', this.formatNumber(info.total_mentions || 0));
    }

    async handleTrackingSubmit(e) {
        e.preventDefault();
        const username = e.target.username.value.trim();
        if (username) await this.startTracking({ username });
    }

    async startTracking(options) {
        this.progressTracker.show();
        this.progressTracker.update(10, 'Iniciando...', 'Conectando ao Instagram...');

        try {
            const result = await this.api.trackActivities(options.username);
            if (result.success) {
                this.progressTracker.update(100, 'Concluído', 'Dados processados.');
                this.state.set('activities', result.activities);
                this.updateActivityWidgets(result);
                this.notifications.success('Rastreamento concluído!');
                
                // Mudar para tab de atividades para mostrar os resultados
                if (this.tabsManager) this.tabsManager.setActiveTab('activities');
            }
        } catch (err) {
            this.notifications.error('Falha no rastreamento');
            this.progressTracker.hide();
        }
    }

    updateActivityWidgets(data) {
        const feed = this.widgets.get('activityFeed');
        if (feed && typeof feed.setData === 'function') {
            feed.setData(data.activities);
        }
        
        const affinity = this.widgets.get('quickAffinity');
        if (affinity && typeof affinity.setData === 'function' && data.affinity_ranking) {
            affinity.setData(data.affinity_ranking);
        }
    }

    async loadAIAnalysis(username) {
        const sentiment = this.widgets.get('sentiment');
        if (sentiment) {
            sentiment.setLoading(true);
            const res = await this.api.analyzeSentiment(username);
            sentiment.setData(res);
            sentiment.setLoading(false);
        }
    }

    async loadNetworkData(username) {
        const graph = this.widgets.get('graph');
        if (graph) {
            const res = await this.api.getNetworkGraph(username);
            graph.setData(res.graph);
        }
    }

    formatNumber(n) {
        if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
        if (n >= 1000) return (n/1000).toFixed(1) + 'K';
        return n;
    }
}

// Inicialização automática
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new Dashboard();
    dashboard.init();
    window.dashboard = dashboard;
});

export default Dashboard;
