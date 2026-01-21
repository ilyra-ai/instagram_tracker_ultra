/**
 * LoadingStates.js - Estados de Loading e Skeletons
 * 
 * Componentes de feedback visual durante carregamento:
 * - Skeleton loaders para cards
 * - Progress bar durante análise
 * - Animações de loading personalizadas
 * - Error states com retry button
 * 
 * @module LoadingStates
 * @version 1.0.0
 */

// Singleton instance
let instance = null;

export class LoadingStates {
    /**
     * Cria uma instância do LoadingStates
     */
    constructor() {
        if (instance) {
            return instance;
        }

        // Contadores de loading
        this.activeLoadings = new Map();

        // Container da progress bar global
        this.progressContainer = null;

        // Estado de progresso
        this.progressValue = 0;
        this.progressText = '';

        instance = this;
    }

    /**
     * Inicializa o componente
     */
    init() {
        this.injectStyles();
        this.createProgressBar();
    }

    // ==========================================================================
    // SKELETON LOADERS
    // ==========================================================================

    /**
     * Gera skeleton para card de perfil
     * @returns {string} HTML
     */
    skeletonProfileCard() {
        return `
            <div class="skeleton-card skeleton-profile">
                <div class="skeleton-header">
                    <div class="skeleton-avatar skeleton-animate"></div>
                    <div class="skeleton-info">
                        <div class="skeleton-text skeleton-text--title skeleton-animate"></div>
                        <div class="skeleton-text skeleton-text--subtitle skeleton-animate"></div>
                    </div>
                </div>
                <div class="skeleton-stats">
                    <div class="skeleton-stat skeleton-animate"></div>
                    <div class="skeleton-stat skeleton-animate"></div>
                    <div class="skeleton-stat skeleton-animate"></div>
                </div>
                <div class="skeleton-bio">
                    <div class="skeleton-text skeleton-animate"></div>
                    <div class="skeleton-text skeleton-animate"></div>
                    <div class="skeleton-text skeleton-text--short skeleton-animate"></div>
                </div>
            </div>
        `;
    }

    /**
     * Gera skeleton para widget
     * @param {string} type - Tipo de widget
     * @returns {string} HTML
     */
    skeletonWidget(type = 'default') {
        const skeletons = {
            'chart': this.skeletonChart(),
            'list': this.skeletonList(),
            'gauge': this.skeletonGauge(),
            'map': this.skeletonMap(),
            'graph': this.skeletonGraph(),
            'default': this.skeletonDefault()
        };

        return skeletons[type] || skeletons.default;
    }

