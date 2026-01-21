/**
 * AIInsightsPanel.js - Painel de Insights com IA
 * 
 * Exibe insights gerados pela IA:
 * - Análise de sentimento geral
 * - Previsões comportamentais
 * - Anomalias detectadas
 * - Recomendações de investigação
 * - Resumo executivo
 * 
 * @module AIInsightsPanel
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class AIInsightsPanel {
    /**
     * Cria uma instância do AIInsightsPanel
     * @param {HTMLElement} container - Container do painel
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Dados de insights
        this.insightsData = null;

        // Estado de carregamento
        this.isLoading = false;

        // Seção ativa
        this.activeSection = 'summary';

        // Bind methods
        this.render = this.render.bind(this);
        this.analyze = this.analyze.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças nos insights
        this.state.subscribe('aiInsights', (data) => {
            this.insightsData = data;
            this.render();
        });

        // Render inicial
        this.render();
    }

    /**
     * Gera análise de IA
     */
    async analyze() {
        const username = this.state.get('currentUser');

        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        this.isLoading = true;
        this.render();

        const loading = this.notifications.loading(`Gerando insights de @${username}...`);

        try {
            const result = await this.api.getAIInsights(username);

            if (result.success) {
                this.state.set('aiInsights', result);
                loading.success('Análise de IA concluída!');
            } else {
                loading.error(result.error || 'Erro na análise de IA');
            }
        } catch (error) {
            loading.error(`Erro: ${error.message}`);
        } finally {
            this.isLoading = false;
            this.render();
        }
    }

    /**
     * Renderiza o painel
     */
    render() {
        if (!this.container) return;

        if (!this.insightsData) {
            this.container.innerHTML = this.renderEmptyState();
            this.attachEventListeners();
            return;
        }

        this.container.innerHTML = this.renderInsightsPanel();
        this.attachEventListeners();
    }

    /**
     * Renderiza estado vazio
     * @returns {string} HTML
     */
    renderEmptyState() {
        return `
            <div class="widget ai-insights-panel">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-brain"></i> Insights de IA
                    </h3>
                </div>
                
                <div class="ai-empty ${this.isLoading ? 'ai-empty--loading' : ''}">
                    ${this.isLoading ? `
                        <div class="ai-loading-animation">
                            <div class="brain-pulse">
                                <i class="fas fa-brain"></i>
                            </div>
                            <p>Processando dados com IA...</p>
                            <div class="loading-progress">
                                <div class="progress-bar"></div>
                            </div>
                        </div>
                    ` : `
                        <div class="ai-empty__icon">
                            <i class="fas fa-robot"></i>
                        </div>
                        <p>Clique para gerar insights com inteligência artificial</p>
                        <button class="btn btn-primary" id="btn-generate-insights">
                            <i class="fas fa-magic"></i>
                            Gerar Insights
                        </button>
                    `}
                </div>
            </div>
        `;
    }

    /**
     * Renderiza painel com dados
     * @returns {string} HTML
     */
    renderInsightsPanel() {
        const data = this.insightsData;

        return `
            <div class="widget ai-insights-panel">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-brain"></i> Insights de IA
                    </h3>
                    <div class="widget__actions">
                        <span class="ai-model-badge">
                            <i class="fas fa-microchip"></i>
                            ${data.model_used || 'Local'}
                        </span>
                        <button class="widget__action-btn" id="btn-refresh-insights" title="Atualizar">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Navegação de Seções -->
                <div class="insights-nav">
                    <button class="nav-tab ${this.activeSection === 'summary' ? 'active' : ''}" 
                            data-section="summary">
                        <i class="fas fa-file-alt"></i>
                        Resumo
                    </button>
                    <button class="nav-tab ${this.activeSection === 'sentiment' ? 'active' : ''}" 
                            data-section="sentiment">
                        <i class="fas fa-smile"></i>
                        Sentimento
                    </button>
                    <button class="nav-tab ${this.activeSection === 'predictions' ? 'active' : ''}" 
                            data-section="predictions">
                        <i class="fas fa-crystal-ball"></i>
                        Previsões
                    </button>
                    <button class="nav-tab ${this.activeSection === 'anomalies' ? 'active' : ''}" 
                            data-section="anomalies">
                        <i class="fas fa-exclamation-triangle"></i>
                        Anomalias
                    </button>
                    <button class="nav-tab ${this.activeSection === 'recommendations' ? 'active' : ''}" 
                            data-section="recommendations">
                        <i class="fas fa-lightbulb"></i>
                        Recomendações
                    </button>
                </div>
                
                <!-- Conteúdo das Seções -->
                <div class="insights-content">
                    ${this.renderActiveSection()}
                </div>
                
                <!-- Confiança do Modelo -->
                <div class="model-confidence">
                    <span class="confidence-label">Confiança do Modelo:</span>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${(data.confidence || 0) * 100}%"></div>
                    </div>
                    <span class="confidence-value">${((data.confidence || 0) * 100).toFixed(0)}%</span>
                </div>
                
                <!-- Timestamp -->
                <div class="widget__footer">
                    <small>
                        <i class="far fa-clock"></i>
                        Análise realizada em: ${this.formatDate(data.analyzed_at || new Date())}
                    </small>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza seção ativa
     * @returns {string} HTML
     */
    renderActiveSection() {
        switch (this.activeSection) {
            case 'summary':
                return this.renderSummarySection();
            case 'sentiment':
                return this.renderSentimentSection();
            case 'predictions':
                return this.renderPredictionsSection();
            case 'anomalies':
                return this.renderAnomaliesSection();
            case 'recommendations':
                return this.renderRecommendationsSection();
            default:
                return this.renderSummarySection();
        }
    }

    /**
     * Renderiza seção de resumo
     * @returns {string} HTML
     */
    renderSummarySection() {
        const summary = this.insightsData.executive_summary || {};
        const highlights = this.insightsData.highlights || [];

        return `
            <div class="insight-section insight-section--summary">
                <h4>
                    <i class="fas fa-file-alt"></i>
                    Resumo Executivo
                </h4>
                
                ${summary.overview ? `
                    <div class="summary-overview">
                        <p>${this.escapeHtml(summary.overview)}</p>
                    </div>
                ` : ''}
                
                ${highlights.length > 0 ? `
                    <div class="summary-highlights">
                        <h5>Destaques Principais</h5>
                        <ul>
                            ${highlights.map(h => `
                                <li class="highlight-item highlight-item--${h.type || 'info'}">
                                    <i class="fas ${this.getHighlightIcon(h.type)}"></i>
                                    <span>${this.escapeHtml(h.text)}</span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${summary.profile_type ? `
                    <div class="profile-classification">
                        <span class="classification-label">Classificação do Perfil:</span>
                        <span class="classification-badge">${this.escapeHtml(summary.profile_type)}</span>
                    </div>
                ` : ''}
                
                ${summary.key_metrics ? `
                    <div class="key-metrics">
                        <h5>Métricas Chave</h5>
                        <div class="metrics-grid">
                            ${Object.entries(summary.key_metrics).map(([key, value]) => `
                                <div class="metric-item">
                                    <span class="metric-label">${this.formatMetricKey(key)}</span>
                                    <span class="metric-value">${this.formatMetricValue(value)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Renderiza seção de sentimento
     * @returns {string} HTML
     */
    renderSentimentSection() {
        const sentiment = this.insightsData.sentiment_analysis || {};
        const overall = sentiment.overall || {};
        const breakdown = sentiment.breakdown || {};
        const topics = sentiment.topics || [];

        return `
            <div class="insight-section insight-section--sentiment">
                <h4>
                    <i class="fas fa-smile"></i>
                    Análise de Sentimento
                </h4>
                
                <!-- Sentimento Geral -->
                <div class="sentiment-gauge">
                    <div class="gauge-visual">
                        <div class="gauge-arc" style="--sentiment: ${(overall.score || 0.5) * 100}%"></div>
                        <div class="gauge-indicator" style="--rotation: ${(overall.score || 0.5) * 180}deg"></div>
                    </div>
                    <div class="gauge-info">
                        <span class="gauge-value">${(overall.score || 0).toFixed(2)}</span>
                        <span class="gauge-label ${this.getSentimentClass(overall.score)}">${this.getSentimentLabel(overall.score)}</span>
                    </div>
                </div>
                
                <!-- Breakdown -->
                ${Object.keys(breakdown).length > 0 ? `
                    <div class="sentiment-breakdown">
                        <h5>Distribuição</h5>
                        <div class="breakdown-bars">
                            <div class="breakdown-bar breakdown-bar--positive">
                                <span class="bar-label">Positivo</span>
                                <div class="bar-track">
                                    <div class="bar-fill" style="width: ${(breakdown.positive || 0) * 100}%"></div>
                                </div>
                                <span class="bar-value">${((breakdown.positive || 0) * 100).toFixed(0)}%</span>
                            </div>
                            <div class="breakdown-bar breakdown-bar--neutral">
                                <span class="bar-label">Neutro</span>
                                <div class="bar-track">
                                    <div class="bar-fill" style="width: ${(breakdown.neutral || 0) * 100}%"></div>
                                </div>
                                <span class="bar-value">${((breakdown.neutral || 0) * 100).toFixed(0)}%</span>
                            </div>
                            <div class="breakdown-bar breakdown-bar--negative">
                                <span class="bar-label">Negativo</span>
                                <div class="bar-track">
                                    <div class="bar-fill" style="width: ${(breakdown.negative || 0) * 100}%"></div>
                                </div>
                                <span class="bar-value">${((breakdown.negative || 0) * 100).toFixed(0)}%</span>
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                <!-- Tópicos -->
                ${topics.length > 0 ? `
                    <div class="sentiment-topics">
                        <h5>Sentimento por Tópico</h5>
                        <div class="topics-list">
                            ${topics.map(topic => `
                                <div class="topic-item">
                                    <span class="topic-name">${this.escapeHtml(topic.name)}</span>
                                    <div class="topic-sentiment">
                                        <div class="mini-gauge ${this.getSentimentClass(topic.score)}">
                                            ${topic.score.toFixed(2)}
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Nuances -->
                ${sentiment.nuances && sentiment.nuances.length > 0 ? `
                    <div class="sentiment-nuances">
                        <h5>Nuances Detectadas</h5>
                        <div class="nuances-tags">
                            ${sentiment.nuances.map(n => `
                                <span class="nuance-tag">${this.escapeHtml(n)}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Renderiza seção de previsões
     * @returns {string} HTML
     */
    renderPredictionsSection() {
        const predictions = this.insightsData.predictions || [];
        const behavioral = this.insightsData.behavioral_predictions || {};

        return `
            <div class="insight-section insight-section--predictions">
                <h4>
                    <i class="fas fa-crystal-ball"></i>
                    Previsões Comportamentais
                </h4>
                
                ${predictions.length > 0 ? `
                    <div class="predictions-list">
                        ${predictions.map(pred => `
                            <div class="prediction-card">
                                <div class="prediction-icon">
                                    <i class="fas ${this.getPredictionIcon(pred.category)}"></i>
                                </div>
                                <div class="prediction-content">
                                    <span class="prediction-title">${this.escapeHtml(pred.title)}</span>
                                    <span class="prediction-description">${this.escapeHtml(pred.description)}</span>
                                    ${pred.time_window ? `
                                        <span class="prediction-time">
                                            <i class="far fa-clock"></i>
                                            ${this.escapeHtml(pred.time_window)}
                                        </span>
                                    ` : ''}
                                </div>
                                <div class="prediction-probability">
                                    <div class="probability-circle" style="--prob: ${(pred.probability || 0) * 100}%">
                                        <span>${((pred.probability || 0) * 100).toFixed(0)}%</span>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : '<p class="empty-message">Nenhuma previsão disponível</p>'}
                
                ${behavioral.patterns ? `
                    <div class="behavioral-patterns">
                        <h5>Padrões Comportamentais</h5>
                        <ul>
                            ${behavioral.patterns.map(p => `<li>${this.escapeHtml(p)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Renderiza seção de anomalias
     * @returns {string} HTML
     */
    renderAnomaliesSection() {
        const anomalies = this.insightsData.anomalies || [];
        const riskLevel = this.insightsData.risk_level || 'low';

        return `
            <div class="insight-section insight-section--anomalies">
                <h4>
                    <i class="fas fa-exclamation-triangle"></i>
                    Anomalias Detectadas
                </h4>
                
                <div class="risk-indicator risk-indicator--${riskLevel}">
                    <span class="risk-label">Nível de Risco:</span>
                    <span class="risk-value">${this.getRiskLabel(riskLevel)}</span>
                </div>
                
                ${anomalies.length > 0 ? `
                    <div class="anomalies-list">
                        ${anomalies.map(anomaly => `
                            <div class="anomaly-item anomaly-item--${anomaly.severity || 'low'}">
                                <div class="anomaly-header">
                                    <i class="fas ${this.getAnomalyIcon(anomaly.type)}"></i>
                                    <span class="anomaly-title">${this.escapeHtml(anomaly.title)}</span>
                                    <span class="anomaly-severity">${this.getSeverityLabel(anomaly.severity)}</span>
                                </div>
                                <p class="anomaly-description">${this.escapeHtml(anomaly.description)}</p>
                                ${anomaly.evidence ? `
                                    <div class="anomaly-evidence">
                                        <small><strong>Evidência:</strong> ${this.escapeHtml(anomaly.evidence)}</small>
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                ` : `
                    <div class="no-anomalies">
                        <i class="fas fa-check-circle"></i>
                        <p>Nenhuma anomalia significativa detectada</p>
                    </div>
                `}
            </div>
        `;
    }

    /**
     * Renderiza seção de recomendações
     * @returns {string} HTML
     */
    renderRecommendationsSection() {
        const recommendations = this.insightsData.recommendations || [];
        const investigationPaths = this.insightsData.investigation_paths || [];

        return `
            <div class="insight-section insight-section--recommendations">
                <h4>
                    <i class="fas fa-lightbulb"></i>
                    Recomendações
                </h4>
                
                ${recommendations.length > 0 ? `
                    <div class="recommendations-list">
                        ${recommendations.map((rec, index) => `
                            <div class="recommendation-item">
                                <div class="recommendation-number">${index + 1}</div>
                                <div class="recommendation-content">
                                    <span class="recommendation-title">${this.escapeHtml(rec.title)}</span>
                                    <p class="recommendation-description">${this.escapeHtml(rec.description)}</p>
                                    ${rec.priority ? `
                                        <span class="recommendation-priority priority-${rec.priority}">
                                            Prioridade: ${this.getPriorityLabel(rec.priority)}
                                        </span>
                                    ` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : '<p class="empty-message">Nenhuma recomendação disponível</p>'}
                
                ${investigationPaths.length > 0 ? `
                    <div class="investigation-paths">
                        <h5><i class="fas fa-route"></i> Caminhos de Investigação</h5>
                        <div class="paths-list">
                            ${investigationPaths.map(path => `
                                <div class="path-item">
                                    <span class="path-name">${this.escapeHtml(path.name)}</span>
                                    <span class="path-potential">${path.potential || 'Moderado'}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Muda seção ativa
     * @param {string} section - Seção
     */
    setActiveSection(section) {
        this.activeSection = section;
        this.render();
    }

    // ==========================================================================
    // HELPERS
    // ==========================================================================

    /**
     * Obtém classe de sentimento
     * @param {number} score - Score
     * @returns {string}
     */
    getSentimentClass(score) {
        if (score > 0.6) return 'positive';
        if (score < 0.4) return 'negative';
        return 'neutral';
    }

    /**
     * Obtém label de sentimento
     * @param {number} score - Score
     * @returns {string}
     */
    getSentimentLabel(score) {
        if (score > 0.7) return 'Muito Positivo';
        if (score > 0.6) return 'Positivo';
        if (score > 0.4) return 'Neutro';
        if (score > 0.3) return 'Negativo';
        return 'Muito Negativo';
    }

    /**
     * Obtém ícone de highlight
     * @param {string} type - Tipo
     * @returns {string}
     */
    getHighlightIcon(type) {
        const icons = {
            'success': 'fa-check-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle',
            'danger': 'fa-times-circle'
        };
        return icons[type] || 'fa-circle';
    }

    /**
     * Obtém ícone de previsão
     * @param {string} category - Categoria
     * @returns {string}
     */
    getPredictionIcon(category) {
        const icons = {
            'post': 'fa-image',
            'story': 'fa-circle-notch',
            'activity': 'fa-chart-line',
            'engagement': 'fa-heart',
            'growth': 'fa-arrow-up',
            'decline': 'fa-arrow-down'
        };
        return icons[category] || 'fa-question';
    }

    /**
     * Obtém ícone de anomalia
     * @param {string} type - Tipo
     * @returns {string}
     */
    getAnomalyIcon(type) {
        const icons = {
            'followers': 'fa-users',
            'engagement': 'fa-heart',
            'activity': 'fa-clock',
            'content': 'fa-image',
            'behavior': 'fa-user'
        };
        return icons[type] || 'fa-exclamation';
    }

    /**
     * Obtém label de risco
     * @param {string} level - Nível
     * @returns {string}
     */
    getRiskLabel(level) {
        const labels = {
            'low': 'Baixo',
            'medium': 'Médio',
            'high': 'Alto',
            'critical': 'Crítico'
        };
        return labels[level] || level;
    }

    /**
     * Obtém label de severidade
     * @param {string} severity - Severidade
     * @returns {string}
     */
    getSeverityLabel(severity) {
        const labels = {
            'low': 'Baixa',
            'medium': 'Média',
            'high': 'Alta',
            'critical': 'Crítica'
        };
        return labels[severity] || severity;
    }

    /**
     * Obtém label de prioridade
     * @param {string} priority - Prioridade
     * @returns {string}
     */
    getPriorityLabel(priority) {
        const labels = {
            'low': 'Baixa',
            'medium': 'Média',
            'high': 'Alta'
        };
        return labels[priority] || priority;
    }

    /**
     * Formata chave de métrica
     * @param {string} key - Chave
     * @returns {string}
     */
    formatMetricKey(key) {
        return key
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Formata valor de métrica
     * @param {any} value - Valor
     * @returns {string}
     */
    formatMetricValue(value) {
        if (typeof value === 'number') {
            if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M';
            if (value >= 1000) return (value / 1000).toFixed(1) + 'K';
            if (value % 1 !== 0) return value.toFixed(2);
            return value.toString();
        }
        return String(value);
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Botão gerar insights
        const btnGenerate = this.container.querySelector('#btn-generate-insights');
        if (btnGenerate) {
            btnGenerate.addEventListener('click', () => this.analyze());
        }

        // Botão refresh
        const btnRefresh = this.container.querySelector('#btn-refresh-insights');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.analyze());
        }

        // Navegação de seções
        const navTabs = this.container.querySelectorAll('.insights-nav .nav-tab');
        navTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                this.setActiveSection(tab.dataset.section);
            });
        });
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
}

// Factory function
export function createAIInsightsPanel(container) {
    const panel = new AIInsightsPanel(container);
    panel.init();
    return panel;
}

export default AIInsightsPanel;
