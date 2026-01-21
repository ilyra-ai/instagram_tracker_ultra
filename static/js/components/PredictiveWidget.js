/**
 * PredictiveWidget.js - Widget de Análise Preditiva
 * 
 * Exibe previsões comportamentais com:
 * - Cards de previsões futuras
 * - Probabilidades em porcentagem
 * - Janela de tempo prevista
 * - Categorias: próximo post, horário provável, interações futuras
 * - Visualização em timeline
 * 
 * @module PredictiveWidget
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class PredictiveWidget {
    /**
     * Cria uma instância do PredictiveWidget
     * @param {HTMLElement} container - Container do widget
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Dados de previsão
        this.predictions = null;

        // Bind methods
        this.render = this.render.bind(this);
        this.analyze = this.analyze.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças nas previsões
        this.state.subscribe('predictions', (data) => {
            this.predictions = data;
            this.render();
        });

        // Render inicial
        this.render();
    }

    /**
     * Analisa e gera previsões
     */
    async analyze() {
        const username = this.state.get('currentUser');

        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        const loading = this.notifications.loading(`Gerando previsões para @${username}...`);

        try {
            const result = await this.api.getPredictions(username);

            if (result.success) {
                this.state.set('predictions', result);
                loading.success('Análise preditiva concluída!');
            } else {
                loading.error(result.error || 'Erro na análise preditiva');
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

        if (!this.predictions) {
            this.container.innerHTML = this.renderEmptyState();
            this.attachEventListeners();
            return;
        }

        this.container.innerHTML = this.renderPredictiveWidget();
        this.attachEventListeners();
    }

    /**
     * Renderiza estado vazio
     * @returns {string} HTML
     */
    renderEmptyState() {
        return `
            <div class="widget predictive-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-crystal-ball"></i> Análise Preditiva
                    </h3>
                </div>
                
                <div class="predictive-empty">
                    <div class="predictive-empty__icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <p>Clique para gerar previsões comportamentais</p>
                    <button class="btn btn-primary" id="btn-analyze-predictions">
                        <i class="fas fa-magic"></i>
                        Gerar Previsões
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza widget com dados
     * @returns {string} HTML
     */
    renderPredictiveWidget() {
        const data = this.predictions;

        // Extrair diferentes tipos de previsões
        const nextPost = data.next_post_prediction;
        const activityPattern = data.activity_pattern;
        const engagementForecast = data.engagement_forecast;
        const behaviorPredictions = data.behavior_predictions || [];
        const interactionPredictions = data.interaction_predictions || [];
        const confidence = data.model_confidence || 0;

        return `
            <div class="widget predictive-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-crystal-ball"></i> Análise Preditiva
                    </h3>
                    <div class="widget__actions">
                        <span class="confidence-badge confidence-badge--${this.getConfidenceClass(confidence)}">
                            <i class="fas fa-check-circle"></i>
                            ${(confidence * 100).toFixed(0)}% confiança
                        </span>
                        <button class="widget__action-btn" id="btn-refresh-predictions" title="Atualizar">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Card de Próximo Post -->
                ${nextPost ? this.renderNextPostCard(nextPost) : ''}
                
                <!-- Padrão de Atividade -->
                ${activityPattern ? this.renderActivityPatternCard(activityPattern) : ''}
                
                <!-- Previsões de Comportamento -->
                ${behaviorPredictions.length > 0 ? `
                    <div class="prediction-section">
                        <h4>
                            <i class="fas fa-user-clock"></i>
                            Previsões de Comportamento
                        </h4>
                        <div class="predictions-grid">
                            ${behaviorPredictions.map(pred => this.renderPredictionCard(pred)).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Previsões de Interação -->
                ${interactionPredictions.length > 0 ? `
                    <div class="prediction-section">
                        <h4>
                            <i class="fas fa-handshake"></i>
                            Previsões de Interação
                        </h4>
                        <div class="predictions-list">
                            ${interactionPredictions.map(pred => this.renderInteractionPrediction(pred)).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Previsão de Engajamento -->
                ${engagementForecast ? this.renderEngagementForecast(engagementForecast) : ''}
                
                <!-- Timeline de Previsões -->
                <div class="prediction-timeline" id="prediction-timeline">
                    <h4>
                        <i class="fas fa-calendar-alt"></i>
                        Linha do Tempo Prevista
                    </h4>
                    ${this.renderPredictionTimeline()}
                </div>
                
                <!-- Timestamp -->
                <div class="widget__footer">
                    <small>
                        <i class="far fa-clock"></i>
                        Previsões geradas em: ${this.formatDate(data.analyzed_at || new Date())}
                    </small>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza card de próximo post
     * @param {Object} nextPost - Dados de previsão
     * @returns {string} HTML
     */
    renderNextPostCard(nextPost) {
        const probability = nextPost.probability || 0;
        const timeWindow = nextPost.time_window || {};
        const contentType = nextPost.predicted_content_type || 'desconhecido';

        return `
            <div class="prediction-card prediction-card--featured">
                <div class="prediction-card__icon">
                    <i class="fas fa-image"></i>
                </div>
                <div class="prediction-card__content">
                    <h4>Próximo Post</h4>
                    <div class="prediction-card__main">
                        <span class="prediction-time">
                            ${this.formatTimeWindow(timeWindow)}
                        </span>
                        <span class="prediction-type">
                            <i class="fas ${this.getContentTypeIcon(contentType)}"></i>
                            ${this.getContentTypeLabel(contentType)}
                        </span>
                    </div>
                    <div class="prediction-probability">
                        <div class="probability-bar">
                            <div class="probability-fill" style="width: ${probability * 100}%"></div>
                        </div>
                        <span class="probability-value">${(probability * 100).toFixed(0)}% probabilidade</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza card de padrão de atividade
     * @param {Object} pattern - Dados do padrão
     * @returns {string} HTML
     */
    renderActivityPatternCard(pattern) {
        const peakHours = pattern.peak_hours || [];
        const peakDays = pattern.peak_days || [];
        const averagePostsPerWeek = pattern.average_posts_per_week || 0;

        return `
            <div class="prediction-card prediction-card--pattern">
                <div class="prediction-card__icon">
                    <i class="fas fa-clock"></i>
                </div>
                <div class="prediction-card__content">
                    <h4>Padrão de Atividade</h4>
                    
                    <div class="pattern-stats">
                        <div class="pattern-stat">
                            <i class="fas fa-calendar-week"></i>
                            <span>${averagePostsPerWeek.toFixed(1)} posts/semana</span>
                        </div>
                        
                        ${peakHours.length > 0 ? `
                            <div class="pattern-stat">
                                <i class="far fa-clock"></i>
                                <span>Horário pico: ${peakHours.slice(0, 3).join(', ')}h</span>
                            </div>
                        ` : ''}
                        
                        ${peakDays.length > 0 ? `
                            <div class="pattern-stat">
                                <i class="fas fa-calendar-day"></i>
                                <span>Dias ativos: ${peakDays.slice(0, 3).join(', ')}</span>
                            </div>
                        ` : ''}
                    </div>
                    
                    <!-- Heatmap de Horários -->
                    <div class="hourly-heatmap">
                        ${this.renderHourlyHeatmap(pattern.hourly_distribution || {})}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza heatmap de horários
     * @param {Object} distribution - Distribuição por hora
     * @returns {string} HTML
     */
    renderHourlyHeatmap(distribution) {
        const maxValue = Math.max(...Object.values(distribution), 1);

        let html = '<div class="heatmap-grid">';

        for (let hour = 0; hour < 24; hour++) {
            const value = distribution[hour] || 0;
            const intensity = value / maxValue;
            const colorClass = this.getHeatmapColor(intensity);

            html += `
                <div class="heatmap-cell heatmap-cell--${colorClass}" 
                     title="${hour}h: ${value} atividades"
                     style="opacity: ${0.3 + intensity * 0.7}">
                    <span class="heatmap-hour">${hour}</span>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    /**
     * Obtém classe de cor do heatmap
     * @param {number} intensity - Intensidade (0-1)
     * @returns {string}
     */
    getHeatmapColor(intensity) {
        if (intensity > 0.75) return 'hot';
        if (intensity > 0.5) return 'warm';
        if (intensity > 0.25) return 'mild';
        return 'cool';
    }

    /**
     * Renderiza card de previsão individual
     * @param {Object} pred - Dados da previsão
     * @returns {string} HTML
     */
    renderPredictionCard(pred) {
        const icon = this.getPredictionIcon(pred.category);
        const colorClass = this.getPredictionColorClass(pred.probability);

        return `
            <div class="prediction-mini-card prediction-mini-card--${colorClass}">
                <div class="prediction-mini-card__icon">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="prediction-mini-card__content">
                    <span class="prediction-title">${this.escapeHtml(pred.title || pred.category)}</span>
                    <span class="prediction-desc">${this.escapeHtml(pred.description || '')}</span>
                </div>
                <div class="prediction-mini-card__prob">
                    <span class="prob-value">${(pred.probability * 100).toFixed(0)}%</span>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza previsão de interação
     * @param {Object} pred - Dados da previsão
     * @returns {string} HTML
     */
    renderInteractionPrediction(pred) {
        return `
            <div class="interaction-prediction">
                <div class="interaction-users">
                    <span class="interaction-from">@${this.escapeHtml(pred.from_user || 'usuário')}</span>
                    <i class="fas fa-arrow-right"></i>
                    <span class="interaction-to">@${this.escapeHtml(pred.to_user || 'alvo')}</span>
                </div>
                <div class="interaction-type">
                    <i class="fas ${this.getInteractionIcon(pred.interaction_type)}"></i>
                    <span>${this.getInteractionLabel(pred.interaction_type)}</span>
                </div>
                <div class="interaction-prob">
                    ${(pred.probability * 100).toFixed(0)}%
                </div>
            </div>
        `;
    }

    /**
     * Renderiza previsão de engajamento
     * @param {Object} forecast - Dados de previsão
     * @returns {string} HTML
     */
    renderEngagementForecast(forecast) {
        const trend = forecast.trend || 'stable';
        const change = forecast.predicted_change || 0;

        const trendIcon = trend === 'up' ? 'fa-arrow-up' : trend === 'down' ? 'fa-arrow-down' : 'fa-minus';
        const trendClass = trend === 'up' ? 'positive' : trend === 'down' ? 'negative' : 'neutral';

        return `
            <div class="prediction-card prediction-card--engagement">
                <div class="prediction-card__icon">
                    <i class="fas fa-chart-bar"></i>
                </div>
                <div class="prediction-card__content">
                    <h4>Previsão de Engajamento</h4>
                    <div class="engagement-forecast">
                        <div class="forecast-trend forecast-trend--${trendClass}">
                            <i class="fas ${trendIcon}"></i>
                            <span>${change > 0 ? '+' : ''}${(change * 100).toFixed(1)}%</span>
                        </div>
                        <span class="forecast-label">nas próximas 2 semanas</span>
                    </div>
                    ${forecast.factors ? `
                        <div class="forecast-factors">
                            <small>Fatores: ${forecast.factors.join(', ')}</small>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Renderiza timeline de previsões
     * @returns {string} HTML
     */
    renderPredictionTimeline() {
        if (!this.predictions) return '<p>Sem dados</p>';

        const events = this.generateTimelineEvents();

        if (events.length === 0) {
            return '<p class="empty-message">Nenhum evento previsto</p>';
        }

        return `
            <div class="timeline">
                ${events.map((event, index) => `
                    <div class="timeline-item timeline-item--${event.type}">
                        <div class="timeline-marker">
                            <i class="fas ${event.icon}"></i>
                        </div>
                        <div class="timeline-content">
                            <span class="timeline-date">${event.date}</span>
                            <span class="timeline-title">${event.title}</span>
                            <span class="timeline-prob">${event.probability}%</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Gera eventos para timeline
     * @returns {Array}
     */
    generateTimelineEvents() {
        const events = [];
        const data = this.predictions;

        // Adicionar previsão de próximo post
        if (data.next_post_prediction) {
            events.push({
                type: 'post',
                icon: 'fa-image',
                date: this.formatTimeWindow(data.next_post_prediction.time_window),
                title: 'Novo post esperado',
                probability: (data.next_post_prediction.probability * 100).toFixed(0)
            });
        }

        // Adicionar previsões comportamentais
        if (data.behavior_predictions) {
            data.behavior_predictions.forEach(pred => {
                if (pred.time_window) {
                    events.push({
                        type: pred.category || 'behavior',
                        icon: this.getPredictionIcon(pred.category),
                        date: this.formatTimeWindow(pred.time_window),
                        title: pred.title || pred.description,
                        probability: (pred.probability * 100).toFixed(0)
                    });
                }
            });
        }

        // Ordenar por probabilidade
        events.sort((a, b) => parseFloat(b.probability) - parseFloat(a.probability));

        return events.slice(0, 5);
    }

    /**
     * Obtém ícone da previsão
     * @param {string} category - Categoria
     * @returns {string}
     */
    getPredictionIcon(category) {
        const icons = {
            'post': 'fa-image',
            'story': 'fa-circle-notch',
            'reel': 'fa-video',
            'like': 'fa-heart',
            'comment': 'fa-comment',
            'follow': 'fa-user-plus',
            'unfollow': 'fa-user-minus',
            'activity': 'fa-chart-line'
        };

        return icons[category] || 'fa-question';
    }

    /**
     * Obtém ícone de tipo de interação
     * @param {string} type - Tipo
     * @returns {string}
     */
    getInteractionIcon(type) {
        const icons = {
            'like': 'fa-heart',
            'comment': 'fa-comment',
            'follow': 'fa-user-plus',
            'mention': 'fa-at',
            'dm': 'fa-envelope'
        };

        return icons[type] || 'fa-handshake';
    }

    /**
     * Obtém label de tipo de interação
     * @param {string} type - Tipo
     * @returns {string}
     */
    getInteractionLabel(type) {
        const labels = {
            'like': 'Curtida',
            'comment': 'Comentário',
            'follow': 'Seguir',
            'mention': 'Menção',
            'dm': 'Mensagem Direta'
        };

        return labels[type] || type || 'Interação';
    }

    /**
     * Obtém ícone de tipo de conteúdo
     * @param {string} type - Tipo
     * @returns {string}
     */
    getContentTypeIcon(type) {
        const icons = {
            'photo': 'fa-image',
            'video': 'fa-video',
            'carousel': 'fa-images',
            'reel': 'fa-film',
            'story': 'fa-circle-notch'
        };

        return icons[type] || 'fa-question';
    }

    /**
     * Obtém label de tipo de conteúdo
     * @param {string} type - Tipo
     * @returns {string}
     */
    getContentTypeLabel(type) {
        const labels = {
            'photo': 'Foto',
            'video': 'Vídeo',
            'carousel': 'Carrossel',
            'reel': 'Reel',
            'story': 'Story'
        };

        return labels[type] || type || 'Desconhecido';
    }

    /**
     * Obtém classe de confiança
     * @param {number} confidence - Confiança (0-1)
     * @returns {string}
     */
    getConfidenceClass(confidence) {
        if (confidence > 0.7) return 'high';
        if (confidence > 0.4) return 'medium';
        return 'low';
    }

    /**
     * Obtém classe de cor da previsão
     * @param {number} probability - Probabilidade
     * @returns {string}
     */
    getPredictionColorClass(probability) {
        if (probability > 0.7) return 'high';
        if (probability > 0.4) return 'medium';
        return 'low';
    }

    /**
     * Formata janela de tempo
     * @param {Object} timeWindow - Janela de tempo
     * @returns {string}
     */
    formatTimeWindow(timeWindow) {
        if (!timeWindow) return 'Em breve';

        if (timeWindow.start && timeWindow.end) {
            return `${this.formatDate(timeWindow.start)} - ${this.formatDate(timeWindow.end)}`;
        }

        if (timeWindow.hours) {
            return `Próximas ${timeWindow.hours} horas`;
        }

        if (timeWindow.days) {
            return `Próximos ${timeWindow.days} dias`;
        }

        return 'Em breve';
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        const btnAnalyze = this.container.querySelector('#btn-analyze-predictions');
        if (btnAnalyze) {
            btnAnalyze.addEventListener('click', () => this.analyze());
        }

        const btnRefresh = this.container.querySelector('#btn-refresh-predictions');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.analyze());
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
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Factory function
export function createPredictiveWidget(container) {
    const widget = new PredictiveWidget(container);
    widget.init();
    return widget;
}

export default PredictiveWidget;