    /**
     * Skeleton para gráfico
     * @returns {string} HTML
     */
    skeletonChart() {
        return `
            <div class="skeleton-card skeleton-chart">
                <div class="skeleton-header-row">
                    <div class="skeleton-text skeleton-text--title skeleton-animate"></div>
                    <div class="skeleton-icon skeleton-animate"></div>
                </div>
                <div class="skeleton-chart-area">
                    <div class="skeleton-bars">
                        ${Array(7).fill('').map(() => `
                            <div class="skeleton-bar skeleton-animate" style="height: ${30 + Math.random() * 70}%"></div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Skeleton para lista
     * @param {number} items - Número de itens
     * @returns {string} HTML
     */
    skeletonList(items = 5) {
        return `
            <div class="skeleton-card skeleton-list">
                <div class="skeleton-header-row">
                    <div class="skeleton-text skeleton-text--title skeleton-animate"></div>
                </div>
                <div class="skeleton-list-items">
                    ${Array(items).fill('').map(() => `
                        <div class="skeleton-list-item">
                            <div class="skeleton-thumbnail skeleton-animate"></div>
                            <div class="skeleton-item-content">
                                <div class="skeleton-text skeleton-animate"></div>
                                <div class="skeleton-text skeleton-text--short skeleton-animate"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Skeleton para gauge
     * @returns {string} HTML
     */
    skeletonGauge() {
        return `
            <div class="skeleton-card skeleton-gauge">
                <div class="skeleton-header-row">
                    <div class="skeleton-text skeleton-text--title skeleton-animate"></div>
                </div>
                <div class="skeleton-gauge-container">
                    <div class="skeleton-gauge-circle skeleton-animate"></div>
                    <div class="skeleton-gauge-value skeleton-animate"></div>
                </div>
                <div class="skeleton-gauge-label skeleton-animate"></div>
            </div>
        `;
    }

    /**
     * Skeleton para mapa
     * @returns {string} HTML
     */
    skeletonMap() {
        return `
            <div class="skeleton-card skeleton-map">
                <div class="skeleton-header-row">
                    <div class="skeleton-text skeleton-text--title skeleton-animate"></div>
                </div>
                <div class="skeleton-map-area skeleton-animate">
                    <div class="skeleton-map-loader">
                        <i class="fas fa-map-marked-alt"></i>
                        <span>Carregando mapa...</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Skeleton para grafo
     * @returns {string} HTML
     */
    skeletonGraph() {
        return `
            <div class="skeleton-card skeleton-graph">
                <div class="skeleton-header-row">
                    <div class="skeleton-text skeleton-text--title skeleton-animate"></div>
                </div>
                <div class="skeleton-graph-area skeleton-animate">
                    <div class="skeleton-graph-loader">
                        <div class="skeleton-nodes">
                            ${Array(6).fill('').map((_, i) => `
                                <div class="skeleton-node" style="--delay: ${i * 0.1}s"></div>
                            `).join('')}
                        </div>
                        <span>Construindo grafo...</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Skeleton padrão
     * @returns {string} HTML
     */
    skeletonDefault() {
        return `
            <div class="skeleton-card">
                <div class="skeleton-header-row">
                    <div class="skeleton-text skeleton-text--title skeleton-animate"></div>
                    <div class="skeleton-icon skeleton-animate"></div>
                </div>
                <div class="skeleton-content">
                    <div class="skeleton-text skeleton-animate"></div>
                    <div class="skeleton-text skeleton-animate"></div>
                    <div class="skeleton-text skeleton-text--short skeleton-animate"></div>
                </div>
            </div>
        `;
    }

    /**
     * Aplica skeleton a um container
     * @param {HTMLElement|string} container - Container ou seletor
     * @param {string} type - Tipo de skeleton
     */
    showSkeleton(container, type = 'default') {
        const el = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!el) return;

        el.innerHTML = this.skeletonWidget(type);
        el.classList.add('is-loading');
    }

    /**
     * Remove skeleton de um container
     * @param {HTMLElement|string} container - Container ou seletor
     */
    hideSkeleton(container) {
        const el = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!el) return;

        el.classList.remove('is-loading');
        // O conteúdo será substituído pelo componente real
    }

    // ==========================================================================
    // PROGRESS BAR
    // ==========================================================================

    /**
     * Cria progress bar global
     */
    createProgressBar() {
        if (document.getElementById('global-progress')) return;

        const container = document.createElement('div');
        container.id = 'global-progress';
        container.className = 'global-progress';
        container.innerHTML = `
            <div class="global-progress__track">
                <div class="global-progress__bar"></div>
            </div>
            <div class="global-progress__info">
                <span class="global-progress__text"></span>
                <span class="global-progress__percentage">0%</span>
            </div>
        `;

        document.body.appendChild(container);
        this.progressContainer = container;
    }

    /**
     * Mostra progress bar
     * @param {string} text - Texto de status
     */
    showProgress(text = 'Carregando...') {
        if (!this.progressContainer) {
            this.createProgressBar();
        }

        this.progressValue = 0;
        this.progressText = text;
        this.updateProgress(0, text);
        this.progressContainer.classList.add('global-progress--active');
    }

    /**
     * Atualiza progress bar
     * @param {number} value - Valor (0-100)
     * @param {string} text - Texto de status
     */
    updateProgress(value, text = null) {
        if (!this.progressContainer) return;

        this.progressValue = Math.min(100, Math.max(0, value));
        if (text) this.progressText = text;

        const bar = this.progressContainer.querySelector('.global-progress__bar');
        const textEl = this.progressContainer.querySelector('.global-progress__text');
        const percentEl = this.progressContainer.querySelector('.global-progress__percentage');

        if (bar) bar.style.width = `${this.progressValue}%`;
        if (textEl) textEl.textContent = this.progressText;
        if (percentEl) percentEl.textContent = `${Math.round(this.progressValue)}%`;
    }

    /**
     * Oculta progress bar
     */
    hideProgress() {
        if (!this.progressContainer) return;

        // Completar antes de esconder
        this.updateProgress(100);

        setTimeout(() => {
            this.progressContainer.classList.remove('global-progress--active');
        }, 300);
    }

    /**
     * Simula progresso automático
     * @param {number} duration - Duração em ms
     * @param {string} text - Texto
     * @returns {Function} Função para completar
     */
    simulateProgress(duration = 3000, text = 'Processando...') {
        this.showProgress(text);

        let progress = 0;
        const increment = 100 / (duration / 50);

        const interval = setInterval(() => {
            progress += increment * (1 - progress / 100);
            if (progress >= 90) {
                clearInterval(interval);
            } else {
                this.updateProgress(progress);
            }
        }, 50);

        // Retorna função para completar
        return () => {
            clearInterval(interval);
            this.hideProgress();
        };
    }

    // ==========================================================================
    // LOADING SPINNERS
    // ==========================================================================

    /**
     * Gera spinner de loading
     * @param {string} size - Tamanho (sm, md, lg)
     * @param {string} variant - Variante (default, pulse, dots, ring)
     * @returns {string} HTML
     */
    spinner(size = 'md', variant = 'default') {
        const sizeClass = `loading-spinner--${size}`;

        switch (variant) {
            case 'pulse':
                return `
                    <div class="loading-spinner loading-spinner--pulse ${sizeClass}">
                        <div class="pulse-ring"></div>
                        <div class="pulse-ring"></div>
                        <div class="pulse-ring"></div>
                    </div>
                `;

            case 'dots':
                return `
                    <div class="loading-spinner loading-spinner--dots ${sizeClass}">
                        <span class="dot"></span>
                        <span class="dot"></span>
                        <span class="dot"></span>
                    </div>
                `;

            case 'ring':
                return `
                    <div class="loading-spinner loading-spinner--ring ${sizeClass}">
                        <svg viewBox="0 0 50 50">
                            <circle cx="25" cy="25" r="20" fill="none" stroke-width="4"/>
                        </svg>
                    </div>
                `;

            default:
                return `
                    <div class="loading-spinner ${sizeClass}">
                        <i class="fas fa-spinner fa-spin"></i>
                    </div>
                `;
        }
    }

    /**
     * Gera overlay de loading
     * @param {string} text - Texto
     * @param {string} variant - Variante do spinner
     * @returns {string} HTML
     */
    overlay(text = 'Carregando...', variant = 'ring') {
        return `
            <div class="loading-overlay">
                <div class="loading-overlay__content">
                    ${this.spinner('lg', variant)}
                    <span class="loading-overlay__text">${text}</span>
                </div>
            </div>
        `;
    }

    /**
     * Adiciona overlay a um container
     * @param {HTMLElement|string} container - Container
     * @param {string} text - Texto
     */
    showOverlay(container, text = 'Carregando...') {
        const el = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!el) return;

        // Verificar se já tem overlay
        if (el.querySelector('.loading-overlay')) return;

        el.style.position = 'relative';
        el.insertAdjacentHTML('beforeend', this.overlay(text));
    }

