/**
 * SearchAdvanced.js - Busca Avançada com Autocomplete
 * 
 * Implementa funcionalidades de busca:
 * - Input de busca com autocomplete
 * - Histórico de buscas recentes
 * - Sugestões de perfis populares
 * - Validação de username em tempo real
 * 
 * @module SearchAdvanced
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';
import { getCacheService } from '../core/CacheService.js';

export class SearchAdvanced {
    /**
     * Cria uma instância do SearchAdvanced
     * @param {HTMLElement} container - Container do componente
     * @param {Object} options - Opções de configuração
     */
    constructor(container, options = {}) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();
        this.cache = getCacheService();

        // Configurações
        this.config = {
            minChars: options.minChars || 3,
            debounceMs: options.debounceMs || 300,
            maxHistory: options.maxHistory || 10,
            maxSuggestions: options.maxSuggestions || 5,
            storageKey: options.storageKey || 'ig_search_history',
            placeholder: options.placeholder || 'Buscar perfil do Instagram...'
        };

        // Estado
        this.inputValue = '';
        this.suggestions = [];
        this.selectedIndex = -1;
        this.isOpen = false;
        this.isLoading = false;
        this.isValid = null;

        // Histórico
        this.searchHistory = this.loadHistory();

        // Debounce timer
        this.debounceTimer = null;

        // Perfis populares (cache)
        this.popularProfiles = [];

        // Bind methods
        this.render = this.render.bind(this);
        this.handleInput = this.handleInput.bind(this);
        this.handleKeydown = this.handleKeydown.bind(this);
        this.search = this.search.bind(this);
    }

    /**
     * Inicializa o componente
     */
    async init() {
        this.render();
        this.attachEventListeners();

        // Carregar perfis populares
        await this.loadPopularProfiles();
    }

    /**
     * Carrega histórico do localStorage
     * @returns {Array}
     */
    loadHistory() {
        try {
            const stored = localStorage.getItem(this.config.storageKey);
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            return [];
        }
    }

    /**
     * Salva histórico no localStorage
     */
    saveHistory() {
        try {
            localStorage.setItem(
                this.config.storageKey,
                JSON.stringify(this.searchHistory.slice(0, this.config.maxHistory))
            );
        } catch (e) {
            console.warn('Erro ao salvar histórico:', e);
        }
    }

    /**
     * Adiciona ao histórico
     * @param {Object} item - Item do histórico
     */
    addToHistory(item) {
        // Remover duplicatas
        this.searchHistory = this.searchHistory.filter(h => h.username !== item.username);

        // Adicionar no início
        this.searchHistory.unshift({
            ...item,
            timestamp: Date.now()
        });

        // Limitar tamanho
        this.searchHistory = this.searchHistory.slice(0, this.config.maxHistory);

        // Salvar
        this.saveHistory();
    }

    /**
     * Remove do histórico
     * @param {string} username - Username
     */
    removeFromHistory(username) {
        this.searchHistory = this.searchHistory.filter(h => h.username !== username);
        this.saveHistory();
        this.updateDropdown();
    }

    /**
     * Carrega perfis populares
     */
    async loadPopularProfiles() {
        try {
            // Tentar cache primeiro
            const cached = await this.cache.get('popular_profiles');
            if (cached) {
                this.popularProfiles = cached;
                return;
            }

            const result = await this.api.getPopularProfiles();
            if (result.success && result.profiles) {
                this.popularProfiles = result.profiles;
                await this.cache.set('popular_profiles', result.profiles, {
                    ttl: 24 * 60 * 60 * 1000 // 24 horas
                });
            }
        } catch (error) {
            console.debug('Erro ao carregar perfis populares:', error);
        }
    }

    /**
     * Renderiza o componente
     */
    render() {
        this.container.innerHTML = `
            <div class="search-advanced" role="combobox" aria-expanded="${this.isOpen}" aria-haspopup="listbox">
                <div class="search-input-container">
                    <i class="fas fa-search search-icon"></i>
                    
                    <input type="text" 
                           class="search-input" 
                           id="search-input"
                           placeholder="${this.config.placeholder}"
                           autocomplete="off"
                           autocapitalize="off"
                           autocorrect="off"
                           spellcheck="false"
                           aria-autocomplete="list"
                           aria-controls="search-dropdown"
                           value="${this.escapeHtml(this.inputValue)}">
                    
                    <div class="search-status">
                        ${this.isLoading ? `
                            <span class="search-loading"><i class="fas fa-spinner fa-spin"></i></span>
                        ` : ''}
                        ${this.isValid === true && !this.isLoading ? `
                            <span class="search-valid"><i class="fas fa-check-circle"></i></span>
                        ` : ''}
                        ${this.isValid === false && !this.isLoading ? `
                            <span class="search-invalid"><i class="fas fa-times-circle"></i></span>
                        ` : ''}
                    </div>
                    
                    ${this.inputValue ? `
                        <button class="search-clear" id="search-clear" title="Limpar">
                            <i class="fas fa-times"></i>
                        </button>
                    ` : ''}
                    
                    <button class="search-submit" id="search-submit" title="Buscar">
                        <i class="fas fa-arrow-right"></i>
                    </button>
                </div>
                
                <div class="search-dropdown ${this.isOpen ? 'search-dropdown--open' : ''}" 
                     id="search-dropdown"
                     role="listbox">
                    ${this.renderDropdownContent()}
                </div>
            </div>
        `;
    }

    /**
     * Renderiza conteúdo do dropdown
     * @returns {string} HTML
     */
    renderDropdownContent() {
        // Se tem input, mostrar sugestões
        if (this.inputValue.length >= this.config.minChars) {
            return this.renderSuggestions();
        }

        // Se não tem input, mostrar histórico e populares
        return this.renderHistoryAndPopular();
    }

    /**
     * Renderiza sugestões de busca
     * @returns {string} HTML
     */
    renderSuggestions() {
        if (this.isLoading) {
            return `
                <div class="search-dropdown__loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Buscando...</span>
                </div>
            `;
        }

        if (this.suggestions.length === 0) {
            return `
                <div class="search-dropdown__empty">
                    <i class="fas fa-user-slash"></i>
                    <span>Nenhum perfil encontrado</span>
                </div>
            `;
        }

        return `
            <div class="search-dropdown__section">
                <span class="search-dropdown__label">
                    <i class="fas fa-search"></i> Resultados
                </span>
                <ul class="search-dropdown__list">
                    ${this.suggestions.map((item, index) => `
                        <li class="search-dropdown__item ${index === this.selectedIndex ? 'search-dropdown__item--selected' : ''}"
                            role="option"
                            data-username="${this.escapeHtml(item.username)}"
                            data-index="${index}">
                            <div class="search-item">
                                <div class="search-item__avatar">
                                    ${item.profile_pic ? `
                                        <img src="${this.escapeHtml(item.profile_pic)}" alt="">
                                    ` : '<i class="fas fa-user"></i>'}
                                </div>
                                <div class="search-item__info">
                                    <span class="search-item__name">
                                        ${this.highlightMatch(item.full_name || item.username)}
                                        ${item.is_verified ? '<i class="fas fa-check-circle verified"></i>' : ''}
                                    </span>
                                    <span class="search-item__username">@${this.escapeHtml(item.username)}</span>
                                </div>
                                ${item.followers_count ? `
                                    <span class="search-item__followers">
                                        ${this.formatNumber(item.followers_count)} seguidores
                                    </span>
                                ` : ''}
                            </div>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    /**
     * Renderiza histórico e perfis populares
     * @returns {string} HTML
     */
    renderHistoryAndPopular() {
        let html = '';

        // Histórico
        if (this.searchHistory.length > 0) {
            html += `
                <div class="search-dropdown__section">
                    <span class="search-dropdown__label">
                        <i class="fas fa-history"></i> Buscas Recentes
                        <button class="search-dropdown__clear-all" id="clear-history" title="Limpar histórico">
                            <i class="fas fa-trash"></i>
                        </button>
                    </span>
                    <ul class="search-dropdown__list">
                        ${this.searchHistory.map((item, index) => `
                            <li class="search-dropdown__item"
                                role="option"
                                data-username="${this.escapeHtml(item.username)}"
                                data-index="${index}">
                                <div class="search-item search-item--history">
                                    <div class="search-item__avatar">
                                        ${item.profile_pic ? `
                                            <img src="${this.escapeHtml(item.profile_pic)}" alt="">
                                        ` : '<i class="fas fa-user"></i>'}
                                    </div>
                                    <div class="search-item__info">
                                        <span class="search-item__name">${this.escapeHtml(item.full_name || item.username)}</span>
                                        <span class="search-item__username">@${this.escapeHtml(item.username)}</span>
                                    </div>
                                    <button class="search-item__remove" 
                                            data-username="${this.escapeHtml(item.username)}"
                                            title="Remover do histórico">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        // Perfis populares
        if (this.popularProfiles.length > 0) {
            html += `
                <div class="search-dropdown__section">
                    <span class="search-dropdown__label">
                        <i class="fas fa-fire"></i> Perfis Populares
                    </span>
                    <ul class="search-dropdown__list">
                        ${this.popularProfiles.slice(0, 5).map((item, index) => `
                            <li class="search-dropdown__item"
                                role="option"
                                data-username="${this.escapeHtml(item.username)}"
                                data-index="${index + this.searchHistory.length}">
                                <div class="search-item search-item--popular">
                                    <div class="search-item__avatar">
                                        ${item.profile_pic ? `
                                            <img src="${this.escapeHtml(item.profile_pic)}" alt="">
                                        ` : '<i class="fas fa-user"></i>'}
                                    </div>
                                    <div class="search-item__info">
                                        <span class="search-item__name">
                                            ${this.escapeHtml(item.full_name || item.username)}
                                            ${item.is_verified ? '<i class="fas fa-check-circle verified"></i>' : ''}
                                        </span>
                                        <span class="search-item__username">@${this.escapeHtml(item.username)}</span>
                                    </div>
                                    <span class="search-item__badge">
                                        <i class="fas fa-fire"></i>
                                    </span>
                                </div>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        if (!html) {
            html = `
                <div class="search-dropdown__empty">
                    <i class="fas fa-search"></i>
                    <span>Digite para buscar um perfil</span>
                </div>
            `;
        }

        return html;
    }

    /**
     * Handler de input
     * @param {Event} e - Evento
     */
    handleInput(e) {
        this.inputValue = e.target.value.trim();
        this.selectedIndex = -1;
        this.isOpen = true;

        // Limpar validação
        this.isValid = null;

        // Limpar debounce anterior
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        // Re-render (mostra estado de input)
        this.render();
        this.attachEventListeners();

        // Se tem caracteres suficientes, buscar
        if (this.inputValue.length >= this.config.minChars) {
            this.debounceTimer = setTimeout(() => {
                this.fetchSuggestions();
            }, this.config.debounceMs);
        } else {
            this.suggestions = [];
        }
    }

    /**
     * Busca sugestões da API
     */
    async fetchSuggestions() {
        if (this.inputValue.length < this.config.minChars) return;

        this.isLoading = true;
        this.render();
        this.attachEventListeners();

        try {
            const result = await this.api.searchProfiles(this.inputValue);

            if (result.success && result.users) {
                this.suggestions = result.users.slice(0, this.config.maxSuggestions);

                // Validar se o username exato existe
                this.isValid = this.suggestions.some(
                    u => u.username.toLowerCase() === this.inputValue.toLowerCase()
                );
            } else {
                this.suggestions = [];
                this.isValid = false;
            }
        } catch (error) {
            console.error('Erro ao buscar sugestões:', error);
            this.suggestions = [];
            this.isValid = false;
        } finally {
            this.isLoading = false;
            this.render();
            this.attachEventListeners();
        }
    }

    /**
     * Handler de teclas
     * @param {KeyboardEvent} e - Evento
     */
    handleKeydown(e) {
        const items = this.getDropdownItems();

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
                this.updateDropdown();
                break;

            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
                this.updateDropdown();
                break;

            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0 && items[this.selectedIndex]) {
                    const username = items[this.selectedIndex].dataset.username;
                    this.selectItem(username);
                } else if (this.inputValue) {
                    this.search(this.inputValue);
                }
                break;

            case 'Escape':
                this.closeDropdown();
                break;

            case 'Tab':
                this.closeDropdown();
                break;
        }
    }

    /**
     * Obtém itens do dropdown
     * @returns {NodeList}
     */
    getDropdownItems() {
        return this.container.querySelectorAll('.search-dropdown__item');
    }

    /**
     * Atualiza dropdown (seleção)
     */
    updateDropdown() {
        const items = this.getDropdownItems();
        items.forEach((item, index) => {
            item.classList.toggle('search-dropdown__item--selected', index === this.selectedIndex);
        });
    }

    /**
     * Seleciona item
     * @param {string} username - Username
     */
    selectItem(username) {
        // Encontrar info do item
        const item = this.suggestions.find(s => s.username === username) ||
            this.searchHistory.find(h => h.username === username) ||
            this.popularProfiles.find(p => p.username === username);

        if (item) {
            this.addToHistory(item);
        }

        this.inputValue = username;
        this.closeDropdown();
        this.search(username);
    }

    /**
     * Executa busca
     * @param {string} username - Username
     */
    search(username) {
        if (!username) return;

        // Limpar caracteres inválidos
        const cleanUsername = username.replace(/[^a-zA-Z0-9._]/g, '');

        if (!cleanUsername) {
            this.notifications.warning('Username inválido');
            return;
        }

        // Atualizar state
        this.state.set('currentUser', cleanUsername);

        // Emitir evento de busca
        this.container.dispatchEvent(new CustomEvent('search', {
            detail: { username: cleanUsername }
        }));

        // Fechar dropdown
        this.closeDropdown();

        // Notificar
        this.notifications.info(`Buscando @${cleanUsername}...`);
    }

    /**
     * Abre dropdown
     */
    openDropdown() {
        this.isOpen = true;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Fecha dropdown
     */
    closeDropdown() {
        this.isOpen = false;
        this.selectedIndex = -1;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Limpa input
     */
    clearInput() {
        this.inputValue = '';
        this.suggestions = [];
        this.isValid = null;
        this.render();
        this.attachEventListeners();

        // Focar no input
        const input = this.container.querySelector('#search-input');
        if (input) {
            input.focus();
        }
    }

    /**
     * Limpa todo o histórico
     */
    clearAllHistory() {
        this.searchHistory = [];
        this.saveHistory();
        this.render();
        this.attachEventListeners();
        this.notifications.success('Histórico limpo');
    }

    /**
     * Destaca match no texto
     * @param {string} text - Texto
     * @returns {string} HTML
     */
    highlightMatch(text) {
        if (!text || !this.inputValue) return this.escapeHtml(text);

        const escaped = this.escapeHtml(text);
        const regex = new RegExp(`(${this.escapeRegex(this.inputValue)})`, 'gi');
        return escaped.replace(regex, '<mark>$1</mark>');
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Input
        const input = this.container.querySelector('#search-input');
        if (input) {
            input.addEventListener('input', this.handleInput);
            input.addEventListener('keydown', this.handleKeydown);
            input.addEventListener('focus', () => this.openDropdown());
        }

        // Botão submit
        const submitBtn = this.container.querySelector('#search-submit');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                if (this.inputValue) {
                    this.search(this.inputValue);
                }
            });
        }

        // Botão limpar
        const clearBtn = this.container.querySelector('#search-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearInput());
        }

        // Itens do dropdown
        const items = this.container.querySelectorAll('.search-dropdown__item');
        items.forEach(item => {
            item.addEventListener('click', () => {
                const username = item.dataset.username;
                if (username) {
                    this.selectItem(username);
                }
            });
        });

        // Botões de remover do histórico
        const removeBtns = this.container.querySelectorAll('.search-item__remove');
        removeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const username = btn.dataset.username;
                if (username) {
                    this.removeFromHistory(username);
                }
            });
        });

        // Limpar todo histórico
        const clearHistoryBtn = this.container.querySelector('#clear-history');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.clearAllHistory();
            });
        }

        // Fechar ao clicar fora
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.closeDropdown();
            }
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
     * Escapa regex
     * @param {string} str - String
     * @returns {string}
     */
    escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
}

// Factory function
export function createSearchAdvanced(container, options = {}) {
    const search = new SearchAdvanced(container, options);
    search.init();
    return search;
}

export default SearchAdvanced;
