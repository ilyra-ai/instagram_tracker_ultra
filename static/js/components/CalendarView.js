/**
 * CalendarView.js - Calendário de Conteúdo
 * 
 * Exibe calendário com histórico de atividades:
 * - Visualização mensal de posts
 * - Cores por quantidade de atividade
 * - Preview de posts ao clicar
 * - Navegação entre meses
 * - Estatísticas do mês
 * 
 * @module CalendarView
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class CalendarView {
    /**
     * Cria uma instância do CalendarView
     * @param {HTMLElement} container - Container do calendário
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Data atual exibida
        this.currentDate = new Date();

        // Dados de atividades
        this.activityData = {};

        // Dia selecionado
        this.selectedDate = null;

        // Dias da semana
        this.weekDays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

        // Meses
        this.months = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ];

        // Bind methods
        this.render = this.render.bind(this);
        this.loadActivities = this.loadActivities.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças nas atividades
        this.state.subscribe('calendarActivities', (data) => {
            if (data) {
                this.activityData = data;
                this.render();
            }
        });

        // Render inicial
        this.render();
    }

    /**
     * Carrega atividades do mês
     */
    async loadActivities() {
        const username = this.state.get('currentUser');

        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth() + 1;

        const loading = this.notifications.loading(`Carregando atividades de ${this.months[month - 1]}...`);

        try {
            const result = await this.api.getCalendarActivities(username, { year, month });

            if (result.success) {
                this.activityData = result.activities || {};
                this.state.set('calendarActivities', this.activityData);
                loading.success('Atividades carregadas!');
            } else {
                loading.error(result.error || 'Erro ao carregar atividades');
            }
        } catch (error) {
            loading.error(`Erro: ${error.message}`);
        }
    }

    /**
     * Renderiza o calendário
     */
    render() {
        if (!this.container) return;

        this.container.innerHTML = this.renderCalendarWidget();
        this.attachEventListeners();
    }

    /**
     * Renderiza widget do calendário
     * @returns {string} HTML
     */
    renderCalendarWidget() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const monthStats = this.calculateMonthStats();

        return `
            <div class="widget calendar-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-calendar-alt"></i> Calendário de Conteúdo
                    </h3>
                    <div class="widget__actions">
                        <button class="widget__action-btn" id="btn-load-calendar" title="Carregar Atividades">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Navegação do Mês -->
                <div class="calendar-nav">
                    <button class="nav-btn" id="btn-prev-month" title="Mês Anterior">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <span class="calendar-title">
                        ${this.months[month]} ${year}
                    </span>
                    <button class="nav-btn" id="btn-next-month" title="Próximo Mês">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
                
                <!-- Grid do Calendário -->
                <div class="calendar-grid">
                    <!-- Cabeçalho da Semana -->
                    <div class="calendar-weekdays">
                        ${this.weekDays.map(day => `
                            <div class="weekday">${day}</div>
                        `).join('')}
                    </div>
                    
                    <!-- Dias do Mês -->
                    <div class="calendar-days">
                        ${this.renderDays()}
                    </div>
                </div>
                
                <!-- Legenda -->
                <div class="calendar-legend">
                    <span class="legend-label">Atividade:</span>
                    <div class="legend-items">
                        <div class="legend-item">
                            <span class="legend-color legend-color--none"></span>
                            <span>Nenhuma</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color legend-color--low"></span>
                            <span>Baixa</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color legend-color--medium"></span>
                            <span>Média</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color legend-color--high"></span>
                            <span>Alta</span>
                        </div>
                    </div>
                </div>
                
                <!-- Estatísticas do Mês -->
                <div class="calendar-stats">
                    <div class="stat-card">
                        <i class="fas fa-image"></i>
                        <span class="stat-value">${monthStats.posts}</span>
                        <span class="stat-label">Posts</span>
                    </div>
                    <div class="stat-card">
                        <i class="fas fa-circle-notch"></i>
                        <span class="stat-value">${monthStats.stories}</span>
                        <span class="stat-label">Stories</span>
                    </div>
                    <div class="stat-card">
                        <i class="fas fa-heart"></i>
                        <span class="stat-value">${this.formatNumber(monthStats.likes)}</span>
                        <span class="stat-label">Curtidas</span>
                    </div>
                    <div class="stat-card">
                        <i class="fas fa-comment"></i>
                        <span class="stat-value">${this.formatNumber(monthStats.comments)}</span>
                        <span class="stat-label">Comentários</span>
                    </div>
                </div>
                
                <!-- Preview do Dia Selecionado -->
                <div class="day-preview" id="day-preview">
                    ${this.selectedDate ? this.renderDayPreview() : this.renderEmptyPreview()}
                </div>
            </div>
        `;
    }

    /**
     * Renderiza dias do mês
     * @returns {string} HTML
     */
    renderDays() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();

        // Primeiro dia do mês
        const firstDay = new Date(year, month, 1);
        const startingDay = firstDay.getDay();

        // Último dia do mês
        const lastDay = new Date(year, month + 1, 0);
        const daysInMonth = lastDay.getDate();

        // Data de hoje
        const today = new Date();
        const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;

        let html = '';

        // Dias vazios antes do primeiro dia
        for (let i = 0; i < startingDay; i++) {
            html += '<div class="calendar-day calendar-day--empty"></div>';
        }

        // Dias do mês
        for (let day = 1; day <= daysInMonth; day++) {
            const dateKey = this.formatDateKey(year, month + 1, day);
            const dayData = this.activityData[dateKey] || {};
            const activityLevel = this.getActivityLevel(dayData);
            const isToday = isCurrentMonth && today.getDate() === day;
            const isSelected = this.selectedDate === dateKey;

            const classes = [
                'calendar-day',
                `calendar-day--${activityLevel}`,
                isToday ? 'calendar-day--today' : '',
                isSelected ? 'calendar-day--selected' : ''
            ].filter(Boolean).join(' ');

            html += `
                <div class="${classes}" data-date="${dateKey}">
                    <span class="day-number">${day}</span>
                    ${dayData.posts > 0 ? `
                        <span class="day-indicator">
                            <i class="fas fa-image"></i>
                            ${dayData.posts}
                        </span>
                    ` : ''}
                </div>
            `;
        }

        return html;
    }

    /**
     * Renderiza preview do dia selecionado
     * @returns {string} HTML
     */
    renderDayPreview() {
        const dayData = this.activityData[this.selectedDate] || {};
        const [year, month, day] = this.selectedDate.split('-').map(Number);
        const dateObj = new Date(year, month - 1, day);

        const formattedDate = dateObj.toLocaleDateString('pt-BR', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });

        const posts = dayData.items || [];

        return `
            <div class="preview-header">
                <h4>
                    <i class="fas fa-calendar-day"></i>
                    ${formattedDate}
                </h4>
                <button class="preview-close" id="btn-close-preview">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <div class="preview-content">
                ${posts.length > 0 ? `
                    <div class="preview-stats">
                        <span><i class="fas fa-image"></i> ${dayData.posts || 0} posts</span>
                        <span><i class="fas fa-heart"></i> ${this.formatNumber(dayData.likes || 0)}</span>
                        <span><i class="fas fa-comment"></i> ${dayData.comments || 0}</span>
                    </div>
                    
                    <div class="preview-posts">
                        ${posts.slice(0, 5).map(post => this.renderPostMini(post)).join('')}
                        ${posts.length > 5 ? `
                            <div class="more-posts">
                                +${posts.length - 5} mais
                            </div>
                        ` : ''}
                    </div>
                ` : `
                    <div class="no-activity">
                        <i class="far fa-calendar"></i>
                        <p>Nenhuma atividade registrada neste dia</p>
                    </div>
                `}
            </div>
        `;
    }

    /**
     * Renderiza preview vazio
     * @returns {string} HTML
     */
    renderEmptyPreview() {
        return `
            <div class="preview-empty">
                <i class="far fa-calendar-check"></i>
                <p>Clique em um dia para ver as atividades</p>
            </div>
        `;
    }

    /**
     * Renderiza mini card de post
     * @param {Object} post - Dados do post
     * @returns {string} HTML
     */
    renderPostMini(post) {
        const thumbnail = post.thumbnail_url || '';
        const type = post.type || 'post';
        const typeIcon = this.getPostTypeIcon(type);

        return `
            <div class="post-mini">
                <div class="post-mini__thumb">
                    ${thumbnail ? `
                        <img src="${this.escapeHtml(thumbnail)}" alt="Post" loading="lazy"
                             onerror="this.parentElement.innerHTML='<i class=\\'fas fa-image\\'></i>'">
                    ` : '<i class="fas fa-image"></i>'}
                    <span class="post-type">
                        <i class="fas ${typeIcon}"></i>
                    </span>
                </div>
                <div class="post-mini__info">
                    <span class="post-time">${this.formatTime(post.created_at)}</span>
                    <div class="post-engagement">
                        <span><i class="fas fa-heart"></i> ${this.formatNumber(post.likes || 0)}</span>
                        <span><i class="fas fa-comment"></i> ${post.comments || 0}</span>
                    </div>
                </div>
                ${post.url ? `
                    <a href="${post.url}" target="_blank" class="post-link">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                ` : ''}
            </div>
        `;
    }

    /**
     * Calcula estatísticas do mês
     * @returns {Object}
     */
    calculateMonthStats() {
        let posts = 0;
        let stories = 0;
        let likes = 0;
        let comments = 0;

        Object.values(this.activityData).forEach(day => {
            posts += day.posts || 0;
            stories += day.stories || 0;
            likes += day.likes || 0;
            comments += day.comments || 0;
        });

        return { posts, stories, likes, comments };
    }

    /**
     * Obtém nível de atividade
     * @param {Object} dayData - Dados do dia
     * @returns {string}
     */
    getActivityLevel(dayData) {
        const total = (dayData.posts || 0) + (dayData.stories || 0);

        if (total === 0) return 'none';
        if (total <= 1) return 'low';
        if (total <= 3) return 'medium';
        return 'high';
    }

    /**
     * Formata chave de data
     * @param {number} year - Ano
     * @param {number} month - Mês
     * @param {number} day - Dia
     * @returns {string}
     */
    formatDateKey(year, month, day) {
        return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    }

    /**
     * Obtém ícone do tipo de post
     * @param {string} type - Tipo
     * @returns {string}
     */
    getPostTypeIcon(type) {
        const icons = {
            'photo': 'fa-image',
            'video': 'fa-video',
            'carousel': 'fa-images',
            'reel': 'fa-film',
            'story': 'fa-circle-notch',
            'igtv': 'fa-tv'
        };
        return icons[type] || 'fa-image';
    }

    /**
     * Navega para o mês anterior
     */
    prevMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() - 1);
        this.selectedDate = null;
        this.activityData = {};
        this.render();
        this.loadActivities();
    }

    /**
     * Navega para o próximo mês
     */
    nextMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() + 1);
        this.selectedDate = null;
        this.activityData = {};
        this.render();
        this.loadActivities();
    }

    /**
     * Seleciona um dia
     * @param {string} dateKey - Chave da data
     */
    selectDay(dateKey) {
        this.selectedDate = dateKey;

        // Atualizar apenas o preview
        const previewEl = this.container.querySelector('#day-preview');
        if (previewEl) {
            previewEl.innerHTML = this.renderDayPreview();
            this.attachPreviewListeners();
        }

        // Atualizar classes dos dias
        const days = this.container.querySelectorAll('.calendar-day');
        days.forEach(day => {
            day.classList.toggle('calendar-day--selected', day.dataset.date === dateKey);
        });
    }

    /**
     * Fecha preview
     */
    closePreview() {
        this.selectedDate = null;

        const previewEl = this.container.querySelector('#day-preview');
        if (previewEl) {
            previewEl.innerHTML = this.renderEmptyPreview();
        }

        // Remover seleção dos dias
        const days = this.container.querySelectorAll('.calendar-day--selected');
        days.forEach(day => {
            day.classList.remove('calendar-day--selected');
        });
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Botão carregar
        const btnLoad = this.container.querySelector('#btn-load-calendar');
        if (btnLoad) {
            btnLoad.addEventListener('click', () => this.loadActivities());
        }

        // Navegação de mês
        const btnPrev = this.container.querySelector('#btn-prev-month');
        if (btnPrev) {
            btnPrev.addEventListener('click', () => this.prevMonth());
        }

        const btnNext = this.container.querySelector('#btn-next-month');
        if (btnNext) {
            btnNext.addEventListener('click', () => this.nextMonth());
        }

        // Clique nos dias
        const days = this.container.querySelectorAll('.calendar-day:not(.calendar-day--empty)');
        days.forEach(day => {
            day.addEventListener('click', () => {
                if (day.dataset.date) {
                    this.selectDay(day.dataset.date);
                }
            });
        });

        // Listeners do preview
        this.attachPreviewListeners();
    }

    /**
     * Anexa listeners do preview
     */
    attachPreviewListeners() {
        const btnClose = this.container.querySelector('#btn-close-preview');
        if (btnClose) {
            btnClose.addEventListener('click', () => this.closePreview());
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
     * Formata hora
     * @param {string|Date} date - Data
     * @returns {string}
     */
    formatTime(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
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
export function createCalendarView(container) {
    const calendar = new CalendarView(container);
    calendar.init();
    return calendar;
}

export default CalendarView;
