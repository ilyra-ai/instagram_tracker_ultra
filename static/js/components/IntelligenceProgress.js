/**
 * IntelligenceProgress.js - Componente de Progresso Inteligente 2026
 * 
 * Fornece feedback visual dinâmico e informativo durante o rastreamento:
 * - Barra de progresso com gradiente animado
 * - Logs de inteligência em tempo real (Contextual Tracking)
 * - Métricas de velocidade e estimativa
 * - Estética Premium Glassmorphism
 */

export class IntelligenceProgress {
    /**
     * @param {string} containerId 
     */
    constructor(containerId) {
        /** @type {HTMLElement | null} */
        this.container = document.getElementById(containerId);
        this.progress = 0;
        this.status = 'Iniciando...';
        /** @type {Array<{timestamp: string, message: string}>} */
        this.logs = [];
        this.startTime = null;
        this.isVisible = false;
    }

    /**
     * Inicializa o componente
     */
    init() {
        if (!this.container) return;
        this.render();
    }

    /**
     * Mostra o componente de progresso
     */
    show() {
        this.isVisible = true;
        this.startTime = Date.now();
        this.progress = 0;
        this.logs = [];
        this.render();
        if (this.container) {
            this.container.classList.add('active');
        }
    }

    /**
     * Oculta o componente
     */
    hide() {
        this.isVisible = false;
        const el = document.getElementById(this.container ? this.container.id : '');
        if (el) {
            el.classList.remove('active');
        }
    }

    /**
     * Atualiza o progresso e o status
     * @param {number} percent - Porcentagem (0-100)
     * @param {string} status - Mensagem de status atual
     * @param {string} logEntry - Entrada opcional para o log de inteligência
     */
    update(percent, status, logEntry = '') {
        this.progress = Math.min(100, Math.max(0, percent));
        this.status = status || 'Processando...';
        
        if (logEntry) {
            this.addLog(logEntry);
        }

        this.updateUI();
    }

    /**
     * Adiciona uma entrada ao log de inteligência
     * @param {string} message 
     */
    addLog(message) {
        const timestamp = new Date().toLocaleTimeString('pt-BR', { hour12: false });
        this.logs.unshift({ timestamp, message }); // Adiciona no topo
        if (this.logs.length > 5) this.logs.pop(); // Mantém apenas os 5 mais recentes
        this.renderLogs();
    }

    /**
     * Calcula a velocidade estimada (itens por segundo)
     */
    getVelocity() {
        if (!this.startTime) return '0/s';
        const elapsed = (Date.now() - this.startTime) / 1000;
        if (elapsed === 0) return '0/s';
        return `${(this.progress / elapsed).toFixed(1)}%/s`;
    }

    /**
     * Renderiza a estrutura base
     */
    render() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="intelligence-progress-card">
                <div class="progress-header">
                    <div class="progress-info">
                        <span class="progress-label">Rastreamento de Inteligência</span>
                        <span class="progress-status">${this.status}</span>
                    </div>
                    <div class="progress-percentage">${Math.round(this.progress)}%</div>
                </div>

                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: ${this.progress}%">
                        <div class="progress-bar-glow"></div>
                    </div>
                </div>

                <div class="progress-metrics">
                    <div class="metric-item">
                        <i class="fas fa-bolt"></i>
                        <span id="progress-velocity">${this.getVelocity()}</span>
                    </div>
                    <div class="metric-item">
                        <i class="fas fa-microchip"></i>
                        <span>AI Engine v2.6 Active</span>
                    </div>
                </div>

                <div class="intelligence-logs" id="intelligence-logs">
                    <!-- Logs serão inseridos aqui -->
                </div>
            </div>
        `;
    }

    /**
     * Atualiza apenas os elementos dinâmicos para performance
     */
    updateUI() {
        if (!this.container) return;
        
        const fill = this.container.querySelector('.progress-bar-fill');
        const percentage = this.container.querySelector('.progress-percentage');
        const status = this.container.querySelector('.progress-status');
        const velocity = this.container.querySelector('#progress-velocity');

        if (fill instanceof HTMLElement) fill.style.width = `${this.progress}%`;
        if (percentage) percentage.textContent = `${Math.round(this.progress)}%`;
        if (status) status.textContent = this.status;
        if (velocity) velocity.textContent = this.getVelocity();
    }

    /**
     * Renderiza a lista de logs
     */
    renderLogs() {
        const logContainer = this.container ? this.container.querySelector('#intelligence-logs') : null;
        if (!logContainer) return;

        logContainer.innerHTML = this.logs.map(log => `
            <div class="log-entry">
                <span class="log-time">[${log.timestamp}]</span>
                <span class="log-msg">${log.message}</span>
            </div>
        `).join('');
    }
}

export default IntelligenceProgress;
