/**
 * ResponsiveLayout.js - Layout Responsivo e Mobile
 * 
 * Gerencia responsividade do dashboard:
 * - Dashboard adapta de 3 colunas (desktop) → 1 coluna (mobile)
 * - Sidebar vira hamburger menu no mobile
 * - Widgets empilham verticalmente
 * - Touch-friendly: botões maiores, gestos de swipe
 * - Suporte a múltiplas resoluções: 320px, 768px, 1024px, 1440px
 * 
 * @module ResponsiveLayout
 * @version 1.0.0
 */

// Singleton instance
let instance = null;

export class ResponsiveLayout {
    /**
     * Cria uma instância do ResponsiveLayout
     */
    constructor() {
        if (instance) {
            return instance;
        }

        // Breakpoints
        this.breakpoints = {
            xs: 320,
            sm: 576,
            md: 768,
            lg: 1024,
            xl: 1280,
            xxl: 1440
        };

        // Estado atual
        this.currentBreakpoint = null;
        this.isMobile = false;
        this.isTablet = false;
        this.isDesktop = false;

        // Estado do menu mobile
        this.menuOpen = false;

        // Callbacks de mudança de breakpoint
        this.onChangeCallbacks = new Set();

        // Touch state
        this.touchStartX = 0;
        this.touchStartY = 0;

        // Bind methods
        this.handleResize = this.handleResize.bind(this);
        this.handleTouchStart = this.handleTouchStart.bind(this);
        this.handleTouchEnd = this.handleTouchEnd.bind(this);

        instance = this;
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Detectar tamanho inicial
        this.handleResize();

        // Listener de resize
        window.addEventListener('resize', this.debounce(this.handleResize, 100));

        // Touch events para gestos de swipe
        document.addEventListener('touchstart', this.handleTouchStart, { passive: true });
        document.addEventListener('touchend', this.handleTouchEnd, { passive: true });

        // Injetar estilos
        this.injectStyles();

        // Criar hamburger menu
        this.createHamburgerMenu();
    }

    /**
     * Handler de resize
     */
    handleResize() {
        const width = window.innerWidth;
        const newBreakpoint = this.getBreakpoint(width);

        // Se mudou o breakpoint
        if (newBreakpoint !== this.currentBreakpoint) {
            const oldBreakpoint = this.currentBreakpoint;
            this.currentBreakpoint = newBreakpoint;

            // Atualizar flags
            this.isMobile = width < this.breakpoints.md;
            this.isTablet = width >= this.breakpoints.md && width < this.breakpoints.lg;
            this.isDesktop = width >= this.breakpoints.lg;

            // Atualizar classes no body
            this.updateBodyClasses();

            // Callbacks
            this.triggerChange(newBreakpoint, oldBreakpoint);
        }

        // Atualizar grid columns
        this.updateGridColumns(width);
    }

    /**
     * Obtém breakpoint para largura
     * @param {number} width - Largura
     * @returns {string}
     */
    getBreakpoint(width) {
        if (width < this.breakpoints.sm) return 'xs';
        if (width < this.breakpoints.md) return 'sm';
        if (width < this.breakpoints.lg) return 'md';
        if (width < this.breakpoints.xl) return 'lg';
        if (width < this.breakpoints.xxl) return 'xl';
        return 'xxl';
    }

    /**
     * Atualiza classes no body
     */
    updateBodyClasses() {
        const body = document.body;

        // Remover classes antigas
        body.classList.remove('is-mobile', 'is-tablet', 'is-desktop');
        body.classList.remove('bp-xs', 'bp-sm', 'bp-md', 'bp-lg', 'bp-xl', 'bp-xxl');

        // Adicionar novas classes
        if (this.isMobile) body.classList.add('is-mobile');
        if (this.isTablet) body.classList.add('is-tablet');
        if (this.isDesktop) body.classList.add('is-desktop');
        body.classList.add(`bp-${this.currentBreakpoint}`);
    }

    /**
     * Atualiza colunas do grid
     * @param {number} width - Largura
     */
    updateGridColumns(width) {
        const dashboard = document.querySelector('.dashboard-grid, .widgets-grid');
        if (!dashboard) return;

        let columns = 1;
        if (width >= this.breakpoints.xl) columns = 3;
        else if (width >= this.breakpoints.lg) columns = 3;
        else if (width >= this.breakpoints.md) columns = 2;

        dashboard.style.setProperty('--grid-columns', columns);
    }

