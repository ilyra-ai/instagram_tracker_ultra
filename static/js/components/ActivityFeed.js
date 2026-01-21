/**
 * ActivityFeed.js - Componente de Feed de Atividades
 * 
 * Exibe lista de atividades rastreadas:
 * - Timeline scrollável
 * - Filtros por tipo (curtidas, comentários, menções)
 * - Cards detalhados de cada atividade
 * - Paginação e infinite scroll
 * - Estatísticas agregadas
 * 
 * @module ActivityFeed
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class ActivityFeed {
    /**
     * Cria uma instância do ActivityFeed
     * @param {HTMLElement} container - Container do feed
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Dados
        this.activities = [];
        this.filteredActivities = [];
        this.currentFilter = 'all';

        // Paginação
        this.page = 1;
        this.pageSize = 20;
        this.hasMore = true;
        this.isLoading = false;

        // Bind methods
        this.render = this.render.bind(this);
        this.filterActivities = this.filterActivities.bind(this);
        this.loadMore = this.loadMore.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças nas atividades
        this.state.subscribe('activities', (activities) => {
            this.activities = activities || [];
            this.applyFilter();
            this.render();
        });

        // Render inicial
        this.render();

        // Configurar infinite scroll
        this.setupInfiniteScroll();
    }

    /**
     * Configura infinite scroll
     */
    setupInfiniteScroll() {
        if (!this.container) return;

        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting && this.hasMore && !this.isLoading) {
                this.loadMore();
            }
        }, { threshold: 0.1 });

        // Observar elemento sentinel
        const createSentinel = () => {
            const sentinel = document.createElement('div');
            sentinel.id = 'activity-sentinel';
            sentinel.style.height = '1px';
            return sentinel;
        };

        // Adicionar sentinel após render
        setTimeout(() => {
            const list = this.container.querySelector('.activities-list');
            if (list) {
                const sentinel = list.querySelector('#activity-sentinel') || createSentinel();
                list.appendChild(sentinel);
                observer.observe(sentinel);
            }
        }, 100);
    }

    /**
     * Aplica filtro nas atividades
     */
    applyFilter() {
        if (this.currentFilter === 'all') {
            this.filteredActivities = [...this.activities];
        } else {
            const filterMap = {
                'like': ['outgoing_like'],
                'comment': ['outgoing_comment'],
                'mention': ['mention']
            };

            const types = filterMap[this.currentFilter] || [];
            this.filteredActivities = this.activities.filter(a => types.includes(a.type));
        }

        this.hasMore = this.filteredActivities.length > this.page * this.pageSize;
    }

    /**
     * Filtra atividades por tipo
     * @param {string} filter - Tipo de filtro
     */
    filterActivities(filter) {
        this.currentFilter = filter;
        this.page = 1;
        this.applyFilter();
        this.render();

        // Atualizar botões de filtro
        this.updateFilterButtons();
    }

    /**
     * Atualiza botões de filtro ativos
     */
    updateFilterButtons() {
        const buttons = this.container.querySelectorAll('[data-filter]');
        buttons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === this.currentFilter);
        });
    }

    /**
     * Carrega mais atividades
     */
    loadMore() {
        if (!this.hasMore || this.isLoading) return;

        this.isLoading = true;
        this.page++;

        // Simular delay para UX
        setTimeout(() => {
            this.render();
            this.isLoading = false;
        }, 300);
    }

    /**
     * Renderiza o feed
     */
    render() {
        if (!this.container) return;

        const paginatedActivities = this.filteredActivities.slice(0, this.page * this.pageSize);

        this.container.innerHTML = `
            <!-- Estatísticas -->
            <div class="activity-stats-bar">
                ${this.renderStats()}
            </div>
            
            <!-- Filtros -->
            <div class="activity-filters">
                <button class="filter-btn ${this.currentFilter === 'all' ? 'active' : ''}" 
                        data-filter="all">
                    <i class="fas fa-list"></i>
                    <span>Todas</span>
                    <span class="filter-count">${this.activities.length}</span>
                </button>
                <button class="filter-btn ${this.currentFilter === 'like' ? 'active' : ''}" 
                        data-filter="like">
                    <i class="fas fa-heart"></i>
                    <span>Curtidas</span>
                    <span class="filter-count">${this.countByType('outgoing_like')}</span>
                </button>
                <button class="filter-btn ${this.currentFilter === 'comment' ? 'active' : ''}" 
                        data-filter="comment">
                    <i class="fas fa-comment"></i>
                    <span>Comentários</span>
                    <span class="filter-count">${this.countByType('outgoing_comment')}</span>
                </button>
                <button class="filter-btn ${this.currentFilter === 'mention' ? 'active' : ''}" 
                        data-filter="mention">
                    <i class="fas fa-at"></i>
                    <span>Menções</span>
                    <span class="filter-count">${this.countByType('mention')}</span>
                </button>
            </div>
            
            <!-- Lista de Atividades -->
            <div class="activities-list">
                ${paginatedActivities.length > 0
                ? paginatedActivities.map(a => this.renderActivityCard(a)).join('')
                : this.renderEmptyState()
            }
                
                ${this.hasMore ? `
                    <div class="load-more-container">
                        <button class="btn btn-secondary" id="btn-load-more">
                            <i class="fas fa-plus"></i> Carregar Mais
                        </button>
                    </div>
                ` : ''}
                
                <div id="activity-sentinel"></div>
            </div>
        `;

        this.attachEventListeners();
    }

    /**
     * Renderiza estatísticas
     * @returns {string} HTML
     */
    renderStats() {
        const counts = this.calculateStats();
        const uniqueUsers = this.getUniqueUsers();

        return `
            <div class="stat-pill">
                <i class="fas fa-heart"></i>
                <span>${counts.likes} curtidas</span>
            </div>
            <div class="stat-pill">
                <i class="fas fa-comment"></i>
                <span>${counts.comments} comentários</span>
            </div>
            <div class="stat-pill">
                <i class="fas fa-at"></i>
                <span>${counts.mentions} menções</span>
            </div>
            <div class="stat-pill stat-pill--highlight">
                <i class="fas fa-users"></i>
                <span>${uniqueUsers.length} usuários únicos</span>
            </div>
        `;
    }

    /**
     * Calcula estatísticas
     * @returns {Object}
     */
    calculateStats() {
        return {
            total: this.activities.length,
            likes: this.countByType('outgoing_like'),
            comments: this.countByType('outgoing_comment'),
            mentions: this.countByType('mention')
        };
    }

    /**
     * Conta atividades por tipo
     * @param {string} type - Tipo
     * @returns {number}
     */
    countByType(type) {
        return this.activities.filter(a => a.type === type).length;
    }

    /**
     * Obtém usuários únicos
     * @returns {string[]}
     */
    getUniqueUsers() {
        const users = new Set();
        this.activities.forEach(a => {
            if (a.target_user) users.add(a.target_user);
        });
        return Array.from(users);
    }

    /**
     * Renderiza card de atividade
     * @param {Object} activity - Dados da atividade
     * @returns {string} HTML
     */
    renderActivityCard(activity) {
        const config = this.getActivityConfig(activity.type);
        const timestamp = activity.comment_timestamp || activity.post_timestamp || activity.timestamp;
        const postUrl = activity.comment_url || activity.post_url;

        return `
            <div class="activity-card activity-card--${config.class}" data-id="${activity.id || ''}">
                <div class="activity-card__main">
                    <div class="activity-card__icon">
                        <i class="fas ${config.icon}"></i>
                    </div>
                    
                    <div class="activity-card__content">
                        <div class="activity-card__header">
                            <span class="activity-type-label">${config.label}</span>
                            <span class="activity-time" title="${new Date(timestamp).toLocaleString('pt-BR')}">
                                <i class="far fa-clock"></i>
                                ${this.formatTimeAgo(timestamp)}
                            </span>
                        </div>
                        
                        ${activity.target_user ? `
                            <div class="activity-target">
                                <span class="target-label">Para:</span>
                                <a href="https://instagram.com/${this.escapeHtml(activity.target_user)}" 
                                   target="_blank" 
                                   class="target-username">
                                    @${this.escapeHtml(activity.target_user)}
                                </a>
                            </div>
                        ` : ''}
                        
                        ${activity.comment_text ? `
                            <div class="activity-comment">
                                <i class="fas fa-quote-left"></i>
                                <span class="comment-text">"${this.escapeHtml(activity.comment_text)}"</span>
                            </div>
                        ` : ''}
                        
                        <div class="activity-actions">
                            ${postUrl ? `
                                <a href="${this.escapeHtml(postUrl)}" target="_blank" class="btn btn-small btn-premium">
                                    <i class="fas fa-external-link-alt"></i>
                                    ${activity.comment_url ? 'Ver Comentário' : 'Ver Post'}
                                </a>
                            ` : ''}
                            
                            ${activity.post_caption ? `
                                <button class="btn btn-small btn-outline btn-context" title="${this.escapeHtml(activity.post_caption)}">
                                    <i class="fas fa-info-circle"></i> Contexto
                                </button>
                            ` : ''}
                        </div>
                    </div>

                    ${activity.thumbnail_url ? `
                        <div class="activity-card__media">
                            <img src="${activity.thumbnail_url}" alt="Preview" loading="lazy" onerror="this.style.display='none'">
                            ${activity.media_type === 'video' ? '<div class="media-badge"><i class="fas fa-play"></i></div>' : ''}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Obtém configuração visual por tipo
     * @param {string} type - Tipo de atividade
     * @returns {Object}
     */
    getActivityConfig(type) {
        const configs = {
            'outgoing_like': {
                icon: 'fa-heart',
                label: 'Curtiu',
                class: 'like'
            },
            'outgoing_comment': {
                icon: 'fa-comment',
                label: 'Comentou',
                class: 'comment'
            },
            'mention': {
                icon: 'fa-at',
                label: 'Mencionou',
                class: 'mention'
            }
        };

        return configs[type] || {
            icon: 'fa-circle',
            label: 'Atividade',
            class: 'default'
        };
    }

    /**
     * Renderiza estado vazio
     * @returns {string} HTML
     */
    renderEmptyState() {
        return `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>Nenhuma atividade encontrada</h3>
                <p>Execute um rastreamento para ver as atividades deste perfil</p>
            </div>
        `;
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Filtros
        const filterBtns = this.container.querySelectorAll('[data-filter]');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.filterActivities(btn.dataset.filter);
            });
        });

        // Botão carregar mais
        const loadMoreBtn = this.container.querySelector('#btn-load-more');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => {
                this.loadMore();
            });
        }
    }

    // ==========================================================================
    // UTILITÁRIOS
    // ==========================================================================

    /**
     * Escapa HTML
     * @param {string} text - Texto
     * @returns {string}
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Formata tempo relativo
     * @param {string|Date} timestamp - Timestamp
     * @returns {string}
     */
    formatTimeAgo(timestamp) {
        if (!timestamp) return '';

        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);

        if (diffSec < 60) return 'agora';
        if (diffMin < 60) return `${diffMin}min atrás`;
        if (diffHour < 24) return `${diffHour}h atrás`;
        if (diffDay < 7) return `${diffDay}d atrás`;

        return date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short'
        });
    }

    /**
     * Obtém top interações (quem o usuário mais interagiu)
     * @param {number} limit - Limite
     * @returns {Array}
     */
    getTopInteractedUsers(limit = 5) {
        const userCounts = {};

        this.activities.forEach(activity => {
            if (activity.target_user) {
                const user = activity.target_user;
                if (!userCounts[user]) {
                    userCounts[user] = {
                        username: user,
                        count: 0,
                        likes: 0,
                        comments: 0
                    };
                }

                userCounts[user].count++;

                if (activity.type === 'outgoing_like') {
                    userCounts[user].likes++;
                } else if (activity.type === 'outgoing_comment') {
                    userCounts[user].comments++;
                }
            }
        });

        return Object.values(userCounts)
            .sort((a, b) => b.count - a.count)
            .slice(0, limit);
    }

    /**
     * Obtém atividades por dia da semana
     * @returns {Object}
     */
    getActivityByDayOfWeek() {
        const days = {
            0: { name: 'Domingo', count: 0 },
            1: { name: 'Segunda', count: 0 },
            2: { name: 'Terça', count: 0 },
            3: { name: 'Quarta', count: 0 },
            4: { name: 'Quinta', count: 0 },
            5: { name: 'Sexta', count: 0 },
            6: { name: 'Sábado', count: 0 }
        };

        this.activities.forEach(activity => {
            if (activity.timestamp) {
                const dayOfWeek = new Date(activity.timestamp).getDay();
                days[dayOfWeek].count++;
            }
        });

        return days;
    }

    /**
     * Obtém atividades por hora do dia
     * @returns {Object}
     */
    getActivityByHour() {
        const hours = {};

        for (let i = 0; i < 24; i++) {
            hours[i] = { hour: i, count: 0 };
        }

        this.activities.forEach(activity => {
            if (activity.timestamp) {
                const hour = new Date(activity.timestamp).getHours();
                hours[hour].count++;
            }
        });

        return hours;
    }

    /**
     * Exporta atividades para JSON
     * @returns {string}
     */
    exportToJSON() {
        return JSON.stringify({
            exportedAt: new Date().toISOString(),
            totalActivities: this.activities.length,
            stats: this.calculateStats(),
            topUsers: this.getTopInteractedUsers(10),
            activities: this.activities
        }, null, 2);
    }

    /**
     * Exporta atividades para CSV
     * @returns {string}
     */
    exportToCSV() {
        const headers = ['Tipo', 'Usuário Alvo', 'Texto do Comentário', 'Data', 'URL do Post', 'Tipo de Mídia'];

        const rows = this.activities.map(a => [
            a.type || '',
            a.target_user || '',
            (a.comment_text || '').replace(/"/g, '""'),
            a.timestamp || '',
            a.post_url || '',
            a.media_type || ''
        ]);

        return [headers, ...rows]
            .map(row => row.map(cell => `"${cell}"`).join(','))
            .join('\n');
    }
}

// Factory function
export function createActivityFeed(container) {
    const feed = new ActivityFeed(container);
    feed.init();
    return feed;
}

export default ActivityFeed;
