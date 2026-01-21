/**
 * AISettingsPanel - Componente de Configuração de Provedores de IA
 * Instagram Intelligence System 2026
 * 
 * Permite configurar e selecionar providers de LLM (Gemini, Ollama)
 * e escolher modelos disponíveis.
 */

class AISettingsPanel {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = null;
        this.providers = {
            gemini: { available: false, configured: false, model: null, models: [] },
            ollama: { available: false, configured: false, model: null, models: [], base_url: null }
        };
        this.selectedProvider = 'gemini';
        this.isLoading = false;
    }

    async init() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.error(`AISettingsPanel: Container #${this.containerId} não encontrado`);
            return;
        }
        
        this.render();
        await this.fetchStatus();
        this.bindEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="ai-settings-panel">
                <div class="ai-settings-panel__header">
                    <h3 class="ai-settings-panel__title">
                        <i class="fas fa-robot"></i>
                        Configuração de IA Generativa
                    </h3>
                    <button class="ai-settings-panel__refresh" id="ai-refresh-btn" title="Atualizar Status">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
                
                <div class="ai-settings-panel__content">
                    <!-- Seletor de Provider -->
                    <div class="ai-settings-panel__section">
                        <label class="ai-settings-panel__label">Provedor de IA</label>
                        <div class="ai-settings-panel__providers">
                            <button class="ai-provider-btn ai-provider-btn--active" data-provider="gemini">
                                <i class="fas fa-cloud"></i>
                                <span>Google Gemini</span>
                                <span class="ai-provider-btn__status" id="gemini-status">●</span>
                            </button>
                            <button class="ai-provider-btn" data-provider="ollama">
                                <i class="fas fa-server"></i>
                                <span>Ollama (Local)</span>
                                <span class="ai-provider-btn__status" id="ollama-status">●</span>
                            </button>
                        </div>
                    </div>

                    <!-- Configuração Gemini -->
                    <div class="ai-settings-panel__provider-config" id="gemini-config">
                        <div class="ai-settings-panel__field">
                            <label class="ai-settings-panel__label">API Key</label>
                            <div class="ai-settings-panel__input-group">
                                <input type="password" 
                                       id="gemini-api-key" 
                                       class="ai-settings-panel__input" 
                                       placeholder="AIzaSy..."
                                       autocomplete="off">
                                <button class="ai-settings-panel__toggle-visibility" id="toggle-gemini-key">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </div>
                            <small class="ai-settings-panel__hint">
                                <a href="https://aistudio.google.com/app/apikey" target="_blank">
                                    Obter chave no Google AI Studio
                                </a>
                            </small>
                        </div>
                        
                        <div class="ai-settings-panel__field">
                            <label class="ai-settings-panel__label">Modelo</label>
                            <select id="gemini-model" class="ai-settings-panel__select">
                                <option value="">Carregando modelos...</option>
                            </select>
                        </div>
                    </div>

                    <!-- Configuração Ollama -->
                    <div class="ai-settings-panel__provider-config ai-settings-panel__provider-config--hidden" id="ollama-config">
                        <div class="ai-settings-panel__field">
                            <label class="ai-settings-panel__label">URL Base do Ollama</label>
                            <input type="text" 
                                   id="ollama-base-url" 
                                   class="ai-settings-panel__input" 
                                   placeholder="http://localhost:11434"
                                   value="http://localhost:11434">
                        </div>
                        
                        <div class="ai-settings-panel__field">
                            <label class="ai-settings-panel__label">Modelo</label>
                            <select id="ollama-model" class="ai-settings-panel__select">
                                <option value="">Nenhum modelo disponível</option>
                            </select>
                        </div>
                        
                        <div class="ai-settings-panel__info" id="ollama-info">
                            <i class="fas fa-info-circle"></i>
                            <span>Ollama não detectado. Certifique-se de que está rodando localmente.</span>
                        </div>
                    </div>

                    <!-- Status e Teste -->
                    <div class="ai-settings-panel__status-section">
                        <div class="ai-settings-panel__status" id="ai-status-message">
                            <i class="fas fa-circle-notch fa-spin"></i>
                            <span>Verificando status...</span>
                        </div>
                        
                        <button class="ai-settings-panel__test-btn" id="ai-test-btn">
                            <i class="fas fa-vial"></i>
                            Testar Conexão
                        </button>
                    </div>

                    <!-- Área de Teste -->
                    <div class="ai-settings-panel__test-area" id="ai-test-area" style="display: none;">
                        <textarea id="ai-test-prompt" 
                                  class="ai-settings-panel__textarea" 
                                  placeholder="Digite um prompt para testar...">Responda em 1 frase: O que é OSINT?</textarea>
                        <button class="ai-settings-panel__generate-btn" id="ai-generate-btn">
                            <i class="fas fa-magic"></i>
                            Gerar Resposta
                        </button>
                        <div class="ai-settings-panel__response" id="ai-test-response"></div>
                    </div>
                </div>
            </div>
        `;
    }

    async fetchStatus() {
        this.setLoading(true);
        try {
            const response = await fetch('/api/ai/status');
            const data = await response.json();
            
            if (data.success) {
                this.providers = data.providers;
                this.updateStatusUI();
                
                // Buscar modelos disponíveis
                await this.fetchModels();
            }
        } catch (error) {
            console.error('Erro ao buscar status de AI:', error);
            this.showStatus('error', 'Erro ao conectar com a API');
        }
        this.setLoading(false);
    }

    async fetchModels() {
        // Buscar modelos Gemini
        try {
            const geminiResp = await fetch('/api/ai/gemini/models');
            const geminiData = await geminiResp.json();
            if (geminiData.success) {
                this.providers.gemini.models = geminiData.models || [];
                this.providers.gemini.model = geminiData.current_model;
                this.populateModelSelect('gemini-model', this.providers.gemini.models, this.providers.gemini.model);
            }
        } catch (e) {
            console.warn('Não foi possível buscar modelos Gemini:', e);
        }

        // Buscar modelos Ollama
        try {
            const ollamaResp = await fetch('/api/ai/ollama/models');
            const ollamaData = await ollamaResp.json();
            if (ollamaData.success) {
                this.providers.ollama.models = ollamaData.models || [];
                this.providers.ollama.model = ollamaData.current_model;
                this.providers.ollama.base_url = ollamaData.base_url;
                this.populateModelSelect('ollama-model', this.providers.ollama.models, this.providers.ollama.model);
                
                if (ollamaData.base_url) {
                    document.getElementById('ollama-base-url').value = ollamaData.base_url;
                }
            }
        } catch (e) {
            console.warn('Não foi possível buscar modelos Ollama:', e);
        }
    }

    populateModelSelect(selectId, models, currentModel) {
        const select = document.getElementById(selectId);
        if (!select) return;

        select.innerHTML = '';
        
        if (models.length === 0) {
            select.innerHTML = '<option value="">Nenhum modelo disponível</option>';
            return;
        }

        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            option.textContent = model.displayName || model.name;
            if (model.name === currentModel) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }

    updateStatusUI() {
        // Atualizar indicadores de status
        const geminiStatus = document.getElementById('gemini-status');
        const ollamaStatus = document.getElementById('ollama-status');
        const ollamaInfo = document.getElementById('ollama-info');

        if (geminiStatus) {
            geminiStatus.className = 'ai-provider-btn__status';
            geminiStatus.classList.add(
                this.providers.gemini.configured ? 'ai-provider-btn__status--online' : 'ai-provider-btn__status--offline'
            );
        }

        if (ollamaStatus) {
            ollamaStatus.className = 'ai-provider-btn__status';
            ollamaStatus.classList.add(
                this.providers.ollama.configured ? 'ai-provider-btn__status--online' : 'ai-provider-btn__status--offline'
            );
        }

        if (ollamaInfo) {
            if (this.providers.ollama.configured) {
                ollamaInfo.innerHTML = `<i class="fas fa-check-circle"></i> <span>Ollama conectado em ${this.providers.ollama.base_url || 'localhost:11434'}</span>`;
                ollamaInfo.className = 'ai-settings-panel__info ai-settings-panel__info--success';
            } else {
                ollamaInfo.innerHTML = '<i class="fas fa-exclamation-circle"></i> <span>Ollama não detectado. Certifique-se de que está rodando.</span>';
                ollamaInfo.className = 'ai-settings-panel__info ai-settings-panel__info--warning';
            }
        }

        // Atualizar mensagem de status geral
        const activeProvider = this.providers[this.selectedProvider];
        if (activeProvider.configured) {
            this.showStatus('success', `${this.selectedProvider === 'gemini' ? 'Gemini' : 'Ollama'} configurado (${activeProvider.model || 'modelo não selecionado'})`);
        } else {
            this.showStatus('warning', `${this.selectedProvider === 'gemini' ? 'Gemini' : 'Ollama'} não configurado`);
        }
    }

    showStatus(type, message) {
        const statusEl = document.getElementById('ai-status-message');
        if (!statusEl) return;

        const icons = {
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle',
            loading: 'fa-circle-notch fa-spin'
        };

        statusEl.className = `ai-settings-panel__status ai-settings-panel__status--${type}`;
        statusEl.innerHTML = `<i class="fas ${icons[type] || icons.loading}"></i> <span>${message}</span>`;
    }

    setLoading(isLoading) {
        this.isLoading = isLoading;
        const refreshBtn = document.getElementById('ai-refresh-btn');
        if (refreshBtn) {
            refreshBtn.disabled = isLoading;
            refreshBtn.innerHTML = isLoading ? '<i class="fas fa-circle-notch fa-spin"></i>' : '<i class="fas fa-sync-alt"></i>';
        }
    }

    bindEvents() {
        // Refresh
        document.getElementById('ai-refresh-btn')?.addEventListener('click', () => this.fetchStatus());

        // Seleção de Provider
        document.querySelectorAll('.ai-provider-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const provider = e.currentTarget.dataset.provider;
                this.selectProvider(provider);
            });
        });

        // Toggle visibilidade da API Key
        document.getElementById('toggle-gemini-key')?.addEventListener('click', () => {
            const input = document.getElementById('gemini-api-key');
            const icon = document.querySelector('#toggle-gemini-key i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.className = 'fas fa-eye-slash';
            } else {
                input.type = 'password';
                icon.className = 'fas fa-eye';
            }
        });

        // Botão de Teste
        document.getElementById('ai-test-btn')?.addEventListener('click', () => {
            const testArea = document.getElementById('ai-test-area');
            testArea.style.display = testArea.style.display === 'none' ? 'block' : 'none';
        });

        // Gerar Resposta
        document.getElementById('ai-generate-btn')?.addEventListener('click', () => this.testGeneration());
    }

    selectProvider(provider) {
        this.selectedProvider = provider;

        // Atualizar botões
        document.querySelectorAll('.ai-provider-btn').forEach(btn => {
            btn.classList.toggle('ai-provider-btn--active', btn.dataset.provider === provider);
        });

        // Mostrar/ocultar configs
        document.getElementById('gemini-config')?.classList.toggle('ai-settings-panel__provider-config--hidden', provider !== 'gemini');
        document.getElementById('ollama-config')?.classList.toggle('ai-settings-panel__provider-config--hidden', provider !== 'ollama');

        this.updateStatusUI();
    }

    async testGeneration() {
        const prompt = document.getElementById('ai-test-prompt')?.value;
        if (!prompt) return;

        const responseEl = document.getElementById('ai-test-response');
        const btn = document.getElementById('ai-generate-btn');
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Gerando...';
        responseEl.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Aguardando resposta...';

        try {
            const endpoint = this.selectedProvider === 'gemini' ? '/api/ai/gemini/generate' : '/api/ai/ollama/generate';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, temperature: 0.7 })
            });

            const data = await response.json();
            
            if (data.success) {
                responseEl.innerHTML = `<strong>Modelo: ${data.model}</strong><br><br>${data.response || 'Resposta vazia'}`;
                responseEl.className = 'ai-settings-panel__response ai-settings-panel__response--success';
            } else {
                responseEl.innerHTML = `<strong>Erro:</strong> ${data.error}`;
                responseEl.className = 'ai-settings-panel__response ai-settings-panel__response--error';
            }
        } catch (error) {
            responseEl.innerHTML = `<strong>Erro de conexão:</strong> ${error.message}`;
            responseEl.className = 'ai-settings-panel__response ai-settings-panel__response--error';
        }

        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-magic"></i> Gerar Resposta';
    }
}

// Exportar para uso global
window.AISettingsPanel = AISettingsPanel;

// Auto-inicializar se o container existir
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('ai-settings-container');
    if (container) {
        const panel = new AISettingsPanel('ai-settings-container');
        panel.init();
        window.aiSettingsPanel = panel;
    }
});