    // ==========================================================================
    // MENU MOBILE (HAMBURGER)
    // ==========================================================================

    /**
     * Cria hamburger menu
     */
    createHamburgerMenu() {
        // Verificar se já existe
        if (document.getElementById('mobile-menu-toggle')) return;

        // Criar botão hamburger
        const toggle = document.createElement('button');
        toggle.id = 'mobile-menu-toggle';
        toggle.className = 'mobile-menu-toggle';
        toggle.setAttribute('aria-label', 'Menu');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.innerHTML = `
            <span class="hamburger-line"></span>
            <span class="hamburger-line"></span>
            <span class="hamburger-line"></span>
        `;

        // Criar overlay
        const overlay = document.createElement('div');
        overlay.id = 'mobile-menu-overlay';
        overlay.className = 'mobile-menu-overlay';

        // Adicionar ao body
        document.body.appendChild(toggle);
        document.body.appendChild(overlay);

        // Event listeners
        toggle.addEventListener('click', () => this.toggleMenu());
        overlay.addEventListener('click', () => this.closeMenu());
    }

    /**
     * Abre/fecha menu mobile
     */
    toggleMenu() {
        if (this.menuOpen) {
            this.closeMenu();
        } else {
            this.openMenu();
        }
    }

    /**
     * Abre menu mobile
     */
    openMenu() {
        this.menuOpen = true;

        const toggle = document.getElementById('mobile-menu-toggle');
        const overlay = document.getElementById('mobile-menu-overlay');
        const sidebar = document.querySelector('.sidebar, .nav-sidebar');

        if (toggle) {
            toggle.classList.add('is-active');
            toggle.setAttribute('aria-expanded', 'true');
        }
        if (overlay) overlay.classList.add('is-active');
        if (sidebar) sidebar.classList.add('is-open');

        // Prevenir scroll do body
        document.body.style.overflow = 'hidden';
    }

    /**
     * Fecha menu mobile
     */
    closeMenu() {
        this.menuOpen = false;

        const toggle = document.getElementById('mobile-menu-toggle');
        const overlay = document.getElementById('mobile-menu-overlay');
        const sidebar = document.querySelector('.sidebar, .nav-sidebar');

        if (toggle) {
            toggle.classList.remove('is-active');
            toggle.setAttribute('aria-expanded', 'false');
        }
        if (overlay) overlay.classList.remove('is-active');
        if (sidebar) sidebar.classList.remove('is-open');

        // Restaurar scroll do body
        document.body.style.overflow = '';
    }

    // ==========================================================================
    // GESTOS DE SWIPE
    // ==========================================================================

    /**
     * Handler de touch start
     * @param {TouchEvent} e - Evento
     */
    handleTouchStart(e) {
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
    }

