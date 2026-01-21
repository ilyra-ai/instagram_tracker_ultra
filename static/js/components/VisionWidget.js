/**
 * VisionWidget.js - Widget de Análise Visual com IA
 * 
 * Exibe análise de imagens/vídeos com:
 * - Galeria de posts analisados
 * - Categorias de objetos detectados
 * - Estatísticas de conteúdo visual
 * - Tags semânticas
 * - Nuvem de palavras dos objetos
 * 
 * @module VisionWidget
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class VisionWidget {
    /**
     * Cria uma instância do VisionWidget
     * @param {HTMLElement} container - Container do widget
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Dados de análise visual
        this.visualData = null;

        // Filtro atual
        this.currentFilter = 'all';

        // Bind methods
        this.render = this.render.bind(this);
        this.analyze = this.analyze.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças na análise visual
        this.state.subscribe('visualAnalysis', (data) => {
            this.visualData = data;
            this.render();
        });

        // Render inicial
        this.render();
    }

    /**
     * Analisa conteúdo visual
     */
    async analyze() {
        const username = this.state.get('currentUser');

        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        const loading = this.notifications.loading(`Analisando imagens de @${username}...`);

        try {
            const result = await this.api.analyzeVisual(username);

            if (result.success) {
                this.state.set('visualAnalysis', result);
                loading.success('Análise visual concluída!');
            } else {
                loading.error(result.error || 'Erro na análise visual');
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

        if (!this.visualData) {
            this.container.innerHTML = this.renderEmptyState();
            this.attachEventListeners();
            return;
        }

        this.container.innerHTML = this.renderVisionWidget();
        this.attachEventListeners();
    }

    /**
     * Renderiza estado vazio
     * @returns {string} HTML
     */
    renderEmptyState() {
        return `
            <div class="widget vision-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-eye"></i> Análise Visual (IA)
                    </h3>
                </div>
                
                <div class="vision-empty">
                    <div class="vision-empty__icon">
                        <i class="fas fa-camera-retro"></i>
                    </div>
                    <p>Clique para analisar o conteúdo visual do perfil</p>
                    <button class="btn btn-primary" id="btn-analyze-vision">
                        <i class="fas fa-magic"></i>
                        Analisar Imagens
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza widget com dados
     * @returns {string} HTML
     */
    renderVisionWidget() {
        const data = this.visualData;

        // Extrair dados
        const analyzedPosts = data.analyzed_posts || [];
        const categories = data.category_summary || {};
        const topObjects = data.top_objects || [];
        const colorPalette = data.dominant_colors || [];
        const semanticTags = data.semantic_tags || [];
        const profileSummary = data.profile_visual_summary || {};

        return `
            <div class="widget vision-widget">
                <div class="widget__header">
                    <h3 class="widget__title">
                        <i class="fas fa-eye"></i> Análise Visual (IA)
                    </h3>
                    <div class="widget__actions">
                        <span class="analysis-count">
                            <i class="fas fa-images"></i>
                            ${analyzedPosts.length} imagens
                        </span>
                        <button class="widget__action-btn" id="btn-refresh-vision" title="Atualizar">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Resumo Visual do Perfil -->
                ${profileSummary.description ? this.renderProfileSummary(profileSummary) : ''}
                
                <!-- Estatísticas de Categorias -->
                <div class="vision-section">
                    <h4>
                        <i class="fas fa-layer-group"></i>
                        Categorias de Conteúdo
                    </h4>
                    <div class="categories-grid">
                        ${this.renderCategoryCards(categories)}
                    </div>
                </div>
                
                <!-- Top Objetos Detectados -->
                ${topObjects.length > 0 ? `
                    <div class="vision-section">
                        <h4>
                            <i class="fas fa-cube"></i>
                            Objetos Mais Frequentes
                        </h4>
                        <div class="objects-cloud">
                            ${this.renderObjectsCloud(topObjects)}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Tags Semânticas -->
                ${semanticTags.length > 0 ? `
                    <div class="vision-section">
                        <h4>
                            <i class="fas fa-tags"></i>
                            Tags Semânticas
                        </h4>
                        <div class="semantic-tags">
                            ${semanticTags.map(tag => this.renderSemanticTag(tag)).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Paleta de Cores Dominante -->
                ${colorPalette.length > 0 ? `
                    <div class="vision-section">
                        <h4>
                            <i class="fas fa-palette"></i>
                            Paleta de Cores Dominante
                        </h4>
                        <div class="color-palette">
                            ${colorPalette.map(color => this.renderColorSwatch(color)).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Galeria de Posts Analisados -->
                ${analyzedPosts.length > 0 ? `
                    <div class="vision-section">
                        <h4>
                            <i class="fas fa-th"></i>
                            Galeria Analisada
                        </h4>
                        
                        <!-- Filtros -->
                        <div class="gallery-filters">
                            <button class="filter-btn ${this.currentFilter === 'all' ? 'active' : ''}" 
                                    data-filter="all">Todos</button>
                            ${Object.keys(categories).slice(0, 5).map(cat => `
                                <button class="filter-btn ${this.currentFilter === cat ? 'active' : ''}" 
                                        data-filter="${cat}">${this.formatCategoryName(cat)}</button>
                            `).join('')}
                        </div>
                        
                        <!-- Grid de Imagens -->
                        <div class="vision-gallery" id="vision-gallery">
                            ${this.renderGallery(analyzedPosts)}
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
     * Renderiza resumo visual do perfil
     * @param {Object} summary - Resumo
     * @returns {string} HTML
     */
    renderProfileSummary(summary) {
        return `
            <div class="vision-summary">
                <div class="summary-icon">
                    <i class="fas fa-lightbulb"></i>
                </div>
                <div class="summary-content">
                    <h4>Resumo Visual do Perfil</h4>
                    <p>${this.escapeHtml(summary.description)}</p>
                    ${summary.style ? `
                        <span class="summary-style">
                            <i class="fas fa-brush"></i>
                            Estilo: ${this.escapeHtml(summary.style)}
                        </span>
                    ` : ''}
                    ${summary.theme ? `
                        <span class="summary-theme">
                            <i class="fas fa-swatchbook"></i>
                            Tema: ${this.escapeHtml(summary.theme)}
                        </span>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Renderiza cards de categorias
     * @param {Object} categories - Categorias e contagens
     * @returns {string} HTML
     */
    renderCategoryCards(categories) {
        const entries = Object.entries(categories);

        if (entries.length === 0) {
            return '<p class="empty-message">Nenhuma categoria detectada</p>';
        }

        // Ordenar por contagem
        entries.sort((a, b) => b[1] - a[1]);

        const total = entries.reduce((sum, [, count]) => sum + count, 0);

        return entries.slice(0, 8).map(([category, count]) => {
            const percentage = ((count / total) * 100).toFixed(1);
            const icon = this.getCategoryIcon(category);

            return `
                <div class="category-card" data-category="${category}">
                    <div class="category-card__icon">
                        <i class="fas ${icon}"></i>
                    </div>
                    <div class="category-card__content">
                        <span class="category-name">${this.formatCategoryName(category)}</span>
                        <span class="category-count">${count} imagens</span>
                    </div>
                    <div class="category-card__bar">
                        <div class="bar-fill" style="width: ${percentage}%"></div>
                    </div>
                    <span class="category-percentage">${percentage}%</span>
                </div>
            `;
        }).join('');
    }

    /**
     * Renderiza nuvem de objetos
     * @param {Array} objects - Lista de objetos
     * @returns {string} HTML
     */
    renderObjectsCloud(objects) {
        const maxCount = Math.max(...objects.map(o => o.count || 1));

        return objects.slice(0, 20).map(obj => {
            const size = 0.8 + ((obj.count || 1) / maxCount) * 0.8;
            const opacity = 0.5 + ((obj.count || 1) / maxCount) * 0.5;

            return `
                <span class="object-tag" 
                      style="font-size: ${size}em; opacity: ${opacity}"
                      title="${obj.name}: ${obj.count} ocorrências">
                    ${this.escapeHtml(obj.name)}
                    <span class="object-count">${obj.count}</span>
                </span>
            `;
        }).join('');
    }

    /**
     * Renderiza tag semântica
     * @param {Object} tag - Dados da tag
     * @returns {string} HTML
     */
    renderSemanticTag(tag) {
        const name = typeof tag === 'string' ? tag : tag.name;
        const confidence = typeof tag === 'object' ? tag.confidence : null;

        return `
            <span class="semantic-tag">
                ${this.escapeHtml(name)}
                ${confidence ? `<span class="tag-confidence">${(confidence * 100).toFixed(0)}%</span>` : ''}
            </span>
        `;
    }

    /**
     * Renderiza amostra de cor
     * @param {Object|string} color - Dados da cor
     * @returns {string} HTML
     */
    renderColorSwatch(color) {
        const hex = typeof color === 'string' ? color : color.hex;
        const name = typeof color === 'object' ? color.name : null;
        const percentage = typeof color === 'object' ? color.percentage : null;

        return `
            <div class="color-swatch" 
                 style="background-color: ${hex}"
                 title="${name || hex}${percentage ? ` (${percentage}%)` : ''}">
                ${name ? `<span class="color-name">${name}</span>` : ''}
            </div>
        `;
    }

    /**
     * Renderiza galeria de imagens
     * @param {Array} posts - Posts analisados
     * @returns {string} HTML
     */
    renderGallery(posts) {
        // Filtrar por categoria se necessário
        let filtered = posts;
        if (this.currentFilter !== 'all') {
            filtered = posts.filter(p =>
                p.categories && p.categories.includes(this.currentFilter)
            );
        }

        if (filtered.length === 0) {
            return '<p class="empty-message">Nenhuma imagem nesta categoria</p>';
        }

        return filtered.slice(0, 12).map(post => this.renderGalleryItem(post)).join('');
    }

    /**
     * Renderiza item da galeria
     * @param {Object} post - Dados do post
     * @returns {string} HTML
     */
    renderGalleryItem(post) {
        const thumbnail = post.thumbnail_url || post.image_url || '';
        const objects = post.detected_objects || [];
        const mainCategory = post.main_category || post.categories?.[0] || 'unknown';

        return `
            <div class="gallery-item" data-post-id="${post.id || ''}">
                <div class="gallery-item__image">
                    ${thumbnail ? `
                        <img src="${this.escapeHtml(thumbnail)}" 
                             alt="Post analisado"
                             loading="lazy"
                             onerror="this.parentElement.innerHTML='<i class=\\'fas fa-image\\'></i>'">
                    ` : '<i class="fas fa-image"></i>'}
                    
                    <div class="gallery-item__overlay">
                        <span class="item-category">
                            <i class="fas ${this.getCategoryIcon(mainCategory)}"></i>
                            ${this.formatCategoryName(mainCategory)}
                        </span>
                        
                        ${objects.length > 0 ? `
                            <div class="item-objects">
                                ${objects.slice(0, 3).map(obj => `
                                    <span class="mini-tag">${obj.name || obj}</span>
                                `).join('')}
                                ${objects.length > 3 ? `<span class="mini-tag">+${objects.length - 3}</span>` : ''}
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                ${post.post_url ? `
                    <a href="${post.post_url}" target="_blank" class="gallery-item__link" title="Ver post">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                ` : ''}
            </div>
        `;
    }

    /**
     * Filtra galeria por categoria
     * @param {string} category - Categoria
     */
    filterGallery(category) {
        this.currentFilter = category;

        // Atualizar botões de filtro
        const buttons = this.container.querySelectorAll('.gallery-filters .filter-btn');
        buttons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === category);
        });

        // Re-renderizar galeria
        const galleryEl = this.container.querySelector('#vision-gallery');
        if (galleryEl && this.visualData) {
            galleryEl.innerHTML = this.renderGallery(this.visualData.analyzed_posts || []);
        }
    }

    /**
     * Obtém ícone da categoria
     * @param {string} category - Categoria
     * @returns {string}
     */
    getCategoryIcon(category) {
        const icons = {
            'person': 'fa-user',
            'people': 'fa-users',
            'selfie': 'fa-camera',
            'food': 'fa-utensils',
            'animal': 'fa-paw',
            'pet': 'fa-dog',
            'nature': 'fa-leaf',
            'landscape': 'fa-mountain',
            'travel': 'fa-plane',
            'beach': 'fa-umbrella-beach',
            'city': 'fa-city',
            'architecture': 'fa-building',
            'car': 'fa-car',
            'vehicle': 'fa-car-side',
            'sport': 'fa-football-ball',
            'fitness': 'fa-dumbbell',
            'fashion': 'fa-tshirt',
            'art': 'fa-palette',
            'music': 'fa-music',
            'party': 'fa-glass-cheers',
            'celebration': 'fa-birthday-cake',
            'work': 'fa-briefcase',
            'technology': 'fa-laptop',
            'home': 'fa-home',
            'product': 'fa-box',
            'text': 'fa-font',
            'meme': 'fa-laugh',
            'screenshot': 'fa-mobile-alt',
            'quote': 'fa-quote-right'
        };

        return icons[category?.toLowerCase()] || 'fa-image';
    }

    /**
     * Formata nome da categoria
     * @param {string} category - Categoria
     * @returns {string}
     */
    formatCategoryName(category) {
        if (!category) return 'Desconhecido';

        const names = {
            'person': 'Pessoa',
            'people': 'Pessoas',
            'selfie': 'Selfie',
            'food': 'Comida',
            'animal': 'Animal',
            'pet': 'Pet',
            'nature': 'Natureza',
            'landscape': 'Paisagem',
            'travel': 'Viagem',
            'beach': 'Praia',
            'city': 'Cidade',
            'architecture': 'Arquitetura',
            'car': 'Carro',
            'vehicle': 'Veículo',
            'sport': 'Esporte',
            'fitness': 'Fitness',
            'fashion': 'Moda',
            'art': 'Arte',
            'music': 'Música',
            'party': 'Festa',
            'celebration': 'Celebração',
            'work': 'Trabalho',
            'technology': 'Tecnologia',
            'home': 'Casa',
            'product': 'Produto',
            'text': 'Texto',
            'meme': 'Meme',
            'screenshot': 'Screenshot',
            'quote': 'Citação'
        };

        return names[category.toLowerCase()] || category.charAt(0).toUpperCase() + category.slice(1);
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        // Botão analisar
        const btnAnalyze = this.container.querySelector('#btn-analyze-vision');
        if (btnAnalyze) {
            btnAnalyze.addEventListener('click', () => this.analyze());
        }

        // Botão refresh
        const btnRefresh = this.container.querySelector('#btn-refresh-vision');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.analyze());
        }

        // Filtros de galeria
        const filterBtns = this.container.querySelectorAll('.gallery-filters .filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.filterGallery(btn.dataset.filter);
            });
        });

        // Clique em categorias
        const categoryCards = this.container.querySelectorAll('.category-card');
        categoryCards.forEach(card => {
            card.addEventListener('click', () => {
                this.filterGallery(card.dataset.category);
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
export function createVisionWidget(container) {
    const widget = new VisionWidget(container);
    widget.init();
    return widget;
}

export default VisionWidget;
