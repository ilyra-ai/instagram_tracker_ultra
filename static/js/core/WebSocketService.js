/**
 * WebSocketService.js - Serviço de WebSocket com Socket.IO
 * 
 * Gerencia conexões em tempo real:
 * - Conexão automática com reconexão
 * - Eventos de status de conexão
 * - Subscrição a canais/rooms
 * - Heartbeat para manter conexão viva
 * - Queue de mensagens offline
 * 
 * @module WebSocketService
 * @version 1.0.0
 */

import { getStateManager } from './StateManager.js';
import { getNotificationService } from './NotificationService.js';

// Singleton instance
let instance = null;

export class WebSocketService {
    /**
     * Cria uma instância do WebSocketService
     * @param {Object} options - Opções de configuração
     */
    constructor(options = {}) {
        if (instance) {
            return instance;
        }

        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Configurações
        this.config = {
            url: options.url || this.getWebSocketUrl(),
            reconnection: options.reconnection !== false,
            reconnectionAttempts: options.reconnectionAttempts || 10,
            reconnectionDelay: options.reconnectionDelay || 1000,
            reconnectionDelayMax: options.reconnectionDelayMax || 5000,
            timeout: options.timeout || 20000,
            autoConnect: options.autoConnect !== false
        };

        // Estado da conexão
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.reconnectTimer = null;

        // Listeners de eventos
        this.eventListeners = new Map();

        // Queue de mensagens offline
        this.offlineQueue = [];

        // Heartbeat
        this.heartbeatInterval = null;
        this.heartbeatTimeout = 30000;

        // Rooms/Canais subscritos
        this.subscribedRooms = new Set();

        // Bind methods
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.emit = this.emit.bind(this);
        this.on = this.on.bind(this);

        instance = this;

        // Auto-connect se configurado
        if (this.config.autoConnect) {
            this.connect();
        }
    }

