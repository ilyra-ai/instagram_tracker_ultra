/**
 * NotificationService.js - Serviço de Notificações
 * 
 * Gerencia toasts, alertas e notificações em tempo real.
 * Integra com SweetAlert2 quando disponível.
 * 
 * @module NotificationService
 * @version 1.0.0
 */

export class NotificationService {
    /**
     * Cria uma instância do NotificationService
     * @param {Object} options - Opções de configuração
     */
    constructor(options = {}) {
        this.options = {
            position: options.position || 'top-right',
            defaultDuration: options.defaultDuration || 5000,
            maxToasts: options.maxToasts || 5,
            ...options
        };

        this.toasts = new Map();
        this.container = null;

        // Inicializar container
        this.createContainer();
    }

    /**
     * Cria o container de toasts
     */
    createContainer() {
        // Verificar se já existe
        this.container = document.querySelector('.toast-container');

        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }

    /**
     * Mostra um toast
     * @param {Object} options - Opções do toast
     * @returns {string} ID do toast
     */
    show(options) {
        const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        const toast = {
            id,
            type: options.type || 'info',
            title: options.title || '',
            message: options.message || '',
            icon: options.icon || this.getDefaultIcon(options.type),
            duration: options.duration ?? this.options.defaultDuration,
            closable: options.closable ?? true,
            actions: options.actions || [],
            ...options
        };

        // Limitar número de toasts
        if (this.toasts.size >= this.options.maxToasts) {
            const oldestId = this.toasts.keys().next().value;
            this.dismiss(oldestId);
        }

        // Criar elemento
        const element = this.createToastElement(toast);
        this.container.appendChild(element);

        // Armazenar
        this.toasts.set(id, { ...toast, element });

        // Auto-dismiss
        if (toast.duration > 0) {
            setTimeout(() => {
                this.dismiss(id);
            }, toast.duration);
        }

        return id;
    }

    /**
     * Cria elemento DOM do toast
     * @param {Object} toast - Configuração do toast
     * @returns {HTMLElement}
     */
    createToastElement(toast) {
        const element = document.createElement('div');
        element.className = `toast ${toast.type}`;
        element.id = toast.id;

        element.innerHTML = `
            <div class="toast__icon">
                <i class="fas ${toast.icon}"></i>
            </div>
            <div class="toast__content">
                ${toast.title ? `<div class="toast__title">${this.escapeHtml(toast.title)}</div>` : ''}
                <div class="toast__message">${this.escapeHtml(toast.message)}</div>
                ${this.createActionsHtml(toast.actions)}
            </div>
            ${toast.closable ? `
                <button class="toast__close" aria-label="Fechar">
                    <i class="fas fa-times"></i>
                </button>
            ` : ''}
        `;

        // Event listeners
        if (toast.closable) {
            element.querySelector('.toast__close').addEventListener('click', () => {
                this.dismiss(toast.id);
            });
        }

        // Actions listeners
        toast.actions.forEach((action, index) => {
            const btn = element.querySelector(`[data-action-index="${index}"]`);
            if (btn && action.onClick) {
                btn.addEventListener('click', () => {
                    action.onClick();
                    if (action.dismissOnClick !== false) {
                        this.dismiss(toast.id);
                    }
                });
            }
        });

        return element;
    }

    /**
     * Cria HTML para ações do toast
     * @param {Array} actions - Lista de ações
     * @returns {string} HTML
     */
    createActionsHtml(actions) {
        if (!actions || actions.length === 0) return '';

        const buttonsHtml = actions.map((action, index) => `
            <button class="toast__action btn btn-small ${action.class || ''}" 
                    data-action-index="${index}">
                ${action.label}
            </button>
        `).join('');

        return `<div class="toast__actions">${buttonsHtml}</div>`;
    }

    /**
     * Remove um toast
     * @param {string} id - ID do toast
     */
    dismiss(id) {
        const toast = this.toasts.get(id);
        if (!toast) return;

        // Animação de saída
        toast.element.style.animation = 'slideOut 0.3s ease forwards';

        setTimeout(() => {
            toast.element.remove();
            this.toasts.delete(id);
        }, 300);
    }

    /**
     * Remove todos os toasts
     */
    dismissAll() {
        for (const id of this.toasts.keys()) {
            this.dismiss(id);
        }
    }

    /**
     * Obtém ícone padrão por tipo
     * @param {string} type - Tipo do toast
     * @returns {string} Classe do ícone
     */
    getDefaultIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    /**
     * Escapa HTML para prevenir XSS
     * @param {string} text - Texto para escapar
     * @returns {string} Texto escapado
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ==========================================================================
    // MÉTODOS DE CONVENIÊNCIA
    // ==========================================================================

    /**
     * Mostra toast de sucesso
     * @param {string} message - Mensagem
     * @param {string} title - Título opcional
     * @param {Object} options - Opções extras
     * @returns {string} ID do toast
     */
    success(message, title = 'Sucesso', options = {}) {
        return this.show({
            type: 'success',
            title,
            message,
            ...options
        });
    }

    /**
     * Mostra toast de erro
     * @param {string} message - Mensagem
     * @param {string} title - Título opcional
     * @param {Object} options - Opções extras
     * @returns {string} ID do toast
     */
    error(message, title = 'Erro', options = {}) {
        return this.show({
            type: 'error',
            title,
            message,
            duration: options.duration ?? 0, // Erros não auto-dismiss
            ...options
        });
    }

