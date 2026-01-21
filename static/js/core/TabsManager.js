/**
 * TabsManager.js - Sistema de Abas/Seções
 * 
 * Gerencia navegação por abas no dashboard:
 * - Tab: Overview (resumo geral)
 * - Tab: Atividades (feed de atividades)
 * - Tab: Inteligência (widgets de IA)
 * - Tab: Rede Social (grafo)
 * - Tab: OSINT (investigação)
 * - Tab: Histórico (snapshots temporais)
 * - Persistir aba ativa na URL (hash routing)
 * 
 * @module TabsManager
 * @version 1.0.0
 */

import { getStateManager } from '../core/StateManager.js';

// Singleton instance
let instance = null;

export class TabsManager {
    /**
     * Cria uma instância do TabsManager
     * @param {Object} options - Opções de configuração
     */
    constructor(options = {}) {
        if (instance) {
            return instance;
        }

        this.state = getStateManager();

        // Container das tabs
        this.container = options.container || null;

        // Container do conteúdo
        this.contentContainer = options.contentContainer || null;

        // Definição das tabs
        this.tabs = options.tabs || this.getDefaultTabs();

        // Tab ativa
        this.activeTab = options.defaultTab || 'overview';

        // Callbacks de mudança de tab
        this.onChangeCallbacks = new Set();

        // Histórico de navegação
        this.navigationHistory = [];

        // Bind methods
        this.render = this.render.bind(this);
        this.setActiveTab = this.setActiveTab.bind(this);
        this.handleHashChange = this.handleHashChange.bind(this);

        instance = this;

        // Inicializar routing
        this.initHashRouting();
    }

    /**
     * Obtém tabs padrão
     * @returns {Array}
     */
    getDefaultTabs() {
        return [
            {
                id: 'overview',
                label: 'Visão Geral',
                icon: 'fas fa-home',
                description: 'Resumo completo do perfil',
                widgets: ['profile', 'stats', 'sentiment', 'engagement']
            },
            {
                id: 'activities',
                label: 'Atividades',
                icon: 'fas fa-stream',
                description: 'Feed de atividades recentes',
                widgets: ['activity-feed', 'top-interactions', 'calendar']
            },
            {
                id: 'intelligence',
                label: 'Inteligência',
                icon: 'fas fa-brain',
                description: 'Análises de IA e previsões',
                widgets: ['sentiment', 'predictive', 'vision', 'ai-insights']
            },
            {
                id: 'network',
                label: 'Rede Social',
                icon: 'fas fa-project-diagram',
                description: 'Visualização de conexões',
                widgets: ['graph', 'top-interactions']
            },
            {
                id: 'osint',
                label: 'OSINT',
                icon: 'fas fa-user-secret',
                description: 'Investigação cross-platform',
                widgets: ['osint-toolbar', 'breach-check', 'geo-heatmap']
            },
            {
                id: 'history',
                label: 'Histórico',
                icon: 'fas fa-history',
                description: 'Snapshots temporais',
                widgets: ['timeline', 'calendar', 'comparator']
            }
        ];
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças na tab ativa
        this.state.subscribe('activeTab', (tabId) => {
            if (tabId && tabId !== this.activeTab) {
                this.setActiveTab(tabId, false);
            }
        });

        // Render inicial
        this.render();
    }

    /**
     * Inicializa hash routing
     */
    initHashRouting() {
        // Ler hash inicial
        const initialHash = window.location.hash.slice(1);
        if (initialHash && this.tabs.find(t => t.id === initialHash)) {
            this.activeTab = initialHash;
        }

        // Listener de mudança de hash
        window.addEventListener('hashchange', this.handleHashChange);
    }

    /**
     * Handler de mudança de hash
     */
    handleHashChange() {
        const hash = window.location.hash.slice(1);
        if (hash && this.tabs.find(t => t.id === hash)) {
            this.setActiveTab(hash, false);
        }
    }

    /**
     * Renderiza as tabs
     */
    render() {
        if (!this.container) return;

        this.container.innerHTML = this.renderTabsBar();
        this.attachEventListeners();
    }