    /**
     * Obtém URL do WebSocket
     * @returns {string}
     */
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}`;
    }

    /**
     * Conecta ao servidor WebSocket
     * @returns {Promise<boolean>}
     */
    async connect() {
        if (this.isConnected) {
            return true;
        }

        return new Promise((resolve, reject) => {
            try {
                // Verificar se Socket.IO está disponível
                if (typeof io === 'undefined') {
                    console.warn('Socket.IO não disponível, usando fallback');
                    this.initializeFallback();
                    resolve(false);
                    return;
                }

                // Criar conexão Socket.IO
                this.socket = io(this.config.url, {
                    reconnection: this.config.reconnection,
                    reconnectionAttempts: this.config.reconnectionAttempts,
                    reconnectionDelay: this.config.reconnectionDelay,
                    reconnectionDelayMax: this.config.reconnectionDelayMax,
                    timeout: this.config.timeout,
                    transports: ['websocket', 'polling']
                });

                // Event handlers
                this.socket.on('connect', () => {
                    this.handleConnect();
                    resolve(true);
                });

                this.socket.on('disconnect', (reason) => {
                    this.handleDisconnect(reason);
                });

                this.socket.on('connect_error', (error) => {
                    this.handleError(error);
                    if (this.reconnectAttempts === 0) {
                        reject(error);
                    }
                });

                this.socket.on('reconnect', (attemptNumber) => {
                    this.handleReconnect(attemptNumber);
                });

                this.socket.on('reconnect_attempt', (attemptNumber) => {
                    this.reconnectAttempts = attemptNumber;
                });

                this.socket.on('reconnect_error', (error) => {
                    console.error('Erro de reconexão:', error);
                });

                this.socket.on('reconnect_failed', () => {
                    this.handleReconnectFailed();
                });

                // Mensagens do servidor
                this.socket.on('message', (data) => {
                    this.handleMessage(data);
                });

                this.socket.on('notification', (data) => {
                    this.handleNotification(data);
                });

                this.socket.on('state_update', (data) => {
                    this.handleStateUpdate(data);
                });

                this.socket.on('error', (error) => {
                    this.handleError(error);
                });

            } catch (error) {
                console.error('Erro ao conectar WebSocket:', error);
                this.initializeFallback();
                reject(error);
            }
        });
    }

    /**
     * Inicializa fallback sem WebSocket
     */
    initializeFallback() {
        this.isConnected = false;
        this.state.set('wsConnected', false);
        this.state.set('wsStatus', 'fallback');

        console.log('WebSocket em modo fallback (polling)');

        // Iniciar polling como fallback
        this.startPolling();
    }

    /**
     * Inicia polling como fallback
     */
    startPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        this.pollingInterval = setInterval(() => {
            this.pollUpdates();
        }, 10000); // Poll a cada 10 segundos
    }

    /**
     * Faz polling de atualizações
     */
    async pollUpdates() {
        try {
            const response = await fetch('/api/updates/poll');
            if (response.ok) {
                const data = await response.json();
                if (data.updates && data.updates.length > 0) {
                    data.updates.forEach(update => {
                        this.handleMessage(update);
                    });
                }
            }
        } catch (error) {
            console.debug('Polling atualização falhou:', error);
        }
    }

    /**
     * Handler de conexão estabelecida
     */
    handleConnect() {
        this.isConnected = true;
        this.reconnectAttempts = 0;

        this.state.set('wsConnected', true);
        this.state.set('wsStatus', 'connected');

        console.log('WebSocket conectado');

        // Processar queue offline
        this.processOfflineQueue();

        // Re-subscrever rooms
        this.resubscribeRooms();

        // Iniciar heartbeat
        this.startHeartbeat();

        // Emitir evento
        this.triggerEvent('connect', { connected: true });
    }

    /**
     * Handler de desconexão
     * @param {string} reason - Razão da desconexão
     */
    handleDisconnect(reason) {
        this.isConnected = false;

        this.state.set('wsConnected', false);
        this.state.set('wsStatus', 'disconnected');

        console.log('WebSocket desconectado:', reason);

        // Parar heartbeat
        this.stopHeartbeat();

        // Emitir evento
        this.triggerEvent('disconnect', { reason });

        // Notificar apenas se foi inesperado
        if (reason === 'io server disconnect' || reason === 'transport close') {
            this.notifications.warning('Conexão em tempo real perdida');
        }
    }

    /**
     * Handler de reconexão
     * @param {number} attemptNumber - Número da tentativa
     */
    handleReconnect(attemptNumber) {
        console.log(`Reconectado após ${attemptNumber} tentativa(s)`);
        this.notifications.success('Conexão em tempo real restaurada');
    }

    /**
     * Handler de falha de reconexão
     */
    handleReconnectFailed() {
        console.error('Falha ao reconectar ao WebSocket');
        this.state.set('wsStatus', 'failed');
        this.notifications.error('Não foi possível reconectar. Recarregue a página.');
    }

    /**
     * Handler de erro
     * @param {Error} error - Erro
     */
    handleError(error) {
        console.error('Erro WebSocket:', error);
        this.triggerEvent('error', { error });
    }

    /**
     * Handler de mensagem
     * @param {Object} data - Dados da mensagem
     */
    handleMessage(data) {
        if (!data) return;

        const { type, payload } = data;

        // Emitir evento específico
        if (type) {
            this.triggerEvent(type, payload);
        }

        // Emitir evento genérico
        this.triggerEvent('message', data);
    }

    /**
     * Handler de notificação
     * @param {Object} data - Dados da notificação
     */
    handleNotification(data) {
        if (!data) return;

        const { type, title, message } = data;

        switch (type) {
            case 'success':
                this.notifications.success(message, title);
                break;
            case 'error':
                this.notifications.error(message, title);
                break;
            case 'warning':
                this.notifications.warning(message, title);
                break;
            case 'info':
            default:
                this.notifications.info(message, title);
                break;
        }
    }

    /**
     * Handler de atualização de estado
     * @param {Object} data - Dados do estado
     */
    handleStateUpdate(data) {
        if (!data || !data.key) return;

        this.state.set(data.key, data.value);
    }

    /**
     * Desconecta do servidor
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }

        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }

        this.isConnected = false;
        this.stopHeartbeat();

        this.state.set('wsConnected', false);
        this.state.set('wsStatus', 'disconnected');
    }

    /**
     * Emite evento para o servidor
     * @param {string} event - Nome do evento
     * @param {any} data - Dados
     * @param {Function} callback - Callback opcional
     */
    emit(event, data, callback) {
        if (!this.isConnected) {
            // Adicionar à queue offline
            this.offlineQueue.push({ event, data, callback, timestamp: Date.now() });
            console.debug('Mensagem adicionada à queue offline:', event);
            return;
        }

        if (this.socket) {
            if (callback) {
                this.socket.emit(event, data, callback);
            } else {
                this.socket.emit(event, data);
            }
        }
    }

    /**
     * Registra listener de evento
     * @param {string} event - Nome do evento
     * @param {Function} callback - Função callback
     * @returns {Function} Função para remover listener
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, new Set());
        }

        this.eventListeners.get(event).add(callback);

        // Registrar também no socket se existir
        if (this.socket && !['connect', 'disconnect', 'error', 'message'].includes(event)) {
            this.socket.on(event, callback);
        }

        // Retornar função para remover listener
        return () => this.off(event, callback);
    }

    /**
     * Remove listener de evento
     * @param {string} event - Nome do evento
     * @param {Function} callback - Função callback
     */
    off(event, callback) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).delete(callback);
        }

        if (this.socket) {
            this.socket.off(event, callback);
        }
    }

    /**
     * Remove todos os listeners de um evento
     * @param {string} event - Nome do evento
     */
    removeAllListeners(event) {
        if (event) {
            this.eventListeners.delete(event);
            if (this.socket) {
                this.socket.removeAllListeners(event);
            }
        } else {
            this.eventListeners.clear();
            if (this.socket) {
                this.socket.removeAllListeners();
            }
        }
    }

    /**
     * Dispara evento para listeners locais
     * @param {string} event - Nome do evento
     * @param {any} data - Dados
     */
    triggerEvent(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Erro no listener de ${event}:`, error);
                }
            });
        }
    }

    /**
     * Subscreve a um room/canal
     * @param {string} room - Nome do room
     * @param {Function} callback - Callback para mensagens
     */
    subscribe(room, callback) {
        this.subscribedRooms.add(room);

        if (callback) {
            this.on(`room:${room}`, callback);
        }

        if (this.isConnected) {
            this.emit('subscribe', { room });
        }
    }

    /**
     * Cancela subscrição de um room
     * @param {string} room - Nome do room
     */
    unsubscribe(room) {
        this.subscribedRooms.delete(room);
        this.removeAllListeners(`room:${room}`);

        if (this.isConnected) {
            this.emit('unsubscribe', { room });
        }
    }

    /**
     * Re-subscreve aos rooms após reconexão
     */
    resubscribeRooms() {
        this.subscribedRooms.forEach(room => {
            this.emit('subscribe', { room });
        });
    }

    /**
     * Processa queue de mensagens offline
     */
    processOfflineQueue() {
        if (this.offlineQueue.length === 0) return;

        console.log(`Processando ${this.offlineQueue.length} mensagens offline`);

        // Filtrar mensagens antigas (mais de 5 minutos)
        const maxAge = 5 * 60 * 1000;
        const now = Date.now();

        const validMessages = this.offlineQueue.filter(msg => {
            return (now - msg.timestamp) < maxAge;
        });

        // Limpar queue
        this.offlineQueue = [];

        // Enviar mensagens válidas
        validMessages.forEach(msg => {
            this.emit(msg.event, msg.data, msg.callback);
        });
    }

    /**
     * Inicia heartbeat
     */
    startHeartbeat() {
        this.stopHeartbeat();

        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.emit('ping', { timestamp: Date.now() });
            }
        }, this.heartbeatTimeout);
    }

    /**
     * Para heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * Obtém status da conexão
     * @returns {Object}
     */
    getStatus() {
        return {
            connected: this.isConnected,
            status: this.state.get('wsStatus') || 'unknown',
            reconnectAttempts: this.reconnectAttempts,
            subscribedRooms: Array.from(this.subscribedRooms),
            offlineQueueSize: this.offlineQueue.length
        };
    }
}

/**
 * Obtém instância singleton do WebSocketService
 * @param {Object} options - Opções
 * @returns {WebSocketService}
 */
export function getWebSocketService(options = {}) {
    if (!instance) {
        instance = new WebSocketService(options);
    }
    return instance;
}

export default WebSocketService;
