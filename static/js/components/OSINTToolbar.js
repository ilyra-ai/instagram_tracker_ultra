/**
 * OSINTToolbar.js - Barra de Ferramentas OSINT
 * 
 * Fornece controles para funcionalidades OSINT:
 * - Account Health Check (shadowban)
 * - Device Fingerprinting
 * - Location Analysis
 * - Breach Check
 * - Cross-Platform Search
 * - Social Connections Analysis
 * 
 * @module OSINTToolbar
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class OSINTToolbar {
    /**
     * Cria uma instância do OSINTToolbar
     * @param {HTMLElement} container - Container do toolbar
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Resultados OSINT
        this.results = {
            healthCheck: null,
            deviceFingerprint: null,
            locationAnalysis: null,
            breachCheck: null,
            crossPlatform: null,
            socialConnections: null
        };

        // Estado de loading por ferramenta
        this.loadingStates = {};

        // Definição das ferramentas OSINT
        this.osintTools = [
            {
                id: 'health-check',
                name: 'Account Health',
                icon: 'fa-heartbeat',
                description: 'Verifica shadowban, restrições e status da conta',
                color: '#28a745',
                action: 'runHealthCheck'
            },
            {
                id: 'device-fingerprint',
                name: 'Device Fingerprint',
                icon: 'fa-mobile-alt',
                description: 'Analisa dispositivos usados para acessar a conta',
                color: '#667eea',
                action: 'runDeviceFingerprint'
            },
            {
                id: 'location-analysis',
                name: 'Análise de Locais',
                icon: 'fa-map-marker-alt',
                description: 'Extrai e analisa localizações de posts e metadados',
                color: '#ff9800',
                action: 'runLocationAnalysis'
            },
            {
                id: 'breach-check',
                name: 'Breach Check',
                icon: 'fa-shield-alt',
                description: 'Verifica vazamentos em bases de dados públicas',
                color: '#dc3545',
                action: 'runBreachCheck'
            },
            {
                id: 'cross-platform',
                name: 'Cross-Platform',
                icon: 'fa-globe',
                description: 'Busca perfis em outras redes sociais',
                color: '#9c27b0',
                action: 'runCrossPlatform'
            },
            {
                id: 'social-connections',
                name: 'Conexões Sociais',
                icon: 'fa-users',
                description: 'Analisa padrões de conexões e interações',
                color: '#2196f3',
                action: 'runSocialConnections'
            }
        ];

        // Bind methods
        this.render = this.render.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças nos resultados OSINT
        this.state.subscribe('osintResults', (data) => {
            if (data) {
                Object.assign(this.results, data);
                this.updateResultsDisplay();
            }
        });

        // Render inicial
        this.render();
    }

    /**
     * Renderiza o toolbar
     */
    render() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="osint-toolbar">
                <div class="toolbar-header">
                    <h3>
                        <i class="fas fa-user-secret"></i>
                        OSINT Toolkit
                    </h3>
                    <span class="toolbar-subtitle">Ferramentas de Investigação</span>
                </div>
                
                <!-- Grid de Ferramentas -->
                <div class="osint-tools-grid">
                    ${this.osintTools.map(tool => this.renderToolCard(tool)).join('')}
                </div>
                
                <!-- Área de Resultados -->
                <div class="osint-results" id="osint-results">
                    ${this.renderResultsArea()}
                </div>
                
                <!-- Botão Executar Tudo -->
                <div class="osint-actions">
                    <button class="btn btn-primary btn-lg" id="btn-run-all-osint">
                        <i class="fas fa-play"></i>
                        Executar Análise Completa
                    </button>
                    <button class="btn btn-secondary" id="btn-export-osint">
                        <i class="fas fa-download"></i>
                        Exportar Relatório
                    </button>
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    /**
     * Renderiza card de ferramenta
     * @param {Object} tool - Definição da ferramenta
     * @returns {string} HTML
     */
    renderToolCard(tool) {
        const isLoading = this.loadingStates[tool.id];
        const hasResult = this.results[this.getResultKey(tool.id)];

        return `
            <div class="osint-tool-card" 
                 data-tool="${tool.id}"
                 style="--tool-color: ${tool.color}">
                <div class="tool-card__icon">
                    ${isLoading ?
                '<i class="fas fa-spinner fa-spin"></i>' :
                `<i class="fas ${tool.icon}"></i>`}
                </div>
                <div class="tool-card__content">
                    <h4>${tool.name}</h4>
                    <p>${tool.description}</p>
                </div>
                <div class="tool-card__status">
                    ${hasResult ?
                '<span class="status-badge status-badge--success"><i class="fas fa-check"></i></span>' :
                '<span class="status-badge status-badge--pending"><i class="fas fa-clock"></i></span>'}
                </div>
                <button class="tool-card__action" 
                        title="Executar ${tool.name}"
                        data-action="${tool.action}"
                        ${isLoading ? 'disabled' : ''}>
                    <i class="fas fa-play"></i>
                </button>
            </div>
        `;
    }

    /**
     * Renderiza área de resultados
     * @returns {string} HTML
     */
    renderResultsArea() {
        const hasAnyResult = Object.values(this.results).some(r => r !== null);

        if (!hasAnyResult) {
            return `
                <div class="osint-results-empty">
                    <i class="fas fa-search"></i>
                    <p>Execute as ferramentas OSINT para ver os resultados</p>
                </div>
            `;
        }

        let html = '<div class="osint-results-content">';

        // Health Check
        if (this.results.healthCheck) {
            html += this.renderHealthCheckResult(this.results.healthCheck);
        }

        // Device Fingerprint
        if (this.results.deviceFingerprint) {
            html += this.renderDeviceFingerprintResult(this.results.deviceFingerprint);
        }

        // Location Analysis
        if (this.results.locationAnalysis) {
            html += this.renderLocationResult(this.results.locationAnalysis);
        }

        // Breach Check
        if (this.results.breachCheck) {
            html += this.renderBreachCheckResult(this.results.breachCheck);
        }

        // Cross Platform
        if (this.results.crossPlatform) {
            html += this.renderCrossPlatformResult(this.results.crossPlatform);
        }

        // Social Connections
        if (this.results.socialConnections) {
            html += this.renderSocialConnectionsResult(this.results.socialConnections);
        }

        html += '</div>';
        return html;
    }

    /**
     * Renderiza resultado do Health Check
     * @param {Object} data - Dados do resultado
     * @returns {string} HTML
     */
    renderHealthCheckResult(data) {
        const statusClass = data.is_healthy ? 'healthy' : 'warning';
        const statusIcon = data.is_healthy ? 'fa-check-circle' : 'fa-exclamation-triangle';
        const statusText = data.is_healthy ? 'Conta Saudável' : 'Possíveis Restrições';

        return `
            <div class="result-card result-card--health">
                <div class="result-card__header">
                    <i class="fas fa-heartbeat"></i>
                    <h4>Account Health</h4>
                    <span class="health-status health-status--${statusClass}">
                        <i class="fas ${statusIcon}"></i>
                        ${statusText}
                    </span>
                </div>
                <div class="result-card__body">
                    <div class="health-metrics">
                        ${data.checks ? data.checks.map(check => `
                            <div class="health-metric">
                                <span class="metric-name">${check.name}</span>
                                <span class="metric-status metric-status--${check.passed ? 'pass' : 'fail'}">
                                    <i class="fas ${check.passed ? 'fa-check' : 'fa-times'}"></i>
                                </span>
                            </div>
                        `).join('') : ''}
                    </div>
                    ${data.warnings && data.warnings.length > 0 ? `
                        <div class="health-warnings">
                            <h5><i class="fas fa-exclamation-triangle"></i> Alertas</h5>
                            <ul>
                                ${data.warnings.map(w => `<li>${this.escapeHtml(w)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Renderiza resultado do Device Fingerprint
     * @param {Object} data - Dados do resultado
     * @returns {string} HTML
     */
    renderDeviceFingerprintResult(data) {
        const devices = data.devices || [];

        return `
            <div class="result-card result-card--devices">
                <div class="result-card__header">
                    <i class="fas fa-mobile-alt"></i>
                    <h4>Device Fingerprint</h4>
                    <span class="device-count">${devices.length} dispositivo(s)</span>
                </div>
                <div class="result-card__body">
                    <div class="devices-list">
                        ${devices.map(device => `
                            <div class="device-item">
                                <div class="device-icon">
                                    <i class="fas ${this.getDeviceIcon(device.type)}"></i>
                                </div>
                                <div class="device-info">
                                    <span class="device-name">${this.escapeHtml(device.name || device.model)}</span>
                                    <span class="device-os">${this.escapeHtml(device.os || 'Desconhecido')}</span>
                                </div>
                                <div class="device-meta">
                                    ${device.last_seen ? `
                                        <span class="device-date">
                                            <i class="far fa-clock"></i>
                                            ${this.formatDate(device.last_seen)}
                                        </span>
                                    ` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza resultado da análise de localizações
     * @param {Object} data - Dados do resultado
     * @returns {string} HTML
     */
    renderLocationResult(data) {
        const locations = data.locations || [];
        const summary = data.summary || {};

        return `
            <div class="result-card result-card--locations">
                <div class="result-card__header">
                    <i class="fas fa-map-marker-alt"></i>
                    <h4>Análise de Locais</h4>
                    <span class="location-count">${locations.length} local(is)</span>
                </div>
                <div class="result-card__body">
                    ${summary.most_frequent ? `
                        <div class="location-highlight">
                            <span class="highlight-label">Local mais frequente:</span>
                            <span class="highlight-value">${this.escapeHtml(summary.most_frequent)}</span>
                        </div>
                    ` : ''}
                    ${summary.countries && summary.countries.length > 0 ? `
                        <div class="location-countries">
                            <span class="countries-label">Países:</span>
                            ${summary.countries.map(c => `<span class="country-tag">${this.escapeHtml(c)}</span>`).join('')}
                        </div>
                    ` : ''}
                    <div class="locations-mini-list">
                        ${locations.slice(0, 5).map(loc => `
                            <div class="location-mini-item">
                                <i class="fas fa-map-pin"></i>
                                <span>${this.escapeHtml(loc.name || loc.city)}</span>
                            </div>
                        `).join('')}
                        ${locations.length > 5 ? `<span class="more-count">+${locations.length - 5} mais</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza resultado do Breach Check
     * @param {Object} data - Dados do resultado
     * @returns {string} HTML
     */
    renderBreachCheckResult(data) {
        const breaches = data.breaches || [];
        const isCompromised = breaches.length > 0;

        return `
            <div class="result-card result-card--breach ${isCompromised ? 'result-card--danger' : ''}">
                <div class="result-card__header">
                    <i class="fas fa-shield-alt"></i>
                    <h4>Breach Check</h4>
                    <span class="breach-status breach-status--${isCompromised ? 'danger' : 'safe'}">
                        <i class="fas ${isCompromised ? 'fa-exclamation-triangle' : 'fa-check-circle'}"></i>
                        ${isCompromised ? `${breaches.length} vazamento(s)` : 'Nenhum vazamento'}
                    </span>
                </div>
                <div class="result-card__body">
                    ${isCompromised ? `
                        <div class="breaches-list">
                            ${breaches.map(breach => `
                                <div class="breach-item">
                                    <span class="breach-name">${this.escapeHtml(breach.name)}</span>
                                    <span class="breach-date">${this.formatDate(breach.date)}</span>
                                    ${breach.data_types ? `
                                        <div class="breach-types">
                                            ${breach.data_types.map(t => `<span class="type-tag">${t}</span>`).join('')}
                                        </div>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    ` : `
                        <p class="safe-message">
                            <i class="fas fa-check"></i>
                            Nenhum vazamento encontrado nas bases de dados verificadas
                        </p>
                    `}
                </div>
            </div>
        `;
    }

    /**
     * Renderiza resultado do Cross-Platform
     * @param {Object} data - Dados do resultado
     * @returns {string} HTML
     */
    renderCrossPlatformResult(data) {
        const profiles = data.profiles || [];
        const found = profiles.filter(p => p.found);

        return `
            <div class="result-card result-card--crossplatform">
                <div class="result-card__header">
                    <i class="fas fa-globe"></i>
                    <h4>Cross-Platform</h4>
                    <span class="platform-count">${found.length} perfil(is) encontrado(s)</span>
                </div>
                <div class="result-card__body">
                    <div class="platforms-grid">
                        ${profiles.slice(0, 12).map(profile => `
                            <div class="platform-item platform-item--${profile.found ? 'found' : 'notfound'}">
                                <i class="fab ${this.getPlatformIcon(profile.platform)}"></i>
                                <span class="platform-name">${profile.platform}</span>
                                ${profile.found && profile.url ? `
                                    <a href="${profile.url}" target="_blank" class="platform-link">
                                        <i class="fas fa-external-link-alt"></i>
                                    </a>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza resultado das Conexões Sociais
     * @param {Object} data - Dados do resultado
     * @returns {string} HTML
     */
    renderSocialConnectionsResult(data) {
        const topConnections = data.top_connections || [];
        const stats = data.stats || {};

        return `
            <div class="result-card result-card--connections">
                <div class="result-card__header">
                    <i class="fas fa-users"></i>
                    <h4>Conexões Sociais</h4>
                </div>
                <div class="result-card__body">
                    <div class="connections-stats">
                        <div class="stat-item">
                            <span class="stat-value">${stats.mutual_count || 0}</span>
                            <span class="stat-label">Mútuos</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${stats.top_interactors || 0}</span>
                            <span class="stat-label">Top Interações</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${stats.communities || 0}</span>
                            <span class="stat-label">Comunidades</span>
                        </div>
                    </div>
                    ${topConnections.length > 0 ? `
                        <div class="top-connections">
                            <h5>Principais Conexões</h5>
                            <div class="connections-list">
                                ${topConnections.slice(0, 5).map(conn => `
                                    <div class="connection-item">
                                        <span class="connection-name">@${this.escapeHtml(conn.username)}</span>
                                        <span class="connection-score">${conn.score || conn.interactions}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // ==========================================================================
    // ACTIONS - Execução das ferramentas OSINT
    // ==========================================================================

    /**
     * Executa Health Check
     */
    async runHealthCheck() {
        const username = this.state.get('currentUser');
        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        this.setLoading('health-check', true);

        try {
            const result = await this.api.osintHealthCheck(username);
            if (result.success) {
                this.results.healthCheck = result;
                this.updateResultsDisplay();
                this.notifications.success('Health Check concluído!');
            } else {
                this.notifications.error(result.error || 'Erro no Health Check');
            }
        } catch (error) {
            this.notifications.error(`Erro: ${error.message}`);
        } finally {
            this.setLoading('health-check', false);
        }
    }

    /**
     * Executa Device Fingerprint
     */
    async runDeviceFingerprint() {
        const username = this.state.get('currentUser');
        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        this.setLoading('device-fingerprint', true);

        try {
            const result = await this.api.osintDeviceFingerprint(username);
            if (result.success) {
                this.results.deviceFingerprint = result;
                this.updateResultsDisplay();
                this.notifications.success('Device Fingerprint concluído!');
            } else {
                this.notifications.error(result.error || 'Erro no Device Fingerprint');
            }
        } catch (error) {
            this.notifications.error(`Erro: ${error.message}`);
        } finally {
            this.setLoading('device-fingerprint', false);
        }
    }

    /**
     * Executa Location Analysis
     */
    async runLocationAnalysis() {
        const username = this.state.get('currentUser');
        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        this.setLoading('location-analysis', true);

        try {
            const result = await this.api.osintLocationAnalysis(username);
            if (result.success) {
                this.results.locationAnalysis = result;
                this.state.set('locations', result.locations);
                this.updateResultsDisplay();
                this.notifications.success('Análise de Locais concluída!');
            } else {
                this.notifications.error(result.error || 'Erro na Análise de Locais');
            }
        } catch (error) {
            this.notifications.error(`Erro: ${error.message}`);
        } finally {
            this.setLoading('location-analysis', false);
        }
    }

    /**
     * Executa Breach Check
     */
    async runBreachCheck() {
        const username = this.state.get('currentUser');
        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        this.setLoading('breach-check', true);

        try {
            const result = await this.api.osintBreachCheck(username);
            if (result.success) {
                this.results.breachCheck = result;
                this.updateResultsDisplay();
                this.notifications.success('Breach Check concluído!');
            } else {
                this.notifications.error(result.error || 'Erro no Breach Check');
            }
        } catch (error) {
            this.notifications.error(`Erro: ${error.message}`);
        } finally {
            this.setLoading('breach-check', false);
        }
    }

    /**
     * Executa Cross-Platform Search
     */
    async runCrossPlatform() {
        const username = this.state.get('currentUser');
        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        this.setLoading('cross-platform', true);

        try {
            const result = await this.api.osintCrossPlatform(username);
            if (result.success) {
                this.results.crossPlatform = result;
                this.updateResultsDisplay();
                this.notifications.success('Cross-Platform concluído!');
            } else {
                this.notifications.error(result.error || 'Erro no Cross-Platform');
            }
        } catch (error) {
            this.notifications.error(`Erro: ${error.message}`);
        } finally {
            this.setLoading('cross-platform', false);
        }
    }

    /**
     * Executa Social Connections Analysis
     */
    async runSocialConnections() {
        const username = this.state.get('currentUser');
        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        this.setLoading('social-connections', true);

        try {
            const result = await this.api.osintSocialConnections(username);
            if (result.success) {
                this.results.socialConnections = result;
                this.updateResultsDisplay();
                this.notifications.success('Conexões Sociais concluído!');
            } else {
                this.notifications.error(result.error || 'Erro nas Conexões Sociais');
            }
        } catch (error) {
            this.notifications.error(`Erro: ${error.message}`);
        } finally {
            this.setLoading('social-connections', false);
        }
    }

    /**
     * Executa todas as ferramentas OSINT
     */
    async runAllOsint() {
        const username = this.state.get('currentUser');
        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        const loading = this.notifications.loading('Executando análise OSINT completa...');

        try {
            // Executar em paralelo
            await Promise.all([
                this.runHealthCheck(),
                this.runDeviceFingerprint(),
                this.runLocationAnalysis(),
                this.runBreachCheck(),
                this.runCrossPlatform(),
                this.runSocialConnections()
            ]);

            loading.success('Análise OSINT completa concluída!');
        } catch (error) {
            loading.error(`Erro: ${error.message}`);
        }
    }

    /**
     * Exporta relatório OSINT
     */
    exportReport() {
        const username = this.state.get('currentUser') || 'unknown';

        const report = {
            exportedAt: new Date().toISOString(),
            targetUser: username,
            results: this.results
        };

        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `osint-report-${username}-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.notifications.success('Relatório OSINT exportado!');
    }

    // ==========================================================================
    // HELPERS
    // ==========================================================================

    /**
     * Define estado de loading
     * @param {string} toolId - ID da ferramenta
     * @param {boolean} isLoading - Estado
     */
    setLoading(toolId, isLoading) {
        this.loadingStates[toolId] = isLoading;
        this.updateToolCard(toolId);
    }

    /**
     * Atualiza card de ferramenta
     * @param {string} toolId - ID da ferramenta
     */
    updateToolCard(toolId) {
        const card = this.container.querySelector(`[data-tool="${toolId}"]`);
        if (!card) return;

        const tool = this.osintTools.find(t => t.id === toolId);
        if (!tool) return;

        card.outerHTML = this.renderToolCard(tool);
        this.attachToolCardListener(toolId);
    }

    /**
     * Atualiza exibição de resultados
     */
    updateResultsDisplay() {
        const resultsEl = this.container.querySelector('#osint-results');
        if (resultsEl) {
            resultsEl.innerHTML = this.renderResultsArea();
        }
    }

    /**
     * Obtém chave de resultado
     * @param {string} toolId - ID da ferramenta
     * @returns {string}
     */
    getResultKey(toolId) {
        const keyMap = {
            'health-check': 'healthCheck',
            'device-fingerprint': 'deviceFingerprint',
            'location-analysis': 'locationAnalysis',
            'breach-check': 'breachCheck',
            'cross-platform': 'crossPlatform',
            'social-connections': 'socialConnections'
        };
        return keyMap[toolId] || toolId;
    }

    /**
     * Obtém ícone do dispositivo
     * @param {string} type - Tipo
     * @returns {string}
     */
    getDeviceIcon(type) {
        const icons = {
            'mobile': 'fa-mobile-alt',
            'tablet': 'fa-tablet-alt',
            'desktop': 'fa-desktop',
            'iphone': 'fa-mobile-alt',
            'android': 'fa-mobile-alt',
            'ipad': 'fa-tablet-alt'
        };
        return icons[type?.toLowerCase()] || 'fa-question';
    }

    /**
     * Obtém ícone da plataforma
     * @param {string} platform - Plataforma
     * @returns {string}
     */
    getPlatformIcon(platform) {
        const icons = {
            'twitter': 'fa-twitter',
            'x': 'fa-x-twitter',
            'facebook': 'fa-facebook',
            'linkedin': 'fa-linkedin',
            'youtube': 'fa-youtube',
            'tiktok': 'fa-tiktok',
            'github': 'fa-github',
            'reddit': 'fa-reddit',
            'pinterest': 'fa-pinterest',
            'snapchat': 'fa-snapchat',
            'telegram': 'fa-telegram',
            'discord': 'fa-discord',
            'spotify': 'fa-spotify',
            'twitch': 'fa-twitch'
        };
        return icons[platform?.toLowerCase()] || 'fa-globe';
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Listeners dos cards de ferramentas
        this.osintTools.forEach(tool => {
            this.attachToolCardListener(tool.id);
        });

        // Botão executar tudo
        const btnRunAll = this.container.querySelector('#btn-run-all-osint');
        if (btnRunAll) {
            btnRunAll.addEventListener('click', () => this.runAllOsint());
        }

        // Botão exportar
        const btnExport = this.container.querySelector('#btn-export-osint');
        if (btnExport) {
            btnExport.addEventListener('click', () => this.exportReport());
        }
    }

    /**
     * Anexa listener de card de ferramenta
     * @param {string} toolId - ID da ferramenta
     */
    attachToolCardListener(toolId) {
        const card = this.container.querySelector(`[data-tool="${toolId}"]`);
        if (!card) return;

        const actionBtn = card.querySelector('.tool-card__action');
        if (actionBtn) {
            const action = actionBtn.dataset.action;
            actionBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this[action]) {
                    this[action]();
                }
            });
        }

        // Clique no card também executa
        card.addEventListener('click', () => {
            const tool = this.osintTools.find(t => t.id === toolId);
            if (tool && this[tool.action]) {
                this[tool.action]();
            }
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
            year: 'numeric'
        });
    }
}

// Factory function
export function createOSINTToolbar(container) {
    const toolbar = new OSINTToolbar(container);
    toolbar.init();
    return toolbar;
}

export default OSINTToolbar;
