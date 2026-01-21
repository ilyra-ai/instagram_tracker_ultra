/**
 * ProfileCard.js - Componente de Card de Perfil
 * 
 * Exibe informações detalhadas do perfil do usuário:
 * - Foto de perfil com status
 * - Nome, username, badge verificado
 * - Contadores (seguidores, seguindo, posts)
 * - Bio
 * - Botões de ação
 * 
 * @module ProfileCard
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class ProfileCard {
    /**
     * Cria uma instância do ProfileCard
     * @param {HTMLElement} container - Container do card
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Dados do perfil
        this.profile = null;

        // Bind methods
        this.render = this.render.bind(this);
        this.loadProfile = this.loadProfile.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças no perfil
        this.state.subscribe('profile', (profile) => {
            this.profile = profile;
            this.render();
        });

        // Render inicial
        this.render();
    }

    /**
     * Carrega perfil do usuário
     * @param {string} username - Nome de usuário
     */
    async loadProfile(username) {
        if (!username) {
            this.notifications.warning('Digite um nome de usuário');
            return;
        }

        try {
            const result = await this.api.getUserInfo(username);

            if (result.success && result.user_info) {
                this.state.set('profile', result.user_info);
                this.state.set('currentUser', username);
                this.notifications.success(`Perfil de @${username} carregado!`);
            } else {
                this.notifications.error(result.error || 'Perfil não encontrado');
            }
        } catch (error) {
            this.notifications.error(`Erro: ${error.message}`);
        }
    }

    /**
     * Renderiza o card
     */
    render() {
        if (!this.container) return;

        if (!this.profile) {
            this.container.innerHTML = this.renderEmptyState();
            return;
        }

        this.container.innerHTML = this.renderProfileCard();
        this.attachEventListeners();
    }

    /**
     * Renderiza estado vazio
     * @returns {string} HTML
     */
    renderEmptyState() {
        return `
            <div class="widget profile-widget profile-widget--empty">
                <div class="profile-empty">
                    <i class="fas fa-user-circle"></i>
                    <p>Nenhum perfil selecionado</p>
                    <small>Use a busca acima para analisar um perfil</small>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza card de perfil completo
     * @returns {string} HTML
     */
    renderProfileCard() {
        const p = this.profile;

        const isPrivate = p.is_private;
        const isVerified = p.is_verified;
        const isBusiness = p.is_business;

        // Determinar status do perfil
        let statusClass = 'online';
        let statusText = 'Público';
        if (isPrivate) {
            statusClass = 'private';
            statusText = 'Privado';
        }

        // Badge de Account Health (se disponível)
        const healthScore = this.state.get('osint.accountHealth.score');
        const healthBadge = healthScore ? this.renderHealthBadge(healthScore) : '';

        return `
            <div class="widget profile-widget">
                <!-- Header do Perfil -->
                <div class="profile-widget__header">
                    <div class="profile-avatar-container">
                        <img src="${this.escapeHtml(p.profile_pic_url || '/static/img/default-avatar.png')}" 
                             alt="${this.escapeHtml(p.username)}"
                             class="profile-avatar"
                             onerror="this.src='/static/img/default-avatar.png'">
                        <div class="profile-status profile-status--${statusClass}" title="${statusText}"></div>
                    </div>
                    
                    <div class="profile-info">
                        <h2 class="profile-name">
                            ${this.escapeHtml(p.full_name || p.username)}
                            ${isVerified ? '<i class="fas fa-check-circle verified-badge" title="Verificado"></i>' : ''}
                            ${isBusiness ? '<i class="fas fa-briefcase business-badge" title="Conta Comercial"></i>' : ''}
                        </h2>
                        <span class="profile-username">@${this.escapeHtml(p.username)}</span>
                        ${p.category ? `<span class="profile-category">${this.escapeHtml(p.category)}</span>` : ''}
                    </div>
                    
                    <div class="profile-actions-menu">
                        <button class="widget__action-btn" onclick="copyToClipboard('https://instagram.com/${p.username}')" title="Copiar link">
                            <i class="fas fa-link"></i>
                        </button>
                        <a href="https://instagram.com/${this.escapeHtml(p.username)}" target="_blank" class="widget__action-btn" title="Abrir no Instagram">
                            <i class="fab fa-instagram"></i>
                        </a>
                    </div>
                </div>
                
                <!-- Estatísticas -->
                <div class="profile-stats">
                    <div class="stat-item">
                        <span class="stat-number">${this.formatNumber(p.followers_count || p.follower_count || 0)}</span>
                        <span class="stat-label">Seguidores</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${this.formatNumber(p.following_count || 0)}</span>
                        <span class="stat-label">Seguindo</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${this.formatNumber(p.media_count || 0)}</span>
                        <span class="stat-label">Posts</span>
                    </div>
                    ${p.engagement_rate ? `
                        <div class="stat-item stat-item--highlight">
                            <span class="stat-number">${(p.engagement_rate * 100).toFixed(2)}%</span>
                            <span class="stat-label">Engajamento</span>
                        </div>
                    ` : ''}
                </div>
                
                <!-- Bio -->
                ${p.biography ? `
                    <div class="profile-bio">
                        <p>${this.formatBio(p.biography)}</p>
                    </div>
                ` : ''}
                
                <!-- Links externos -->
                ${p.external_url ? `
                    <div class="profile-external-link">
                        <a href="${this.escapeHtml(p.external_url)}" target="_blank" rel="noopener">
                            <i class="fas fa-external-link-alt"></i>
                            ${this.extractDomain(p.external_url)}
                        </a>
                    </div>
                ` : ''}
                
                <!-- Health Badge -->
                ${healthBadge}
                
                <!-- Metadados adicionais -->
                <div class="profile-metadata">
                    ${p.fb_page_name ? `
                        <div class="metadata-item">
                            <i class="fab fa-facebook"></i>
                            <span>${this.escapeHtml(p.fb_page_name)}</span>
                        </div>
                    ` : ''}
                    ${p.contact_phone_number ? `
                        <div class="metadata-item">
                            <i class="fas fa-phone"></i>
                            <span>${this.escapeHtml(p.contact_phone_number)}</span>
                        </div>
                    ` : ''}
                    ${p.public_email ? `
                        <div class="metadata-item">
                            <i class="fas fa-envelope"></i>
                            <span>${this.escapeHtml(p.public_email)}</span>
                        </div>
                    ` : ''}
                    ${p.city_name ? `
                        <div class="metadata-item">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${this.escapeHtml(p.city_name)}</span>
                        </div>
                    ` : ''}
                </div>
                
                <!-- Botões de Ação -->
                <div class="profile-actions">
                    <button class="btn btn-primary" id="btn-analyze-ai" data-username="${this.escapeHtml(p.username)}">
                        <i class="fas fa-brain"></i>
                        Analisar com IA
                    </button>
                    <button class="btn btn-secondary" id="btn-track-activities" data-username="${this.escapeHtml(p.username)}">
                        <i class="fas fa-search"></i>
                        Rastrear Atividades
                    </button>
                    <button class="btn btn-secondary" id="btn-osint-search" data-username="${this.escapeHtml(p.username)}">
                        <i class="fas fa-user-secret"></i>
                        OSINT
                    </button>
                </div>
                
                <!-- Última atualização -->
                <div class="profile-footer">
                    <small>
                        <i class="far fa-clock"></i>
                        Atualizado: ${this.formatDate(new Date())}
                    </small>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza badge de saúde da conta
     * @param {number} score - Score de 0-100
     * @returns {string} HTML
     */
    renderHealthBadge(score) {
        let colorClass = 'success';
        let label = 'Saudável';

        if (score < 30) {
            colorClass = 'danger';
            label = 'Risco Alto';
        } else if (score < 60) {
            colorClass = 'warning';
            label = 'Atenção';
        }

        return `
            <div class="profile-health-badge health-badge--${colorClass}">
                <i class="fas fa-shield-alt"></i>
                <span>Saúde da Conta: ${score}% - ${label}</span>
            </div>
        `;
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Botão Analisar com IA
        const btnAI = this.container.querySelector('#btn-analyze-ai');
        if (btnAI) {
            btnAI.addEventListener('click', () => {
                const username = btnAI.dataset.username;
                this.analyzeWithAI(username);
            });
        }

        // Botão Rastrear Atividades
        const btnTrack = this.container.querySelector('#btn-track-activities');
        if (btnTrack) {
            btnTrack.addEventListener('click', () => {
                const username = btnTrack.dataset.username;
                this.trackActivities(username);
            });
        }

        // Botão OSINT
        const btnOSINT = this.container.querySelector('#btn-osint-search');
        if (btnOSINT) {
            btnOSINT.addEventListener('click', () => {
                const username = btnOSINT.dataset.username;
                this.runOSINTSearch(username);
            });
        }
    }

    /**
     * Analisa perfil com IA
     * @param {string} username - Username
     */
    async analyzeWithAI(username) {
        const loading = this.notifications.loading(`Analisando @${username} com IA...`);

        try {
            const [sentiment, predictions, visual] = await Promise.allSettled([
                this.api.analyzeSentiment(username),
                this.api.getPredictions(username),
                this.api.analyzeVisual(username)
            ]);

            if (sentiment.status === 'fulfilled' && sentiment.value.success) {
                this.state.set('sentiment', sentiment.value);
            }

            if (predictions.status === 'fulfilled' && predictions.value.success) {
                this.state.set('predictions', predictions.value);
            }

            if (visual.status === 'fulfilled' && visual.value.success) {
                this.state.set('visualAnalysis', visual.value);
            }

            loading.success('Análise de IA concluída!');

            // Navegar para tab de inteligência
            window.location.hash = '#sentiment';

        } catch (error) {
            loading.error(`Erro: ${error.message}`);
        }
    }

    /**
     * Inicia rastreamento de atividades
     * @param {string} username - Username
     */
    async trackActivities(username) {
        // Redirecionar para tab de rastreamento
        window.location.hash = '#tracking';

        // Preencher campo de username
        setTimeout(() => {
            const input = document.getElementById('targetUsername');
            if (input) {
                input.value = username;
                input.focus();
            }
        }, 100);
    }

    /**
     * Executa busca OSINT
     * @param {string} username - Username
     */
    async runOSINTSearch(username) {
        const loading = this.notifications.loading(`Executando OSINT para @${username}...`);

        try {
            const [health, crossPlatform] = await Promise.allSettled([
                this.api.getAccountHealth(username),
                this.api.crossPlatformSearch(username)
            ]);

            if (health.status === 'fulfilled' && health.value.success) {
                this.state.set('osint.accountHealth', health.value);
            }

            if (crossPlatform.status === 'fulfilled' && crossPlatform.value.success) {
                this.state.set('osint.crossPlatform', crossPlatform.value);
            }

            loading.success('Busca OSINT concluída!');
            window.location.hash = '#osint';

        } catch (error) {
            loading.error(`Erro: ${error.message}`);
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
     * Formata número
     * @param {number} num - Número
     * @returns {string}
     */
    formatNumber(num) {
        if (!num) return '0';
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toLocaleString('pt-BR');
    }

    /**
     * Formata bio com links e hashtags
     * @param {string} bio - Bio
     * @returns {string}
     */
    formatBio(bio) {
        if (!bio) return '';

        let formatted = this.escapeHtml(bio);

        // Converter hashtags em links
        formatted = formatted.replace(/#(\w+)/g, '<a href="https://instagram.com/explore/tags/$1" target="_blank" class="bio-hashtag">#$1</a>');

        // Converter @mentions em links
        formatted = formatted.replace(/@(\w+)/g, '<a href="https://instagram.com/$1" target="_blank" class="bio-mention">@$1</a>');

        // Converter URLs (simplificado)
        formatted = formatted.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');

        // Converter quebras de linha
        formatted = formatted.replace(/\n/g, '<br>');

        return formatted;
    }

    /**
     * Extrai domínio de URL
     * @param {string} url - URL completa
     * @returns {string}
     */
    extractDomain(url) {
        try {
            const domain = new URL(url).hostname.replace('www.', '');
            return domain;
        } catch {
            return url;
        }
    }

    /**
     * Formata data
     * @param {Date} date - Data
     * @returns {string}
     */
    formatDate(date) {
        return date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Factory function
export function createProfileCard(container) {
    const card = new ProfileCard(container);
    card.init();
    return card;
}

export default ProfileCard;