    /**
     * Renderiza barra de tabs
     * @returns {string} HTML
     */
    renderTabsBar() {
        return `
            <div class="tabs-container">
                <div class="tabs-bar" role="tablist">
                    ${this.tabs.map(tab => this.renderTab(tab)).join('')}
                </div>
                
                <!-- Indicador móvel -->
                <div class="tabs-indicator"></div>
                
                <!-- Navegação mobile (dropdown) -->
                <div class="tabs-mobile">
                    <button class="tabs-mobile__trigger" id="mobile-tabs-trigger">
                        <i class="${this.getActiveTabIcon()}"></i>
                        <span>${this.getActiveTabLabel()}</span>
                        <i class="fas fa-chevron-down"></i>
                    </button>
                    <div class="tabs-mobile__dropdown" id="mobile-tabs-dropdown">
                        ${this.tabs.map(tab => this.renderMobileTab(tab)).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza uma tab
     * @param {Object} tab - Definição da tab
     * @returns {string} HTML
     */
    renderTab(tab) {
        const isActive = this.activeTab === tab.id;

        return `
            <button class="tab ${isActive ? 'tab--active' : ''}"
                    role="tab"
                    id="tab-${tab.id}"
                    data-tab-id="${tab.id}"
                    aria-selected="${isActive}"
                    aria-controls="panel-${tab.id}"
                    title="${tab.description}">
                <i class="${tab.icon}"></i>
                <span class="tab__label">${tab.label}</span>
                ${tab.badge ? `<span class="tab__badge">${tab.badge}</span>` : ''}
            </button>
        `;
    }

    /**
     * Renderiza tab mobile
     * @param {Object} tab - Definição da tab
     * @returns {string} HTML
     */
    renderMobileTab(tab) {
        const isActive = this.activeTab === tab.id;

        return `
            <button class="tabs-mobile__item ${isActive ? 'tabs-mobile__item--active' : ''}"
                    data-tab-id="${tab.id}">
                <i class="${tab.icon}"></i>
                <span>${tab.label}</span>
                <span class="tabs-mobile__desc">${tab.description}</span>
            </button>
        `;
    }

    /**
     * Define tab ativa
     * @param {string} tabId - ID da tab
     * @param {boolean} updateHash - Atualizar hash na URL
     */
    setActiveTab(tabId, updateHash = true) {
        const tab = this.tabs.find(t => t.id === tabId);
        if (!tab) return;

        // Salvar no histórico
        if (this.activeTab !== tabId) {
            this.navigationHistory.push(this.activeTab);
        }

        this.activeTab = tabId;

        // Atualizar hash
        if (updateHash) {
            history.pushState(null, '', `#${tabId}`);
        }

        // Atualizar state
        this.state.set('activeTab', tabId);

        // Re-render
        this.render();

        // Callback
        this.triggerChange(tabId, tab);