    /**
     * Remove overlay de um container
     * @param {HTMLElement|string} container - Container
     */
    hideOverlay(container) {
        const el = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!el) return;

        const overlay = el.querySelector('.loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    // ==========================================================================
    // ERROR STATES
    // ==========================================================================

    /**
     * Gera estado de erro
     * @param {Object} options - Opções
     * @returns {string} HTML
     */
    errorState(options = {}) {
        const {
            title = 'Erro ao carregar',
            message = 'Ocorreu um erro inesperado. Tente novamente.',
            icon = 'fas fa-exclamation-triangle',
            retryable = true,
            retryText = 'Tentar Novamente',
            retryCallback = null
        } = options;

        return `
            <div class="error-state">
                <div class="error-state__icon">
                    <i class="${icon}"></i>
                </div>
                <h4 class="error-state__title">${title}</h4>
                <p class="error-state__message">${message}</p>
                ${retryable ? `
                    <button class="error-state__retry btn btn-primary" ${retryCallback ? `onclick="${retryCallback}"` : ''}>
                        <i class="fas fa-redo"></i>
                        ${retryText}
                    </button>
                ` : ''}
            </div>
        `;
    }

    /**
     * Gera estado vazio
     * @param {Object} options - Opções
     * @returns {string} HTML
     */
    emptyState(options = {}) {
        const {
            title = 'Nenhum dado encontrado',
            message = 'Não há dados para exibir no momento.',
            icon = 'fas fa-inbox',
            actionText = null,
            actionCallback = null
        } = options;

        return `
            <div class="empty-state">
                <div class="empty-state__icon">
                    <i class="${icon}"></i>
                </div>
                <h4 class="empty-state__title">${title}</h4>
                <p class="empty-state__message">${message}</p>
                ${actionText ? `
                    <button class="empty-state__action btn btn-outline" ${actionCallback ? `onclick="${actionCallback}"` : ''}>
                        ${actionText}
                    </button>
                ` : ''}
            </div>
        `;
    }

    /**
     * Mostra erro em container
     * @param {HTMLElement|string} container - Container
     * @param {Object} options - Opções
     */
    showError(container, options = {}) {
        const el = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!el) return;

        el.innerHTML = this.errorState(options);
        el.classList.remove('is-loading');
        el.classList.add('has-error');
    }