    /**
     * Handler de touch end
     * @param {TouchEvent} e - Evento
     */
    handleTouchEnd(e) {
        if (!this.isMobile) return;

        const touchEndX = e.changedTouches[0].clientX;
        const touchEndY = e.changedTouches[0].clientY;

        const deltaX = touchEndX - this.touchStartX;
        const deltaY = touchEndY - this.touchStartY;

        // Verificar se é um swipe horizontal (não vertical)
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
            if (deltaX > 0 && this.touchStartX < 30) {
                // Swipe direita a partir da borda esquerda → abrir menu
                this.openMenu();
            } else if (deltaX < 0 && this.menuOpen) {
                // Swipe esquerda com menu aberto → fechar menu
                this.closeMenu();
            }
        }
    }

    // ==========================================================================
    // HELPERS
    // ==========================================================================

    /**
     * Verifica se é mobile
     * @returns {boolean}
     */
    checkMobile() {
        return this.isMobile;
    }

    /**
     * Verifica se é tablet
     * @returns {boolean}
     */
    checkTablet() {
        return this.isTablet;
    }

    /**
     * Verifica se é desktop
     * @returns {boolean}
     */
    checkDesktop() {
        return this.isDesktop;
    }

    /**
     * Obtém breakpoint atual
     * @returns {string}
     */
    getBreakpointName() {
        return this.currentBreakpoint;
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
     * @param {string} newBreakpoint - Novo breakpoint
     * @param {string} oldBreakpoint - Breakpoint anterior
     */
    triggerChange(newBreakpoint, oldBreakpoint) {
        this.onChangeCallbacks.forEach(callback => {
            try {
                callback({
                    breakpoint: newBreakpoint,
                    previousBreakpoint: oldBreakpoint,
                    isMobile: this.isMobile,
                    isTablet: this.isTablet,
                    isDesktop: this.isDesktop
                });
            } catch (error) {
                console.error('Erro no callback de mudança de breakpoint:', error);
            }
        });
    }

    /**
     * Debounce helper
     * @param {Function} func - Função
     * @param {number} wait - Tempo de espera
     * @returns {Function}
     */
    debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // ==========================================================================
    // ESTILOS CSS
    // ==========================================================================

    /**
     * Injeta estilos CSS
     */
    injectStyles() {
        if (document.getElementById('responsive-layout-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'responsive-layout-styles';
        styles.textContent = `
            /* CSS Variables */
            :root {
                --grid-columns: 3;
                --sidebar-width: 280px;
                --header-height: 60px;
                --mobile-toggle-size: 44px;
            }
            
            /* Dashboard Grid */
            .dashboard-grid,
            .widgets-grid {
                display: grid;
                grid-template-columns: repeat(var(--grid-columns), 1fr);
                gap: var(--space-4, 1rem);
                padding: var(--space-4, 1rem);
            }
            
            /* Widget responsivo */
            .widget {
                min-width: 0;
                overflow: hidden;
            }
            
            /* Widget span full em mobile */
            .widget--full {
                grid-column: 1 / -1;
            }
            
            /* Hamburger Menu Toggle */
            .mobile-menu-toggle {
                position: fixed;
                top: 12px;
                left: 12px;
                z-index: 1000;
                width: var(--mobile-toggle-size);
                height: var(--mobile-toggle-size);
                padding: 10px;
                background: var(--bg-card, #fff);
                border: 1px solid var(--border, #e5e7eb);
                border-radius: var(--radius-md, 8px);
                cursor: pointer;
                display: none;
                flex-direction: column;
                justify-content: center;
                gap: 5px;
                box-shadow: var(--shadow-md, 0 4px 6px rgba(0,0,0,0.1));
            }
            
            .hamburger-line {
                display: block;
                width: 100%;
                height: 2px;
                background: var(--text-primary, #1f2937);
                border-radius: 1px;
                transition: all 0.3s ease;
            }
            
            .mobile-menu-toggle.is-active .hamburger-line:nth-child(1) {
                transform: translateY(7px) rotate(45deg);
            }
            
            .mobile-menu-toggle.is-active .hamburger-line:nth-child(2) {
                opacity: 0;
            }
            
            .mobile-menu-toggle.is-active .hamburger-line:nth-child(3) {
                transform: translateY(-7px) rotate(-45deg);
            }
            
            /* Menu Overlay */
            .mobile-menu-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                z-index: 998;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
            }
            
            .mobile-menu-overlay.is-active {
                opacity: 1;
                visibility: visible;
            }
            
            /* Sidebar responsiva */
            .sidebar,
            .nav-sidebar {
                position: fixed;
                top: 0;
                left: 0;
                width: var(--sidebar-width);
                height: 100vh;
                background: var(--bg-sidebar, #1f2937);
                z-index: 999;
                transform: translateX(-100%);
                transition: transform 0.3s ease;
                overflow-y: auto;
            }
            
            .sidebar.is-open,
            .nav-sidebar.is-open {
                transform: translateX(0);
            }
            
            /* Botões touch-friendly em mobile */
            .is-mobile .btn,
            .is-mobile button {
                min-height: 44px;
                min-width: 44px;
                padding: 12px 16px;
            }
            
            .is-mobile .btn--sm {
                min-height: 36px;
                min-width: 36px;
                padding: 8px 12px;
            }
            
            /* Cards touch-friendly */
            .is-mobile .card,
            .is-mobile .widget {
                padding: var(--space-4, 1rem);
            }
            
            .is-mobile .card__action,
            .is-mobile .widget__action-btn {
                min-width: 44px;
                min-height: 44px;
            }
            
            /* Media Queries */
            
            /* XS: < 576px */
            @media (max-width: 575px) {
                .dashboard-grid,
                .widgets-grid {
                    grid-template-columns: 1fr;
                    padding: var(--space-2, 0.5rem);
                    gap: var(--space-2, 0.5rem);
                }
                
                .mobile-menu-toggle {
                    display: flex;
                }
                
                .main-content {
                    padding-top: calc(var(--mobile-toggle-size) + 24px);
                }
                
                /* Esconder elementos não essenciais */
                .desktop-only {
                    display: none !important;
                }
                
                .widget__title {
                    font-size: 14px;
                }
                
                .search-advanced .search-input {
                    font-size: 16px; /* Evita zoom no iOS */
                }
            }
            
            /* SM: 576px - 767px */
            @media (min-width: 576px) and (max-width: 767px) {
                .dashboard-grid,
                .widgets-grid {
                    grid-template-columns: 1fr;
                }
                
                .mobile-menu-toggle {
                    display: flex;
                }
            }
            
            /* MD: 768px - 1023px */
            @media (min-width: 768px) and (max-width: 1023px) {
                .dashboard-grid,
                .widgets-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .mobile-menu-toggle {
                    display: flex;
                }
                
                .sidebar,
                .nav-sidebar {
                    width: 300px;
                }
            }
            
            /* LG: >= 1024px */
            @media (min-width: 1024px) {
                .dashboard-grid,
                .widgets-grid {
                    grid-template-columns: repeat(3, 1fr);
                }
                
                .mobile-menu-toggle {
                    display: none;
                }
                
                .mobile-menu-overlay {
                    display: none;
                }
                
                .sidebar,
                .nav-sidebar {
                    transform: translateX(0);
                }
                
                .main-content {
                    margin-left: var(--sidebar-width);
                }
            }
            
            /* XL: >= 1280px */
            @media (min-width: 1280px) {
                .dashboard-grid,
                .widgets-grid {
                    gap: var(--space-6, 1.5rem);
                    padding: var(--space-6, 1.5rem);
                }
            }
            
            /* XXL: >= 1440px */
            @media (min-width: 1440px) {
                .container,
                .main-content {
                    max-width: 1400px;
                    margin-left: auto;
                    margin-right: auto;
                }
                
                .main-content.has-sidebar {
                    max-width: calc(1400px + var(--sidebar-width));
                    padding-left: var(--sidebar-width);
                }
            }
            
            /* Preferência de redução de movimento */
            @media (prefers-reduced-motion: reduce) {
                .mobile-menu-toggle,
                .hamburger-line,
                .mobile-menu-overlay,
                .sidebar,
                .nav-sidebar {
                    transition: none;
                }
            }
            
            /* Orientação paisagem em mobile */
            @media (max-height: 500px) and (orientation: landscape) {
                .mobile-menu-toggle {
                    top: 8px;
                    left: 8px;
                }
                
                .sidebar,
                .nav-sidebar {
                    padding-top: var(--space-2, 0.5rem);
                }
            }
            
            /* Safe area insets para dispositivos com notch */
            @supports (padding: env(safe-area-inset-left)) {
                .mobile-menu-toggle {
                    left: max(12px, env(safe-area-inset-left));
                    top: max(12px, env(safe-area-inset-top));
                }
                
                .sidebar,
                .nav-sidebar {
                    padding-left: env(safe-area-inset-left);
                    padding-bottom: env(safe-area-inset-bottom);
                }
                
                .main-content {
                    padding-bottom: env(safe-area-inset-bottom);
                }
            }
        `;

        document.head.appendChild(styles);
    }

    /**
     * Destrói o componente
     */
    destroy() {
        window.removeEventListener('resize', this.handleResize);
        document.removeEventListener('touchstart', this.handleTouchStart);
        document.removeEventListener('touchend', this.handleTouchEnd);

        const toggle = document.getElementById('mobile-menu-toggle');
        const overlay = document.getElementById('mobile-menu-overlay');
        const styles = document.getElementById('responsive-layout-styles');

        if (toggle) toggle.remove();
        if (overlay) overlay.remove();
        if (styles) styles.remove();

        this.onChangeCallbacks.clear();
        instance = null;
    }
}

/**
 * Obtém instância singleton do ResponsiveLayout
 * @returns {ResponsiveLayout}
 */
export function getResponsiveLayout() {
    if (!instance) {
        instance = new ResponsiveLayout();
        instance.init();
    }
    return instance;
}

export default ResponsiveLayout;