        // Mostrar conteúdo correto
        this.showTabContent(tabId);
    }

    /**
     * Mostra conteúdo da tab
     * @param {string} tabId - ID da tab
     */
    showTabContent(tabId) {
        if (!this.contentContainer) return;

        // Esconder todos os painéis
        const panels = this.contentContainer.querySelectorAll('[data-tab-panel]');
        panels.forEach(panel => {
            const isActive = panel.dataset.tabPanel === tabId;
            panel.classList.toggle('tab-panel--active', isActive);
            panel.setAttribute('aria-hidden', !isActive);
        });
    }

    /**
     * Obtém label da tab ativa
     * @returns {string}
     */
    getActiveTabLabel() {
        const tab = this.tabs.find(t => t.id === this.activeTab);
        return tab ? tab.label : '';
    }

    /**
     * Obtém ícone da tab ativa
     * @returns {string}
     */
    getActiveTabIcon() {
        const tab = this.tabs.find(t => t.id === this.activeTab);
        return tab ? tab.icon : 'fas fa-home';
    }

    /**
     * Navega para tab anterior
     */
    goBack() {
        if (this.navigationHistory.length > 0) {
            const prevTab = this.navigationHistory.pop();
            this.setActiveTab(prevTab);
        }
    }

    /**
     * Registra callback de mudança
     * @param {Function} callback - Função callback
     * @returns {Function} Função para remover callback
     */
    onChange(callback) {
        this.onChangeCallbacks.add(callback);
        return () => this.onChangeCallbacks.delete(callback);
    }

    /**
     * Dispara callbacks de mudança
     * @param {string} tabId - ID da tab
     * @param {Object} tab - Definição da tab
     */
    triggerChange(tabId, tab) {
        this.onChangeCallbacks.forEach(callback => {
            try {
                callback(tabId, tab);
            } catch (error) {
                console.error('Erro no callback de mudança de tab:', error);
            }
        });
    }

    /**
     * Define badge em uma tab
     * @param {string} tabId - ID da tab
     * @param {string|number} badge - Valor do badge
     */
    setBadge(tabId, badge) {
        const tabIndex = this.tabs.findIndex(t => t.id === tabId);
        if (tabIndex !== -1) {
            this.tabs[tabIndex].badge = badge;
            this.render();
        }
    }

    /**
     * Remove badge de uma tab
     * @param {string} tabId - ID da tab
     */
    removeBadge(tabId) {
        const tabIndex = this.tabs.findIndex(t => t.id === tabId);
        if (tabIndex !== -1) {
            delete this.tabs[tabIndex].badge;
            this.render();
        }
    }

    /**
     * Adiciona tab dinamicamente
     * @param {Object} tab - Definição da tab
     * @param {number} position - Posição (opcional)
     */
    addTab(tab, position = null) {
        if (this.tabs.find(t => t.id === tab.id)) {
            console.warn(`Tab ${tab.id} já existe`);
            return;
        }

        if (position !== null && position >= 0 && position <= this.tabs.length) {
            this.tabs.splice(position, 0, tab);
        } else {
            this.tabs.push(tab);
        }

        this.render();
    }

    /**
     * Remove tab dinamicamente
     * @param {string} tabId - ID da tab
     */
    removeTab(tabId) {
        const index = this.tabs.findIndex(t => t.id === tabId);
        if (index !== -1) {
            this.tabs.splice(index, 1);

            // Se a tab removida era a ativa, ir para a primeira
            if (this.activeTab === tabId && this.tabs.length > 0) {
                this.setActiveTab(this.tabs[0].id);
            }

            this.render();
        }
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Clique nas tabs
        const tabButtons = this.container.querySelectorAll('.tab');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.setActiveTab(btn.dataset.tabId);
            });
        });

        // Navegação por teclado
        tabButtons.forEach((btn, index) => {
            btn.addEventListener('keydown', (e) => {
                let targetIndex = index;

                if (e.key === 'ArrowRight') {
                    targetIndex = (index + 1) % this.tabs.length;
                } else if (e.key === 'ArrowLeft') {
                    targetIndex = (index - 1 + this.tabs.length) % this.tabs.length;
                } else if (e.key === 'Home') {
                    targetIndex = 0;
                } else if (e.key === 'End') {
                    targetIndex = this.tabs.length - 1;
                } else {
                    return;
                }

                e.preventDefault();
                const allTabs = Array.from(tabButtons);
                allTabs[targetIndex].focus();
                this.setActiveTab(this.tabs[targetIndex].id);
            });
        });

        // Toggle dropdown mobile
        const mobileToggle = this.container.querySelector('#mobile-tabs-trigger');
        const mobileDropdown = this.container.querySelector('#mobile-tabs-dropdown');

        if (mobileToggle && mobileDropdown) {
            mobileToggle.addEventListener('click', () => {
                mobileDropdown.classList.toggle('tabs-mobile__dropdown--open');
            });

            // Fechar ao clicar fora
            document.addEventListener('click', (e) => {
                if (!mobileToggle.contains(e.target) && !mobileDropdown.contains(e.target)) {
                    mobileDropdown.classList.remove('tabs-mobile__dropdown--open');
                }
            });

            // Clique em item mobile
            const mobileItems = mobileDropdown.querySelectorAll('.tabs-mobile__item');
            mobileItems.forEach(item => {
                item.addEventListener('click', () => {
                    this.setActiveTab(item.dataset.tabId);
                    mobileDropdown.classList.remove('tabs-mobile__dropdown--open');
                });
            });
        }
    }

    /**
     * Destrói o componente
     */
    destroy() {
        window.removeEventListener('hashchange', this.handleHashChange);
        this.onChangeCallbacks.clear();
        instance = null;
    }
}

/**
 * Obtém instância singleton do TabsManager
 * @param {Object} options - Opções
 * @returns {TabsManager}
 */
export function getTabsManager(options = {}) {
    if (!instance) {
        instance = new TabsManager(options);
    }
    return instance;
}

export default TabsManager;
