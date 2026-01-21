/**
 * ChatWidget.js - Componente de Chat/Anotações Investigativas
 * 
 * Implementa uma interface de chat estilo mensageiro para:
 * 1. Registrar anotações sobre o perfil investigado
 * 2. Interface para futura integração com assistente de IA
 * 
 * @module ChatWidget
 */

import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export function createChatWidget(container) {
    return new ChatWidget(container);
}

class ChatWidget {
    constructor(container) {
        this.container = container;
        this.state = getStateManager();
        this.notifications = getNotificationService();
        
        this.messages = [];
        this.currentUser = null;
        
        this.init();
    }

    init() {
        this.render();
        this.setupEventListeners();
        
        // Inscrever-se para mudanças de usuário
        this.state.subscribe('currentUser', (username) => {
            this.currentUser = username;
            this.loadMessages(username);
            this.updateHeader(username);
        });
        
        // Carregar usuário inicial se houver
        const initialUser = this.state.get('currentUser');
        if (initialUser) {
            this.currentUser = initialUser;
            this.loadMessages(initialUser);
            this.updateHeader(initialUser);
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="chat-interface">
                <!-- Sidebar do Chat (Lista de Conversas) -->
                <div class="chat-sidebar">
                    <div class="chat-sidebar-header">
                        <h3>Investigações</h3>
                        <button class="btn-icon" title="Nova Anotação">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                    <div class="chat-search">
                        <i class="fas fa-search"></i>
                        <input type="text" placeholder="Buscar notas...">
                    </div>
                    <div class="chat-contacts-list">
                        <!-- Lista dinâmica -->
                        <div class="chat-contact active">
                            <div class="contact-avatar">
                                <i class="fas fa-user-secret"></i>
                            </div>
                            <div class="contact-info">
                                <div class="contact-name">Anotações do Alvo</div>
                                <div class="contact-last-msg">Registro de evidências...</div>
                            </div>
                        </div>
                        <div class="chat-contact">
                            <div class="contact-avatar system">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div class="contact-info">
                                <div class="contact-name">Assistente IA</div>
                                <div class="contact-last-msg">Análise concluída.</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Área Principal do Chat -->
                <div class="chat-main">
                    <div class="chat-header">
                        <div class="chat-header-info">
                            <div class="chat-avatar">
                                <i class="fas fa-user-secret"></i>
                            </div>
                            <div class="chat-title">
                                <h3 id="chat-target-name">Selecione um perfil</h3>
                                <span class="chat-status">Online</span>
                            </div>
                        </div>
                        <div class="chat-header-actions">
                            <button class="btn-icon"><i class="fas fa-search"></i></button>
                            <button class="btn-icon"><i class="fas fa-paperclip"></i></button>
                            <button class="btn-icon"><i class="fas fa-ellipsis-v"></i></button>
                        </div>
                    </div>

                    <div class="chat-messages" id="chat-messages-area">
                        <!-- Mensagens serão inseridas aqui -->
                        <div class="message-date-divider">
                            <span>Hoje</span>
                        </div>
                        <div class="message system">
                            <div class="message-content">
                                <p>Inicie suas anotações investigativas sobre este perfil.</p>
                                <span class="message-time">10:00</span>
                            </div>
                        </div>
                    </div>

                    <div class="chat-input-area">
                        <button class="btn-icon"><i class="far fa-smile"></i></button>
                        <input type="text" id="chat-input" placeholder="Digite uma anotação ou comando...">
                        <button class="btn-send" id="btn-send-msg">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        const input = this.container.querySelector('#chat-input');
        const sendBtn = this.container.querySelector('#btn-send-msg');
        
        const sendMessage = () => {
            const text = input.value.trim();
            if (text) {
                this.addMessage(text, 'sent');
                input.value = '';
                this.saveMessages();
            }
        };

        sendBtn.addEventListener('click', sendMessage);
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    addMessage(text, type = 'sent') {
        const messagesArea = this.container.querySelector('#chat-messages-area');
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;
        msgDiv.innerHTML = `
            <div class="message-content">
                <p>${this.escapeHtml(text)}</p>
                <span class="message-time">${time}</span>
            </div>
        `;
        
        messagesArea.appendChild(msgDiv);
        messagesArea.scrollTop = messagesArea.scrollHeight;
        
        this.messages.push({ text, type, timestamp: new Date().toISOString() });
    }

    /**
     * Recebe uma mensagem do sistema ou IA
     * @param {string} text - Conteúdo da mensagem
     */
    receiveMessage(text) {
        this.addMessage(text, 'received');
        
        // Incrementar badge se não estiver na aba chat
        const activeTab = this.state.get('ui.activeTab');
        if (activeTab !== 'chat') {
            const current = this.state.get('notifications.chat') || 0;
            this.state.set('notifications.chat', current + 1);
        }
    }

    loadMessages(username) {
        // Carregar histórico de mensagens do armazenamento local
        const key = `chat_history_${username}`;
        const saved = localStorage.getItem(key);
        const messagesArea = this.container.querySelector('#chat-messages-area');
        
        // Limpar mensagens atuais (exceto a inicial de sistema)
        messagesArea.innerHTML = `
            <div class="message-date-divider">
                <span>Histórico</span>
            </div>
            <div class="message system">
                <div class="message-content">
                    <p>Histórico de anotações para @${username}</p>
                    <span class="message-time">Sistema</span>
                </div>
            </div>
        `;
        
        if (saved) {
            this.messages = JSON.parse(saved);
            this.messages.forEach(msg => {
                const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const msgDiv = document.createElement('div');
                msgDiv.className = `message ${msg.type}`;
                msgDiv.innerHTML = `
                    <div class="message-content">
                        <p>${this.escapeHtml(msg.text)}</p>
                        <span class="message-time">${time}</span>
                    </div>
                `;
                messagesArea.appendChild(msgDiv);
            });
            messagesArea.scrollTop = messagesArea.scrollHeight;
        } else {
            this.messages = [];
        }
    }

    saveMessages() {
        if (this.currentUser) {
            const key = `chat_history_${this.currentUser}`;
            localStorage.setItem(key, JSON.stringify(this.messages));
        }
    }

    updateHeader(username) {
        const title = this.container.querySelector('#chat-target-name');
        if (title) {
            title.textContent = `Anotações: @${username}`;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