    /**
     * Mostra estado vazio em container
     * @param {HTMLElement|string} container - Container
     * @param {Object} options - Opções
     */
    showEmpty(container, options = {}) {
        const el = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!el) return;

        el.innerHTML = this.emptyState(options);
        el.classList.remove('is-loading');
        el.classList.add('is-empty');
    }

    // ==========================================================================
    // ESTILOS CSS
    // ==========================================================================

    /**
     * Injeta estilos CSS
     */
    injectStyles() {
        if (document.getElementById('loading-states-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'loading-states-styles';
        styles.textContent = `
            /* Skeleton Animation */
            @keyframes skeleton-pulse {
                0% { opacity: 1; }
                50% { opacity: 0.4; }
                100% { opacity: 1; }
            }
            
            .skeleton-animate {
                animation: skeleton-pulse 1.5s ease-in-out infinite;
                background: linear-gradient(90deg, var(--skeleton-base, #e0e0e0) 25%, var(--skeleton-shine, #f5f5f5) 50%, var(--skeleton-base, #e0e0e0) 75%);
                background-size: 200% 100%;
            }
            
            /* Skeleton Card */
            .skeleton-card {
                padding: var(--space-4, 1rem);
                border-radius: var(--radius-lg, 12px);
                background: var(--bg-card, #fff);
            }
            
            .skeleton-avatar {
                width: 60px;
                height: 60px;
                border-radius: 50%;
            }
            
            .skeleton-text {
                height: 16px;
                border-radius: 4px;
                margin-bottom: 8px;
            }
            
            .skeleton-text--title {
                width: 60%;
                height: 20px;
            }
            
            .skeleton-text--subtitle {
                width: 40%;
            }
            
            .skeleton-text--short {
                width: 30%;
            }
            
            /* Progress Bar */
            .global-progress {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 9999;
                padding: 0;
                opacity: 0;
                transform: translateY(-100%);
                transition: all 0.3s ease;
            }
            
            .global-progress--active {
                opacity: 1;
                transform: translateY(0);
            }
            
            .global-progress__track {
                height: 4px;
                background: var(--progress-bg, rgba(0,0,0,0.1));
            }
            
            .global-progress__bar {
                height: 100%;
                background: linear-gradient(90deg, var(--primary, #3b82f6), var(--primary-light, #60a5fa));
                width: 0%;
                transition: width 0.3s ease;
            }
            
            .global-progress__info {
                display: flex;
                justify-content: space-between;
                padding: 4px 12px;
                font-size: 12px;
                color: var(--text-secondary, #666);
                background: var(--bg-secondary, #f5f5f5);
            }
            
            /* Loading Spinners */
            .loading-spinner {
                display: inline-flex;
                align-items: center;
                justify-content: center;
            }
            
            .loading-spinner--sm { font-size: 14px; }
            .loading-spinner--md { font-size: 24px; }
            .loading-spinner--lg { font-size: 48px; }
            
            .loading-spinner--dots .dot {
                display: inline-block;
                width: 8px;
                height: 8px;
                margin: 0 2px;
                background: var(--primary, #3b82f6);
                border-radius: 50%;
                animation: dot-bounce 1.4s infinite ease-in-out both;
            }
            
            .loading-spinner--dots .dot:nth-child(1) { animation-delay: -0.32s; }
            .loading-spinner--dots .dot:nth-child(2) { animation-delay: -0.16s; }
            
            @keyframes dot-bounce {
                0%, 80%, 100% { transform: scale(0); }
                40% { transform: scale(1); }
            }
            
            .loading-spinner--ring svg circle {
                stroke: var(--primary, #3b82f6);
                stroke-linecap: round;
                stroke-dasharray: 90, 150;
                stroke-dashoffset: 0;
                animation: ring-rotate 1.5s ease-in-out infinite, ring-dash 1.5s ease-in-out infinite;
                transform-origin: center;
            }
            
            @keyframes ring-rotate {
                100% { transform: rotate(360deg); }
            }
            
            @keyframes ring-dash {
                0% { stroke-dasharray: 1, 150; stroke-dashoffset: 0; }
                50% { stroke-dasharray: 90, 150; stroke-dashoffset: -35px; }
                100% { stroke-dasharray: 90, 150; stroke-dashoffset: -124px; }
            }
            
            /* Loading Overlay */
            .loading-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(2px);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 100;
            }
            
            .loading-overlay__content {
                text-align: center;
            }
            
            .loading-overlay__text {
                display: block;
                margin-top: 12px;
                color: var(--text-secondary, #666);
            }
            
            /* Error State */
            .error-state,
            .empty-state {
                padding: var(--space-6, 1.5rem);
                text-align: center;
            }
            
            .error-state__icon,
            .empty-state__icon {
                font-size: 48px;
                color: var(--error, #ef4444);
                margin-bottom: var(--space-4, 1rem);
            }
            
            .empty-state__icon {
                color: var(--text-muted, #9ca3af);
            }
            
            .error-state__title,
            .empty-state__title {
                margin: 0 0 var(--space-2, 0.5rem);
                font-size: 18px;
            }
            
            .error-state__message,
            .empty-state__message {
                color: var(--text-secondary, #666);
                margin: 0 0 var(--space-4, 1rem);
            }
            
            .error-state__retry,
            .empty-state__action {
                margin-top: var(--space-2, 0.5rem);
            }
        `;

        document.head.appendChild(styles);
    }
}

/**
 * Obtém instância singleton do LoadingStates
 * @returns {LoadingStates}
 */
export function getLoadingStates() {
    if (!instance) {
        instance = new LoadingStates();
        instance.init();
    }
    return instance;
}

export default LoadingStates;
