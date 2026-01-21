/**
 * BreachCheckWidget.js - Widget de Verificação de Vazamentos
 * 
 * Exibe resultados de verificação de vazamentos de dados:
 * - Lista de vazamentos encontrados
 * - Severidade por vazamento (cores)
 * - Data do vazamento
 * - Dados expostos (email, senha, etc)
 * - Score de exposição (0-100)
 * 
 * @module BreachCheckWidget
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class BreachCheckWidget {
    /**
     * Cria uma instância do BreachCheckWidget
     * @param {HTMLElement} container - Container do widget
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Dados de breaches
        this.breachData = null;

        // Estado de carregamento
        this.isLoading = false;

        // Identificador para busca (email ou username)
        this.searchIdentifier = '';

        // Filtro de severidade
        this.severityFilter = 'all'; // 'all' | 'critical' | 'high' | 'medium' | 'low'

        // Bind methods
        this.render = this.render.bind(this);
        this.checkBreaches = this.checkBreaches.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças nos dados
        this.state.subscribe('breachData', (data) => {
            if (data) {
                this.breachData = data;
                this.render();
            }
        });

        // Render inicial
        this.render();
    }

    /**
     * Verifica breaches
     * @param {string} identifier - Email ou username
     */
    async checkBreaches(identifier = null) {
        const searchTerm = identifier || this.searchIdentifier || this.state.get('currentUser');

        if (!searchTerm) {
            this.notifications.warning('Digite um email ou username para verificar');
            return;
        }

        this.searchIdentifier = searchTerm;
        this.isLoading = true;
        this.render();

        const loading = this.notifications.loading('Verificando vazamentos de dados...');

        try {
            const result = await this.api.checkBreaches(searchTerm);

            if (result.success) {
                this.breachData = result;
                this.state.set('breachData', result);

                const breachCount = result.breaches?.length || 0;
                if (breachCount > 0) {
                    loading.warning(`${breachCount} vazamento(s) encontrado(s)!`);
                } else {
                    loading.success('Nenhum vazamento encontrado');
                }
            } else {
                loading.error(result.error || 'Erro ao verificar vazamentos');
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

        if (!this.breachData) {
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
            <div class="widget breach-check-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-shield-alt"></i> Verificação de Vazamentos
                    </h3>
                </div>
                
                <div class="widget__empty ${this.isLoading ? 'widget__empty--loading' : ''}">
                    ${this.isLoading ? `
                        <div class="loading-animation">
                            <div class="shield-scan">
                                <i class="fas fa-shield-alt"></i>
                            </div>
                            <p>Verificando vazamentos...</p>
                        </div>
                    ` : `
                        <div class="empty-icon">
                            <i class="fas fa-user-shield"></i>
                        </div>
                        <p>Verifique se um email ou username foi exposto em vazamentos de dados</p>
                        
                        <div class="search-form">
                            <input type="text" 
                                   id="breach-search-input" 
                                   class="search-input"
                                   placeholder="Digite email ou username..."
                                   value="${this.escapeHtml(this.searchIdentifier)}">
                            <button class="btn btn-primary" id="btn-check-breaches">
                                <i class="fas fa-search"></i>
                                Verificar
                            </button>
                        </div>
                        
                        <small class="disclaimer">
                            <i class="fas fa-info-circle"></i>
                            Dados obtidos via API Have I Been Pwned
                        </small>
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
        const data = this.breachData;
        const breaches = data.breaches || [];
        const exposureScore = data.exposure_score || 0;
        const filteredBreaches = this.filterBreaches(breaches);

        return `
            <div class="widget breach-check-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-shield-alt"></i> Verificação de Vazamentos
                    </h3>
                    <div class="widget__actions">
                        <button class="widget__action-btn" id="btn-new-search" title="Nova Busca">
                            <i class="fas fa-search"></i>
                        </button>
                        <button class="widget__action-btn" id="btn-refresh-breaches" title="Atualizar">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Score de Exposição -->
                <div class="exposure-score ${this.getExposureClass(exposureScore)}">
                    <div class="score-visual">
                        <svg viewBox="0 0 100 100" class="score-circle">
                            <circle cx="50" cy="50" r="45" class="score-bg"/>
                            <circle cx="50" cy="50" r="45" class="score-fill" 
                                    style="stroke-dasharray: ${exposureScore * 2.83} 283"/>
                        </svg>
                        <div class="score-value">${exposureScore}</div>
                    </div>
                    <div class="score-info">
                        <span class="score-label">Score de Exposição</span>
                        <span class="score-desc">${this.getExposureDescription(exposureScore)}</span>
                    </div>
                </div>
                
                <!-- Resumo -->
                <div class="breach-summary">
                    <div class="summary-stat">
                        <span class="stat-value">${breaches.length}</span>
                        <span class="stat-label">Vazamentos</span>
                    </div>
                    <div class="summary-stat">
                        <span class="stat-value">${this.countExposedData(breaches)}</span>
                        <span class="stat-label">Tipos de Dados</span>
                    </div>
                    <div class="summary-stat summary-stat--${this.getHighestSeverity(breaches)}">
                        <span class="stat-value">${this.getHighestSeverityLabel(breaches)}</span>
                        <span class="stat-label">Maior Risco</span>
                    </div>
                </div>
                
                <!-- Filtros -->
                <div class="breach-filters">
                    <span class="filter-label">Filtrar por severidade:</span>
                    <div class="filter-buttons">
                        <button class="filter-btn ${this.severityFilter === 'all' ? 'active' : ''}" 
                                data-filter="all">Todos</button>
                        <button class="filter-btn filter-btn--critical ${this.severityFilter === 'critical' ? 'active' : ''}" 
                                data-filter="critical">Crítico</button>
                        <button class="filter-btn filter-btn--high ${this.severityFilter === 'high' ? 'active' : ''}" 
                                data-filter="high">Alto</button>
                        <button class="filter-btn filter-btn--medium ${this.severityFilter === 'medium' ? 'active' : ''}" 
                                data-filter="medium">Médio</button>
                        <button class="filter-btn filter-btn--low ${this.severityFilter === 'low' ? 'active' : ''}" 
                                data-filter="low">Baixo</button>
                    </div>
                </div>
                
                <!-- Lista de Breaches -->
                <div class="breach-list">
                    ${filteredBreaches.length > 0 ?
                filteredBreaches.map(breach => this.renderBreachCard(breach)).join('') :
                '<div class="no-breaches"><i class="fas fa-check-circle"></i> Nenhum vazamento nesta categoria</div>'
            }
                </div>
                
                <!-- Disclaimer -->
                <div class="widget__footer">
                    <small>
                        <i class="fas fa-clock"></i>
                        Verificado em: ${this.formatDate(data.checked_at || new Date())}
                    </small>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza card de breach
     * @param {Object} breach - Dados do breach
     * @returns {string} HTML
     */
    renderBreachCard(breach) {
        const severity = breach.severity || 'medium';
        const dataTypes = breach.data_classes || [];

        return `
            <div class="breach-card breach-card--${severity}">
                <div class="breach-header">
                    <div class="breach-logo">
                        ${breach.logo_path ? `
                            <img src="${this.escapeHtml(breach.logo_path)}" alt="${this.escapeHtml(breach.name)}"
                                 onerror="this.parentElement.innerHTML='<i class=\\'fas fa-database\\'></i>'">
                        ` : '<i class="fas fa-database"></i>'}
                    </div>
                    <div class="breach-title">
                        <h4>${this.escapeHtml(breach.name)}</h4>
                        <span class="breach-domain">${this.escapeHtml(breach.domain || '')}</span>
                    </div>
                    <div class="breach-severity severity-${severity}">
                        <i class="fas ${this.getSeverityIcon(severity)}"></i>
                        ${this.getSeverityLabel(severity)}
                    </div>
                </div>
                
                <div class="breach-body">
                    <div class="breach-info">
                        <div class="info-item">
                            <i class="far fa-calendar"></i>
                            <span>Data: ${this.formatDate(breach.breach_date)}</span>
                        </div>
                        <div class="info-item">
                            <i class="fas fa-users"></i>
                            <span>${this.formatNumber(breach.pwn_count || 0)} contas afetadas</span>
                        </div>
                    </div>
                    
                    <div class="breach-data-types">
                        <span class="data-label">Dados expostos:</span>
                        <div class="data-tags">
                            ${dataTypes.map(type => `
                                <span class="data-tag ${this.isSensitiveData(type) ? 'data-tag--sensitive' : ''}">
                                    <i class="${this.getDataTypeIcon(type)}"></i>
                                    ${this.translateDataType(type)}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                    
                    ${breach.description ? `
                        <p class="breach-description">${this.escapeHtml(breach.description)}</p>
                    ` : ''}
                </div>
                
                ${breach.is_verified ? `
                    <div class="breach-verified">
                        <i class="fas fa-check-circle"></i> Vazamento Verificado
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Filtra breaches por severidade
     * @param {Array} breaches - Lista de breaches
     * @returns {Array}
     */
    filterBreaches(breaches) {
        if (this.severityFilter === 'all') {
            return breaches;
        }
        return breaches.filter(b => b.severity === this.severityFilter);
    }

    /**
     * Define filtro de severidade
     * @param {string} filter - Filtro
     */
    setSeverityFilter(filter) {
        this.severityFilter = filter;
        this.render();
    }

    /**
     * Inicia nova busca
     */
    startNewSearch() {
        this.breachData = null;
        this.searchIdentifier = '';
        this.render();
    }

    // ==========================================================================
    // HELPERS
    // ==========================================================================

    /**
     * Obtém classe de exposição
     * @param {number} score - Score
     * @returns {string}
     */
    getExposureClass(score) {
        if (score >= 80) return 'exposure--critical';
        if (score >= 60) return 'exposure--high';
        if (score >= 40) return 'exposure--medium';
        if (score >= 20) return 'exposure--low';
        return 'exposure--safe';
    }

    /**
     * Obtém descrição de exposição
     * @param {number} score - Score
     * @returns {string}
     */
    getExposureDescription(score) {
        if (score >= 80) return 'Exposição Crítica - Ação Imediata Necessária';
        if (score >= 60) return 'Exposição Alta - Recomendado Trocar Senhas';
        if (score >= 40) return 'Exposição Moderada - Monitorar';
        if (score >= 20) return 'Exposição Baixa - Risco Mínimo';
        return 'Seguro - Nenhuma Exposição Conhecida';
    }

    /**
     * Conta tipos de dados expostos
     * @param {Array} breaches - Breaches
     * @returns {number}
     */
    countExposedData(breaches) {
        const allTypes = new Set();
        breaches.forEach(b => {
            (b.data_classes || []).forEach(type => allTypes.add(type));
        });
        return allTypes.size;
    }

    /**
     * Obtém maior severidade
     * @param {Array} breaches - Breaches
     * @returns {string}
     */
    getHighestSeverity(breaches) {
        const severityOrder = ['critical', 'high', 'medium', 'low'];
        for (const sev of severityOrder) {
            if (breaches.some(b => b.severity === sev)) {
                return sev;
            }
        }
        return 'low';
    }

    /**
     * Obtém label da maior severidade
     * @param {Array} breaches - Breaches
     * @returns {string}
     */
    getHighestSeverityLabel(breaches) {
        return this.getSeverityLabel(this.getHighestSeverity(breaches));
    }

    /**
     * Obtém label de severidade
     * @param {string} severity - Severidade
     * @returns {string}
     */
    getSeverityLabel(severity) {
        const labels = {
            'critical': 'Crítico',
            'high': 'Alto',
            'medium': 'Médio',
            'low': 'Baixo'
        };
        return labels[severity] || severity;
    }

    /**
     * Obtém ícone de severidade
     * @param {string} severity - Severidade
     * @returns {string}
     */
    getSeverityIcon(severity) {
        const icons = {
            'critical': 'fa-skull-crossbones',
            'high': 'fa-exclamation-triangle',
            'medium': 'fa-exclamation-circle',
            'low': 'fa-info-circle'
        };
        return icons[severity] || 'fa-circle';
    }

    /**
     * Obtém ícone do tipo de dados
     * @param {string} type - Tipo
     * @returns {string}
     */
    getDataTypeIcon(type) {
        const icons = {
            'Passwords': 'fas fa-key',
            'Email addresses': 'fas fa-envelope',
            'Usernames': 'fas fa-user',
            'Phone numbers': 'fas fa-phone',
            'Physical addresses': 'fas fa-map-marker-alt',
            'IP addresses': 'fas fa-network-wired',
            'Credit cards': 'fas fa-credit-card',
            'Dates of birth': 'fas fa-birthday-cake',
            'Social security numbers': 'fas fa-id-card',
            'Bank account numbers': 'fas fa-university'
        };
        return icons[type] || 'fas fa-file';
    }

    /**
     * Traduz tipo de dados
     * @param {string} type - Tipo
     * @returns {string}
     */
    translateDataType(type) {
        const translations = {
            'Passwords': 'Senhas',
            'Email addresses': 'Emails',
            'Usernames': 'Usuários',
            'Phone numbers': 'Telefones',
            'Physical addresses': 'Endereços',
            'IP addresses': 'IPs',
            'Credit cards': 'Cartões',
            'Dates of birth': 'Nascimento',
            'Social security numbers': 'CPF/SSN',
            'Bank account numbers': 'Contas Bancárias',
            'Names': 'Nomes',
            'Genders': 'Gêneros',
            'Job titles': 'Cargos',
            'Geographic locations': 'Localizações'
        };
        return translations[type] || type;
    }

    /**
     * Verifica se é dado sensível
     * @param {string} type - Tipo
     * @returns {boolean}
     */
    isSensitiveData(type) {
        const sensitive = [
            'Passwords', 'Credit cards', 'Social security numbers',
            'Bank account numbers', 'Financial data'
        ];
        return sensitive.includes(type);
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Botão verificar
        const btnCheck = this.container.querySelector('#btn-check-breaches');
        if (btnCheck) {
            btnCheck.addEventListener('click', () => {
                const input = this.container.querySelector('#breach-search-input');
                const value = input?.value?.trim() || '';
                this.checkBreaches(value);
            });
        }

        // Input enter
        const searchInput = this.container.querySelector('#breach-search-input');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.checkBreaches(searchInput.value.trim());
                }
            });
        }

        // Botão refresh
        const btnRefresh = this.container.querySelector('#btn-refresh-breaches');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.checkBreaches());
        }

        // Botão nova busca
        const btnNew = this.container.querySelector('#btn-new-search');
        if (btnNew) {
            btnNew.addEventListener('click', () => this.startNewSearch());
        }

        // Filtros
        const filterBtns = this.container.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.setSeverityFilter(btn.dataset.filter);
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
        if (num >= 1000000000) {
            return (num / 1000000000).toFixed(1) + 'B';
        }
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    /**
     * Formata data
     * @param {Date|string} date - Data
     * @returns {string}
     */
    formatDate(date) {
        if (!date) return 'Desconhecida';
        const d = new Date(date);
        return d.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
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
export function createBreachCheckWidget(container) {
    const widget = new BreachCheckWidget(container);
    widget.init();
    return widget;
}

export default BreachCheckWidget;
