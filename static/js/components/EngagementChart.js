/**
 * EngagementChart.js - Gráficos de Engajamento com Chart.js
 * 
 * Exibe gráficos de engajamento com:
 * - Linha temporal de engajamento
 * - Barras de curtidas/comentários por post
 * - Pizza de distribuição de interações
 * - Comparativo entre períodos
 * - Taxa de engajamento ao longo do tempo
 * 
 * @module EngagementChart
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class EngagementChart {
    /**
     * Cria uma instância do EngagementChart
     * @param {HTMLElement} container - Container do widget
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Instâncias dos gráficos Chart.js
        this.charts = {
            timeline: null,
            bars: null,
            pie: null,
            rate: null
        };

        // Dados de engajamento
        this.engagementData = null;

        // Período selecionado
        this.selectedPeriod = '30d';

        // Cores do tema
        this.colors = {
            primary: '#667eea',
            secondary: '#764ba2',
            success: '#28a745',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8',
            likes: '#e91e63',
            comments: '#2196f3',
            shares: '#4caf50',
            saves: '#ff9800'
        };

        // Bind methods
        this.render = this.render.bind(this);
        this.loadData = this.loadData.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças no engajamento
        this.state.subscribe('engagement', (data) => {
            this.engagementData = data;
            this.render();
        });

        // Render inicial
        this.render();
    }

    /**
     * Carrega dados de engajamento
     */
    async loadData() {
        const username = this.state.get('currentUser');

        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        const loading = this.notifications.loading(`Carregando engajamento de @${username}...`);

        try {
            const result = await this.api.getEngagement(username, { period: this.selectedPeriod });

            if (result.success) {
                this.state.set('engagement', result);
                loading.success('Dados de engajamento carregados!');
            } else {
                loading.error(result.error || 'Erro ao carregar engajamento');
            }
        } catch (error) {
            loading.error(`Erro: ${error.message}`);
        }
    }

    /**
     * Renderiza o widget
     */
    render() {
        if (!this.container) return;

        if (!this.engagementData) {
            this.container.innerHTML = this.renderEmptyState();
            this.attachEventListeners();
            return;
        }

        this.container.innerHTML = this.renderChartWidget();
        this.attachEventListeners();

        // Inicializar gráficos após render
        setTimeout(() => {
            this.initializeCharts();
        }, 100);
    }

    /**
     * Renderiza estado vazio
     * @returns {string} HTML
     */
    renderEmptyState() {
        return `
            <div class="widget engagement-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-chart-line"></i> Análise de Engajamento
                    </h3>
                </div>
                
                <div class="engagement-empty">
                    <div class="engagement-empty__icon">
                        <i class="fas fa-chart-bar"></i>
                    </div>
                    <p>Clique para carregar dados de engajamento</p>
                    <button class="btn btn-primary" id="btn-load-engagement">
                        <i class="fas fa-sync-alt"></i>
                        Carregar Dados
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza widget com dados
     * @returns {string} HTML
     */
    renderChartWidget() {
        const data = this.engagementData;
        const summary = data.summary || {};

        return `
            <div class="widget engagement-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-chart-line"></i> Análise de Engajamento
                    </h3>
                    <div class="widget__actions">
                        <select class="period-select" id="period-select">
                            <option value="7d" ${this.selectedPeriod === '7d' ? 'selected' : ''}>7 dias</option>
                            <option value="30d" ${this.selectedPeriod === '30d' ? 'selected' : ''}>30 dias</option>
                            <option value="90d" ${this.selectedPeriod === '90d' ? 'selected' : ''}>90 dias</option>
                            <option value="all" ${this.selectedPeriod === 'all' ? 'selected' : ''}>Todo período</option>
                        </select>
                        <button class="widget__action-btn" id="btn-refresh-engagement" title="Atualizar">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Cards de Resumo -->
                <div class="engagement-summary">
                    ${this.renderSummaryCards(summary)}
                </div>
                
                <!-- Gráfico de Linha Temporal -->
                <div class="chart-section">
                    <h4>
                        <i class="fas fa-chart-line"></i>
                        Engajamento ao Longo do Tempo
                    </h4>
                    <div class="chart-container">
                        <canvas id="timeline-chart"></canvas>
                    </div>
                </div>
                
                <!-- Gráfico de Barras por Post -->
                <div class="chart-section">
                    <h4>
                        <i class="fas fa-chart-bar"></i>
                        Engajamento por Post (Top 10)
                    </h4>
                    <div class="chart-container chart-container--medium">
                        <canvas id="bars-chart"></canvas>
                    </div>
                </div>
                
                <!-- Gráficos Pequenos -->
                <div class="charts-row">
                    <!-- Distribuição de Interações -->
                    <div class="chart-section chart-section--half">
                        <h4>
                            <i class="fas fa-chart-pie"></i>
                            Distribuição
                        </h4>
                        <div class="chart-container chart-container--small">
                            <canvas id="pie-chart"></canvas>
                        </div>
                    </div>
                    
                    <!-- Taxa de Engajamento -->
                    <div class="chart-section chart-section--half">
                        <h4>
                            <i class="fas fa-percentage"></i>
                            Taxa de Engajamento
                        </h4>
                        <div class="chart-container chart-container--small">
                            <canvas id="rate-chart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Insights -->
                ${data.insights ? this.renderInsights(data.insights) : ''}
                
                <!-- Timestamp -->
                <div class="widget__footer">
                    <small>
                        <i class="far fa-clock"></i>
                        Atualizado em: ${this.formatDate(data.updated_at || new Date())}
                    </small>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza cards de resumo
     * @param {Object} summary - Dados de resumo
     * @returns {string} HTML
     */
    renderSummaryCards(summary) {
        const cards = [
            {
                icon: 'fa-heart',
                label: 'Total de Curtidas',
                value: this.formatNumber(summary.total_likes || 0),
                color: 'likes',
                change: summary.likes_change
            },
            {
                icon: 'fa-comment',
                label: 'Total de Comentários',
                value: this.formatNumber(summary.total_comments || 0),
                color: 'comments',
                change: summary.comments_change
            },
            {
                icon: 'fa-percentage',
                label: 'Taxa de Engajamento',
                value: `${(summary.engagement_rate || 0).toFixed(2)}%`,
                color: 'primary',
                change: summary.rate_change
            },
            {
                icon: 'fa-fire',
                label: 'Média por Post',
                value: this.formatNumber(summary.avg_per_post || 0),
                color: 'warning',
                change: summary.avg_change
            }
        ];

        return cards.map(card => `
            <div class="summary-card summary-card--${card.color}">
                <div class="summary-card__icon">
                    <i class="fas ${card.icon}"></i>
                </div>
                <div class="summary-card__content">
                    <span class="summary-value">${card.value}</span>
                    <span class="summary-label">${card.label}</span>
                </div>
                ${card.change !== undefined ? `
                    <div class="summary-card__change ${card.change >= 0 ? 'positive' : 'negative'}">
                        <i class="fas ${card.change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down'}"></i>
                        ${Math.abs(card.change).toFixed(1)}%
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    /**
     * Renderiza insights
     * @param {Array} insights - Lista de insights
     * @returns {string} HTML
     */
    renderInsights(insights) {
        if (!insights || insights.length === 0) return '';

        return `
            <div class="engagement-insights">
                <h4>
                    <i class="fas fa-lightbulb"></i>
                    Insights
                </h4>
                <div class="insights-list">
                    ${insights.map(insight => `
                        <div class="insight-item insight-item--${insight.type || 'info'}">
                            <i class="fas ${this.getInsightIcon(insight.type)}"></i>
                            <span>${this.escapeHtml(insight.message)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Inicializa todos os gráficos
     */
    initializeCharts() {
        // Verificar se Chart.js está disponível
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js não disponível');
            return;
        }

        // Destruir gráficos existentes
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });

        // Inicializar cada gráfico
        this.initTimelineChart();
        this.initBarsChart();
        this.initPieChart();
        this.initRateChart();
    }

    /**
     * Inicializa gráfico de linha temporal
     */
    initTimelineChart() {
        const canvas = this.container.querySelector('#timeline-chart');
        if (!canvas) return;

        const data = this.engagementData;
        const timeline = data.timeline || [];

        // Preparar dados
        const labels = timeline.map(t => this.formatDateShort(t.date));
        const likesData = timeline.map(t => t.likes || 0);
        const commentsData = timeline.map(t => t.comments || 0);

        this.charts.timeline = new Chart(canvas, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Curtidas',
                        data: likesData,
                        borderColor: this.colors.likes,
                        backgroundColor: this.hexToRgba(this.colors.likes, 0.1),
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Comentários',
                        data: commentsData,
                        borderColor: this.colors.comments,
                        backgroundColor: this.hexToRgba(this.colors.comments, 0.1),
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#adb5bd',
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: this.colors.primary,
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#adb5bd'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#adb5bd'
                        }
                    }
                }
            }
        });
    }

    /**
     * Inicializa gráfico de barras
     */
    initBarsChart() {
        const canvas = this.container.querySelector('#bars-chart');
        if (!canvas) return;

        const data = this.engagementData;
        const posts = (data.top_posts || []).slice(0, 10);

        // Preparar dados
        const labels = posts.map((p, i) => `Post ${i + 1}`);
        const likesData = posts.map(p => p.likes || 0);
        const commentsData = posts.map(p => p.comments || 0);

        this.charts.bars = new Chart(canvas, {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Curtidas',
                        data: likesData,
                        backgroundColor: this.colors.likes,
                        borderRadius: 4
                    },
                    {
                        label: 'Comentários',
                        data: commentsData,
                        backgroundColor: this.colors.comments,
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#adb5bd',
                            usePointStyle: true
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#adb5bd'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#adb5bd'
                        }
                    }
                }
            }
        });
    }

    /**
     * Inicializa gráfico de pizza
     */
    initPieChart() {
        const canvas = this.container.querySelector('#pie-chart');
        if (!canvas) return;

        const data = this.engagementData;
        const summary = data.summary || {};

        // Preparar dados
        const chartData = {
            labels: ['Curtidas', 'Comentários', 'Compartilhamentos', 'Salvos'],
            datasets: [{
                data: [
                    summary.total_likes || 0,
                    summary.total_comments || 0,
                    summary.total_shares || 0,
                    summary.total_saves || 0
                ],
                backgroundColor: [
                    this.colors.likes,
                    this.colors.comments,
                    this.colors.shares,
                    this.colors.saves
                ],
                borderWidth: 0
            }]
        };

        this.charts.pie = new Chart(canvas, {
            type: 'doughnut',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#adb5bd',
                            usePointStyle: true,
                            padding: 15
                        }
                    }
                }
            }
        });
    }

    /**
     * Inicializa gráfico de taxa
     */
    initRateChart() {
        const canvas = this.container.querySelector('#rate-chart');
        if (!canvas) return;

        const data = this.engagementData;
        const rateHistory = data.rate_history || [];

        // Preparar dados
        const labels = rateHistory.map(r => this.formatDateShort(r.date));
        const rateData = rateHistory.map(r => r.rate || 0);

        this.charts.rate = new Chart(canvas, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Taxa de Engajamento',
                    data: rateData,
                    borderColor: this.colors.primary,
                    backgroundColor: this.hexToRgba(this.colors.primary, 0.2),
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: false
                    }
                }
            }
        });
    }

    /**
     * Muda período selecionado
     * @param {string} period - Período
     */
    changePeriod(period) {
        this.selectedPeriod = period;
        this.loadData();
    }

    /**
     * Obtém ícone do insight
     * @param {string} type - Tipo
     * @returns {string}
     */
    getInsightIcon(type) {
        const icons = {
            'success': 'fa-check-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle',
            'tip': 'fa-lightbulb'
        };

        return icons[type] || 'fa-info-circle';
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Botão carregar
        const btnLoad = this.container.querySelector('#btn-load-engagement');
        if (btnLoad) {
            btnLoad.addEventListener('click', () => this.loadData());
        }

        // Botão refresh
        const btnRefresh = this.container.querySelector('#btn-refresh-engagement');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.loadData());
        }

        // Select de período
        const periodSelect = this.container.querySelector('#period-select');
        if (periodSelect) {
            periodSelect.addEventListener('change', (e) => {
                this.changePeriod(e.target.value);
            });
        }
    }

    // ==========================================================================
    // UTILITÁRIOS
    // ==========================================================================

    /**
     * Formata número grande
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
     * Converte hex para rgba
     * @param {string} hex - Cor hex
     * @param {number} alpha - Alpha
     * @returns {string}
     */
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
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

    /**
     * Formata data
     * @param {Date|string} date - Data
     * @returns {string}
     */
    formatDate(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Formata data curta
     * @param {Date|string} date - Data
     * @returns {string}
     */
    formatDateShort(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short'
        });
    }

    /**
     * Destrói gráficos
     */
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};
    }
}

// Factory function
export function createEngagementChart(container) {
    const chart = new EngagementChart(container);
    chart.init();
    return chart;
}

export default EngagementChart;