    /**
     * Mostra toast de warning
     * @param {string} message - Mensagem
     * @param {string} title - Título opcional
     * @param {Object} options - Opções extras
     * @returns {string} ID do toast
     */
    warning(message, title = 'Atenção', options = {}) {
        return this.show({
            type: 'warning',
            title,
            message,
            ...options
        });
    }

    /**
     * Mostra toast de info
     * @param {string} message - Mensagem
     * @param {string} title - Título opcional
     * @param {Object} options - Opções extras
     * @returns {string} ID do toast
     */
    info(message, title = '', options = {}) {
        return this.show({
            type: 'info',
            title,
            message,
            ...options
        });
    }

    /**
     * Mostra toast de loading
     * @param {string} message - Mensagem
     * @returns {Object} Objeto com update e dismiss
     */
    loading(message = 'Carregando...') {
        const id = this.show({
            type: 'info',
            message,
            icon: 'fa-spinner fa-spin',
            duration: 0,
            closable: false
        });

        return {
            id,
            update: (newMessage) => {
                const toast = this.toasts.get(id);
                if (toast) {
                    toast.element.querySelector('.toast__message').textContent = newMessage;
                }
            },
            dismiss: () => this.dismiss(id),
            success: (message, title) => {
                this.dismiss(id);
                return this.success(message, title);
            },
            error: (message, title) => {
                this.dismiss(id);
                return this.error(message, title);
            }
        };
    }

    // ==========================================================================
    // MODAIS E CONFIRMAÇÕES
    // ==========================================================================

    /**
     * Mostra modal de confirmação
     * @param {Object} options - Opções do modal
     * @returns {Promise<boolean>} True se confirmou
     */
    async confirm(options) {
        const {
            title = 'Confirmar',
            message = 'Você tem certeza?',
            confirmText = 'Sim',
            cancelText = 'Cancelar',
            type = 'warning',
            icon = null
        } = options;

        // Verificar se SweetAlert2 está disponível
        if (window.Swal) {
            const result = await Swal.fire({
                title,
                text: message,
                icon: type,
                showCancelButton: true,
                confirmButtonText: confirmText,
                cancelButtonText: cancelText,
                confirmButtonColor: '#667eea',
                cancelButtonColor: '#6c757d'
            });

            return result.isConfirmed;
        }

        // Fallback para confirm nativo
        return window.confirm(`${title}\n\n${message}`);
    }

    /**
     * Mostra modal de alerta
     * @param {Object} options - Opções do modal
     * @returns {Promise<void>}
     */
    async alert(options) {
        const {
            title = 'Aviso',
            message = '',
            type = 'info'
        } = options;

        // Verificar se SweetAlert2 está disponível
        if (window.Swal) {
            await Swal.fire({
                title,
                text: message,
                icon: type,
                confirmButtonColor: '#667eea'
            });
            return;
        }

        // Fallback para alert nativo
        window.alert(`${title}\n\n${message}`);
    }

    /**
     * Mostra modal de input
     * @param {Object} options - Opções do modal
     * @returns {Promise<string|null>} Valor inserido ou null se cancelou
     */
    async prompt(options) {
        const {
            title = 'Digite',
            message = '',
            placeholder = '',
            defaultValue = '',
            inputType = 'text'
        } = options;

        // Verificar se SweetAlert2 está disponível
        if (window.Swal) {
            const result = await Swal.fire({
                title,
                text: message,
                input: inputType,
                inputPlaceholder: placeholder,
                inputValue: defaultValue,
                showCancelButton: true,
                confirmButtonColor: '#667eea',
                cancelButtonColor: '#6c757d'
            });

            return result.isConfirmed ? result.value : null;
        }

        // Fallback para prompt nativo
        return window.prompt(`${title}\n${message}`, defaultValue);
    }

    /**
     * Mostra modal de progresso
     * @param {Object} options - Opções
     * @returns {Object} Objeto para controlar o progresso
     */
    progress(options = {}) {
        const {
            title = 'Processando...',
            text = '',
            allowClose = false
        } = options;

        // Verificar se SweetAlert2 está disponível
        if (window.Swal) {
            Swal.fire({
                title,
                text,
                allowOutsideClick: allowClose,
                allowEscapeKey: allowClose,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            return {
                update: (newTitle, newText) => {
                    if (newTitle) Swal.getTitle().textContent = newTitle;
                    if (newText) Swal.getHtmlContainer().textContent = newText;
                },
                close: () => Swal.close(),
                success: (message) => {
                    Swal.fire({
                        icon: 'success',
                        title: 'Concluído!',
                        text: message,
                        confirmButtonColor: '#667eea'
                    });
                },
                error: (message) => {
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro!',
                        text: message,
                        confirmButtonColor: '#667eea'
                    });
                }
            };
        }

        // Fallback simples
        const id = this.loading(title);
        return {
            update: (newTitle) => id.update(newTitle),
            close: () => id.dismiss(),
            success: (message) => id.success(message),
            error: (message) => id.error(message)
        };
    }
}

// Singleton global
let notificationService = null;

/**
 * Obtém instância única do NotificationService
 * @param {Object} options - Opções de configuração
 * @returns {NotificationService}
 */
export function getNotificationService(options = {}) {
    if (!notificationService) {
        notificationService = new NotificationService(options);
    }
    return notificationService;
}

// Export default
export default NotificationService;
