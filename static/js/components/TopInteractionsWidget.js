/**
 * TopInteractionsWidget.js - Widget de Top Interações
 * 
 * Exibe as pessoas que mais interagem com/do perfil rastreado:
 * - Top 5 quem mais interage COM o rastreado
 * - Top 5 quem o rastreado mais interage
 * - Cards com foto, nome e contagem
 * - Gráfico de barras comparativo
 * - Indicador de reciprocidade
 * 
 * @module TopInteractionsWidget
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class TopInteractionsWidget {
    /**
     * Cria uma instância do TopInteractionsWidget
     * @param {HTMLElement} container - Container do widget
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Dados de interações
        this.interactionsData = null;

        // Estado de carregamento
        this.isLoading = false;

        // Visualização ativa
        this.activeView = 'incoming'; // 'incoming' | 'outgoing' | 'mutual'

        // Bind methods
        this.render = this.render.bind(this);
        this.loadInteractions = this.loadInteractions.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças nos dados
        this.state.subscribe('topInteractions', (data) => {
            if (data) {
                this.interactionsData = data;
                this.render();
            }
        });

        // Render inicial
        this.render();
    }

    /**
     * Carrega dados de interações
     */
    async loadInteractions() {
        const username = this.state.get('currentUser');

        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        this.isLoading = true;
        this.render();

        const loading = this.notifications.loading('Analisando interações...');

        try {
            const result = await this.api.getTopInteractions(username);

            if (result.success) {
                this.interactionsData = result;
                this.state.set('topInteractions', result);
                loading.success('Análise de interações concluída!');
            } else {
                loading.error(result.error || 'Erro ao analisar interações');
            }
        } catch (error) {
            loading.error(`Erro: ${error.message}`);
        } finally {
            this.isLoading = false;
            this.render();
        }
    }

    /**
     * Renderiza o widget
     */
    render() {
        if (!this.container) return;

        if (!this.interactionsData) {
            this.container.innerHTML = this.renderEmptyState();
            this.attachEventListeners();
            return;
        }

        this.container.innerHTML = this.renderWidget();
        this.attachEventListeners();
    }

    /**
     * Renderiza estado vazio
     * @returns {string} HTML
     */
    renderEmptyState() {
        return `
            <div class="widget top-interactions-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-users"></i> Top Interações
                    </h3>
                </div>
                
                <div class="widget__empty ${this.isLoading ? 'widget__empty--loading' : ''}">
                    ${this.isLoading ? `
                        <div class="loading-animation">
                            <div class="loading-spinner"></div>
                            <p>Analisando interações...</p>
                        </div>
                    ` : `
                        <div class="empty-icon">
                            <i class="fas fa-users"></i>
                        </div>
                        <p>Clique para analisar as principais interações</p>
                        <button class="btn btn-primary" id="btn-load-interactions">
                            <i class="fas fa-chart-bar"></i>
                            Analisar Interações
                        </button>
                    `}
                </div>
            </div>
        `;
    }

    /**
     * Renderiza widget com dados
     * @returns {string} HTML
     */
    renderWidget() {
        const data = this.interactionsData;
        const incoming = data.incoming_top || [];
        const outgoing = data.outgoing_top || [];
        const mutual = data.mutual || [];

        return `
            <div class="widget top-interactions-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-users"></i> Top Interações
                    </h3>
                    <div class="widget__actions">
                        <button class="widget__action-btn" id="btn-refresh-interactions" title="Atualizar">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Navegação de Tabs -->
                <div class="interactions-tabs">
                    <button class="tab-btn ${this.activeView === 'incoming' ? 'active' : ''}" 
                            data-view="incoming">
                        <i class="fas fa-arrow-down"></i>
                        Recebidas
                        <span class="count">${incoming.length}</span>
                    </button>
                    <button class="tab-btn ${this.activeView === 'outgoing' ? 'active' : ''}" 
                            data-view="outgoing">
                        <i class="fas fa-arrow-up"></i>
                        Enviadas
                        <span class="count">${outgoing.length}</span>
                    </button>
                    <button class="tab-btn ${this.activeView === 'mutual' ? 'active' : ''}" 
                            data-view="mutual">
                        <i class="fas fa-exchange-alt"></i>
                        Mútuas
                        <span class="count">${mutual.length}</span>
                    </button>
                </div>
                
                <!-- Conteúdo da Tab Ativa -->
                <div class="interactions-content">
                    ${this.renderActiveView()}
                </div>
                
                <!-- Resumo de Estatísticas -->
                <div class="interactions-summary">
                    <div class="summary-stat">
                        <span class="stat-value">${data.total_incoming || 0}</span>
                        <span class="stat-label">Interações Recebidas</span>
                    </div>
                    <div class="summary-stat">
                        <span class="stat-value">${data.total_outgoing || 0}</span>
                        <span class="stat-label">Interações Enviadas</span>
                    </div>
                    <div class="summary-stat">
                        <span class="stat-value">${mutual.length}</span>
                        <span class="stat-label">Conexões Mútuas</span>
                    </div>
                </div>
                
                <!-- Gráfico de Comparação -->
                <div class="interactions-chart">
                    <h4><i class="fas fa-chart-bar"></i> Comparação Visual</h4>
                    <div class="chart-container" id="interactions-chart-container">
                        ${this.renderComparisonChart()}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza visualização ativa
     * @returns {string} HTML
     */
    renderActiveView() {
        const data = this.interactionsData;

        switch (this.activeView) {
            case 'incoming':
                return this.renderUserList(data.incoming_top || [], 'incoming');
            case 'outgoing':
                return this.renderUserList(data.outgoing_top || [], 'outgoing');
            case 'mutual':
                return this.renderUserList(data.mutual || [], 'mutual');
            default:
                return this.renderUserList(data.incoming_top || [], 'incoming');
        }
    }

    /**
     * Renderiza lista de usuários
     * @param {Array} users - Lista de usuários
     * @param {string} type - Tipo de interação
     * @returns {string} HTML
     */
    renderUserList(users, type) {
        if (users.length === 0) {
            return `
                <div class="no-users">
                    <i class="fas fa-user-slash"></i>
                    <p>Nenhuma interação encontrada</p>
                </div>
            `;
        }

        const maxCount = Math.max(...users.map(u => u.count || 0));

        return `
            <div class="users-list">
                ${users.slice(0, 10).map((user, index) => this.renderUserCard(user, index, type, maxCount)).join('')}
            </div>
        `;
    }

    /**
     * Renderiza card de usuário
     * @param {Object} user - Dados do usuário
     * @param {number} index - Índice
     * @param {string} type - Tipo
     * @param {number} maxCount - Count máximo para barras
     * @returns {string} HTML
     */
    renderUserCard(user, index, type, maxCount) {
        const percentage = maxCount > 0 ? (user.count / maxCount) * 100 : 0;
        const isMutual = user.is_mutual || type === 'mutual';

        return `
            <div class="user-card">
                <div class="user-rank">${index + 1}</div>
                
                <div class="user-avatar">
                    ${user.profile_pic ? `
                        <img src="${this.escapeHtml(user.profile_pic)}" alt="${this.escapeHtml(user.username)}"
                             onerror="this.parentElement.innerHTML='<i class=\\'fas fa-user\\'></i>'">
                    ` : '<i class="fas fa-user"></i>'}
                    ${isMutual ? `
                        <span class="mutual-badge" title="Interação Mútua">
                            <i class="fas fa-exchange-alt"></i>
                        </span>
                    ` : ''}
                </div>
                
                <div class="user-info">
                    <span class="user-name">${this.escapeHtml(user.full_name || user.username)}</span>
                    <span class="user-username">@${this.escapeHtml(user.username)}</span>
                </div>
                
                <div class="user-stats">
                    <div class="stat-bar">
                        <div class="stat-bar-fill" style="width: ${percentage}%"></div>
                    </div>
                    <div class="stat-details">
                        <span class="interaction-count">${this.formatNumber(user.count)}</span>
                        <span class="interaction-breakdown">
                            ${user.likes ? `<span><i class="fas fa-heart"></i> ${user.likes}</span>` : ''}
                            ${user.comments ? `<span><i class="fas fa-comment"></i> ${user.comments}</span>` : ''}
                        </span>
                    </div>
                </div>
                
                <a href="https://instagram.com/${this.escapeHtml(user.username)}" 
                   target="_blank" 
                   class="user-link"
                   title="Abrir perfil no Instagram">
                    <i class="fab fa-instagram"></i>
                </a>
            </div>
        `;
    }

    /**
     * Renderiza gráfico de comparação
     * @returns {string} HTML
     */
    renderComparisonChart() {
        const data = this.interactionsData;
        const incoming = data.incoming_top || [];
        const outgoing = data.outgoing_top || [];

        // Pegar top 5 de cada
        const topIncoming = incoming.slice(0, 5);
        const topOutgoing = outgoing.slice(0, 5);

        // Calcular max para escala
        const allCounts = [...topIncoming.map(u => u.count || 0), ...topOutgoing.map(u => u.count || 0)];
        const maxCount = Math.max(...allCounts, 1);

        return `
            <div class="comparison-chart">
                <div class="chart-section chart-incoming">
                    <h5>Top 5 - Quem Mais Interage</h5>
                    <div class="bars">
                        ${topIncoming.map(user => `
                            <div class="bar-row">
                                <span class="bar-label">${this.truncate(user.username, 12)}</span>
                                <div class="bar-container">
                                    <div class="bar bar--incoming" style="width: ${(user.count / maxCount) * 100}%"></div>
                                </div>
                                <span class="bar-value">${user.count}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="chart-section chart-outgoing">
                    <h5>Top 5 - Mais Interagido Pelo Perfil</h5>
                    <div class="bars">
                        ${topOutgoing.map(user => `
                            <div class="bar-row">
                                <span class="bar-label">${this.truncate(user.username, 12)}</span>
                                <div class="bar-container">
                                    <div class="bar bar--outgoing" style="width: ${(user.count / maxCount) * 100}%"></div>
                                </div>
                                <span class="bar-value">${user.count}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Define visualização ativa
     * @param {string} view - Visualização
     */
    setActiveView(view) {
        this.activeView = view;
        this.render();
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Botão carregar
        const btnLoad = this.container.querySelector('#btn-load-interactions');
        if (btnLoad) {
            btnLoad.addEventListener('click', () => this.loadInteractions());
        }

        // Botão refresh
        const btnRefresh = this.container.querySelector('#btn-refresh-interactions');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.loadInteractions());
        }

        // Tabs
        const tabBtns = this.container.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.setActiveView(btn.dataset.view);
            });
        });
    }

    // ==========================================================================
    // UTILITÁRIOS
    // ==========================================================================

    /**
     * Formata número
     * @param {number} num - Número
     * @returns {string}
     */
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    /**
     * Trunca texto
     * @param {string} text - Texto
     * @param {number} maxLength - Tamanho máximo
     * @returns {string}
     */
    truncate(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

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
}

// Factory function
export function createTopInteractionsWidget(container) {
    const widget = new TopInteractionsWidget(container);
    widget.init();
    return widget;
}

export default TopInteractionsWidget;
