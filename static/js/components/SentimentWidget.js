/**
 * SentimentWidget.js - Widget de Análise de Sentimento
 * 
 * Exibe análise de sentimento com:
 * - Gauge circular animado
 * - Score numérico (-100 a +100)
 * - Classificação (Positivo/Negativo/Neutro)
 * - Tags de nuances (ironia, sarcasmo, etc.)
 * - Histórico de análises anteriores
 * 
 * @module SentimentWidget
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class SentimentWidget {
    /**
     * Cria uma instância do SentimentWidget
     * @param {HTMLElement} container - Container do widget
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Dados
        this.sentimentData = null;

        // Configuração do gauge
        this.gaugeConfig = {
            radius: 80,
            strokeWidth: 12,
            animationDuration: 1500
        };

        // Bind methods
        this.render = this.render.bind(this);
        this.analyze = this.analyze.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças no sentimento
        this.state.subscribe('sentiment', (data) => {
            this.sentimentData = data;
            this.render();
        });

        // Render inicial
        this.render();
    }

    /**
     * Analisa sentimento do usuário atual
     */
    async analyze() {
        const username = this.state.get('currentUser');

        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        const loading = this.notifications.loading(`Analisando sentimento de @${username}...`);

        try {
            const result = await this.api.analyzeSentiment(username);

            if (result.success) {
                this.state.set('sentiment', result);
                loading.success('Análise de sentimento concluída!');
            } else {
                loading.error(result.error || 'Erro na análise');
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

        if (!this.sentimentData) {
            this.container.innerHTML = this.renderEmptyState();
            this.attachEventListeners();
            return;
        }

        this.container.innerHTML = this.renderSentimentWidget();
        this.attachEventListeners();

        // Animar gauge após render
        setTimeout(() => this.animateGauge(), 100);
    }

    /**
     * Renderiza estado vazio
     * @returns {string} HTML
     */
    renderEmptyState() {
        return `
            <div class="widget sentiment-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-smile"></i> Análise de Sentimento
                    </h3>
                </div>
                
                <div class="sentiment-empty">
                    <div class="sentiment-empty__icon">
                        <i class="fas fa-brain"></i>
                    </div>
                    <p>Clique para analisar o sentimento do perfil</p>
                    <button class="btn btn-primary" id="btn-analyze-sentiment">
                        <i class="fas fa-magic"></i>
                        Analisar Sentimento
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza widget com dados
     * @returns {string} HTML
     */
    renderSentimentWidget() {
        const data = this.sentimentData;
        const overall = data.overall_sentiment || {};

        // Score de -1 a 1, convertemos para 0 a 100
        const score = overall.compound || 0;
        const percentage = ((score + 1) / 2) * 100;

        // Classificação
        const classification = this.getClassification(score);

        // Nuances detectadas
        const nuances = data.nuances || [];

        // Dados de bio e posts
        const bioSentiment = data.bio_sentiment;
        const postsSentiment = data.posts_sentiment || [];

        return `
            <div class="widget sentiment-widget sentiment-widget--${classification.class}">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-smile"></i> Análise de Sentimento
                    </h3>
                    <div class="widget__actions">
                        <button class="widget__action-btn" id="btn-refresh-sentiment" title="Atualizar">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Gauge Principal -->
                <div class="sentiment-gauge">
                    <div class="gauge-container">
                        <svg viewBox="0 0 200 200" class="gauge-svg">
                            <!-- Fundo do gauge -->
                            <circle 
                                class="gauge-background" 
                                cx="100" 
                                cy="100" 
                                r="${this.gaugeConfig.radius}"
                                fill="none"
                                stroke-width="${this.gaugeConfig.strokeWidth}">
                            </circle>
                            
                            <!-- Preenchimento do gauge -->
                            <circle 
                                class="gauge-fill gauge-fill--${classification.class}" 
                                cx="100" 
                                cy="100" 
                                r="${this.gaugeConfig.radius}"
                                fill="none"
                                stroke-width="${this.gaugeConfig.strokeWidth}"
                                stroke-linecap="round"
                                stroke-dasharray="${this.calculateCircumference()}"
                                stroke-dashoffset="${this.calculateCircumference()}"
                                data-percentage="${percentage}">
                            </circle>
                        </svg>
                        
                        <!-- Valor central -->
                        <div class="gauge-value">
                            <div class="gauge-score" data-score="${(score * 100).toFixed(0)}">0</div>
                            <div class="gauge-label">${classification.label}</div>
                        </div>
                    </div>
                    
                    <!-- Indicadores -->
                    <div class="sentiment-indicators">
                        <div class="indicator indicator--negative">
                            <span class="indicator__label">Negativo</span>
                            <span class="indicator__value">${((overall.neg || 0) * 100).toFixed(1)}%</span>
                        </div>
                        <div class="indicator indicator--neutral">
                            <span class="indicator__label">Neutro</span>
                            <span class="indicator__value">${((overall.neu || 0) * 100).toFixed(1)}%</span>
                        </div>
                        <div class="indicator indicator--positive">
                            <span class="indicator__label">Positivo</span>
                            <span class="indicator__value">${((overall.pos || 0) * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
                
                <!-- Nuances Detectadas -->
                ${nuances.length > 0 ? `
                    <div class="sentiment-nuances">
                        <h4>
                            <i class="fas fa-theater-masks"></i>
                            Nuances Detectadas
                        </h4>
                        <div class="nuances-list">
                            ${nuances.map(nuance => this.renderNuanceTag(nuance)).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Bio Sentiment -->
                ${bioSentiment ? `
                    <div class="sentiment-section">
                        <h4>
                            <i class="fas fa-quote-left"></i>
                            Sentimento da Bio
                        </h4>
                        <div class="sentiment-bar-container">
                            <div class="sentiment-bar sentiment-bar--${this.getClassification(bioSentiment.compound).class}"
                                 style="width: ${((bioSentiment.compound + 1) / 2) * 100}%">
                            </div>
                        </div>
                        <span class="sentiment-bar-label">
                            ${(bioSentiment.compound * 100).toFixed(0)}%
                        </span>
                    </div>
                ` : ''}
                
                <!-- Posts Sentiment Overview -->
                ${postsSentiment.length > 0 ? `
                    <div class="sentiment-section">
                        <h4>
                            <i class="fas fa-images"></i>
                            Sentimento dos Posts (${postsSentiment.length} analisados)
                        </h4>
                        <div class="posts-sentiment-chart" id="posts-sentiment-chart">
                            ${this.renderPostsSentimentChart(postsSentiment)}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Timestamp -->
                <div class="widget__footer">
                    <small>
                        <i class="far fa-clock"></i>
                        Analisado em: ${this.formatDate(data.analyzed_at || new Date())}
                    </small>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza tag de nuance
     * @param {string|Object} nuance - Nuance
     * @returns {string} HTML
     */
    renderNuanceTag(nuance) {
        const name = typeof nuance === 'string' ? nuance : nuance.name;
        const confidence = typeof nuance === 'object' ? nuance.confidence : null;

        const iconMap = {
            'ironia': 'fa-theater-masks',
            'sarcasmo': 'fa-meh-rolling-eyes',
            'agressividade': 'fa-angry',
            'flerte': 'fa-heart',
            'entusiasmo': 'fa-grin-stars',
            'tristeza': 'fa-sad-tear',
            'humor': 'fa-laugh',
            'formal': 'fa-user-tie',
            'informal': 'fa-smile-wink'
        };

        const icon = iconMap[name.toLowerCase()] || 'fa-comment';

        return `
            <span class="nuance-tag nuance-tag--${name.toLowerCase()}">
                <i class="fas ${icon}"></i>
                ${name}
                ${confidence ? `<span class="nuance-confidence">${(confidence * 100).toFixed(0)}%</span>` : ''}
            </span>
        `;
    }

    /**
     * Renderiza gráfico de sentimento dos posts
     * @param {Array} posts - Sentimentos dos posts
     * @returns {string} HTML
     */
    renderPostsSentimentChart(posts) {
        // Mini sparkline dos últimos 20 posts
        const last20 = posts.slice(-20);

        if (last20.length === 0) return '<p>Sem dados</p>';

        const maxScore = 1;
        const minScore = -1;
        const range = maxScore - minScore;
        const barWidth = 100 / last20.length;

        const bars = last20.map((post, index) => {
            const score = post.compound || 0;
            const normalizedHeight = ((score - minScore) / range) * 100;
            const colorClass = this.getClassification(score).class;

            return `
                <div class="spark-bar spark-bar--${colorClass}" 
                     style="left: ${index * barWidth}%; width: ${barWidth - 1}%; height: ${normalizedHeight}%"
                     title="Post ${index + 1}: ${(score * 100).toFixed(0)}%">
                </div>
            `;
        }).join('');

        return `
            <div class="sparkline-container">
                <div class="sparkline-baseline"></div>
                ${bars}
            </div>
        `;
    }

    /**
     * Obtém classificação baseada no score
     * @param {number} score - Score de -1 a 1
     * @returns {Object}
     */
    getClassification(score) {
        if (score > 0.05) {
            return {
                class: 'positive',
                label: 'Positivo',
                color: '#28a745'
            };
        } else if (score < -0.05) {
            return {
                class: 'negative',
                label: 'Negativo',
                color: '#dc3545'
            };
        } else {
            return {
                class: 'neutral',
                label: 'Neutro',
                color: '#ffc107'
            };
        }
    }

    /**
     * Calcula circunferência do gauge
     * @returns {number}
     */
    calculateCircumference() {
        return 2 * Math.PI * this.gaugeConfig.radius;
    }

    /**
     * Anima o gauge
     */
    animateGauge() {
        const gaugeFill = this.container.querySelector('.gauge-fill');
        const scoreElement = this.container.querySelector('.gauge-score');

        if (!gaugeFill || !scoreElement) return;

        const percentage = parseFloat(gaugeFill.dataset.percentage) || 0;
        const targetScore = parseInt(scoreElement.dataset.score) || 0;
        const circumference = this.calculateCircumference();
        const offset = circumference - (percentage / 100) * circumference;

        // Animar stroke-dashoffset
        setTimeout(() => {
            gaugeFill.style.transition = `stroke-dashoffset ${this.gaugeConfig.animationDuration}ms ease-out`;
            gaugeFill.style.strokeDashoffset = offset;
        }, 50);

        // Animar contador
        this.animateCounter(scoreElement, 0, targetScore, this.gaugeConfig.animationDuration);
    }

    /**
     * Anima contador numérico
     * @param {HTMLElement} element - Elemento
     * @param {number} start - Valor inicial
     * @param {number} end - Valor final
     * @param {number} duration - Duração em ms
     */
    animateCounter(element, start, end, duration) {
        const startTime = performance.now();
        const diff = end - start;

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function (ease-out)
            const easeOut = 1 - Math.pow(1 - progress, 3);

            const current = Math.round(start + diff * easeOut);
            element.textContent = current + '%';

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Botão analisar
        const btnAnalyze = this.container.querySelector('#btn-analyze-sentiment');
        if (btnAnalyze) {
            btnAnalyze.addEventListener('click', () => this.analyze());
        }

        // Botão refresh
        const btnRefresh = this.container.querySelector('#btn-refresh-sentiment');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.analyze());
        }
    }

    /**
     * Formata data
     * @param {Date|string} date - Data
     * @returns {string}
     */
    formatDate(date) {
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
export function createSentimentWidget(container) {
    const widget = new SentimentWidget(container);
    widget.init();
    return widget;
}

export default SentimentWidget;
