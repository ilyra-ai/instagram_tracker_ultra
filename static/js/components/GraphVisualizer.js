/**
 * GraphVisualizer.js - Visualizador de Grafo de Rede Social
 * 
 * Exibe grafo 3D interativo com:
 * - Nós representando usuários
 * - Arestas representando conexões/interações
 * - Cores por tipo de nó (alvo, seguidor, seguindo)
 * - Tamanho por centralidade/importância
 * - Zoom, rotação e pan interativos
 * - Destaque de comunidades
 * 
 * Utiliza ForceGraph3D ou alternativa 2D
 * 
 * @module GraphVisualizer
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class GraphVisualizer {
    /**
     * Cria uma instância do GraphVisualizer
     * @param {HTMLElement} container - Container do grafo
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();

        // Instância do ForceGraph
        this.graph = null;

        // Dados do grafo
        this.graphData = {
            nodes: [],
            links: []
        };

        // Configurações
        this.config = {
            nodeRelSize: 6,
            linkWidth: 1,
            linkOpacity: 0.3,
            particleSpeed: 0.01,
            warmupTicks: 100,
            cooldownTicks: 200,
            d3AlphaDecay: 0.01,
            d3VelocityDecay: 0.1
        };

        // Cores por tipo de nó
        this.nodeColors = {
            'target': '#667eea',      // Roxo - usuário alvo
            'follower': '#28a745',    // Verde - seguidores
            'following': '#ff9800',   // Laranja - seguindo
            'mutual': '#e91e63',      // Rosa - mútuos
            'interaction': '#2196f3', // Azul - interações
            'community_1': '#9c27b0', // Comunidade 1
            'community_2': '#00bcd4', // Comunidade 2
            'community_3': '#8bc34a', // Comunidade 3
            'default': '#999999'
        };

        // Bind methods
        this.render = this.render.bind(this);
        this.loadGraphData = this.loadGraphData.bind(this);
    }

    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças nos dados do grafo
        this.state.subscribe('networkGraph', (data) => {
            if (data) {
                this.graphData = data;
                this.render();
            }
        });

        // Render inicial
        this.render();

        // Configurar resize observer
        this.setupResizeObserver();
    }

    /**
     * Configura observer para resize
     */
    setupResizeObserver() {
        if (!this.container) return;

        const resizeObserver = new ResizeObserver(() => {
            if (this.graph) {
                this.graph.width(this.container.clientWidth);
                this.graph.height(this.container.clientHeight);
            }
        });

        resizeObserver.observe(this.container);
    }

    /**
     * Carrega dados do grafo
     * @param {string} username - Username
     */
    async loadGraphData(username) {
        if (!username) {
            username = this.state.get('currentUser');
        }

        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }

        const loading = this.notifications.loading(`Gerando grafo de rede de @${username}...`);

        try {
            const result = await this.api.getNetworkGraph(username);

            if (result.success && result.graph_data) {
                this.graphData = result.graph_data;
                this.state.set('networkGraph', result.graph_data);
                loading.success('Grafo de rede gerado!');
                this.render();
            } else {
                loading.error(result.error || 'Erro ao gerar grafo');
            }
        } catch (error) {
            loading.error(`Erro: ${error.message}`);
        }
    }

    /**
     * Renderiza o grafo
     */
    render() {
        if (!this.container) return;

        // Se não há dados, mostrar estado vazio
        if (!this.graphData.nodes || this.graphData.nodes.length === 0) {
            this.container.innerHTML = this.renderEmptyState();
            this.attachEventListeners();
            return;
        }

        // Verificar se ForceGraph3D está disponível
        if (typeof ForceGraph3D !== 'undefined') {
            this.render3DGraph();
        } else if (typeof ForceGraph !== 'undefined') {
            this.render2DGraph();
        } else {
            // Fallback para visualização simples
            this.renderFallbackGraph();
        }
    }

    /**
     * Renderiza estado vazio
     * @returns {string} HTML
     */
    renderEmptyState() {
        return `
            <div class="network-empty">
                <div class="network-empty__icon">
                    <i class="fas fa-project-diagram"></i>
                </div>
                <h3>Grafo de Rede Social</h3>
                <p>Visualize as conexões e interações do perfil</p>
                <button class="btn btn-primary" id="btn-generate-graph">
                    <i class="fas fa-magic"></i>
                    Gerar Grafo
                </button>
            </div>
        `;
    }

    /**
     * Renderiza grafo 3D com ForceGraph3D
     */
    render3DGraph() {
        // Limpar container
        this.container.innerHTML = '';

        // Criar instância do grafo
        this.graph = ForceGraph3D()(this.container)
            .graphData(this.graphData)
            .nodeRelSize(this.config.nodeRelSize)
            .nodeColor(node => this.getNodeColor(node))
            .nodeLabel(node => this.getNodeLabel(node))
            .nodeVal(node => this.getNodeSize(node))
            .linkWidth(this.config.linkWidth)
            .linkOpacity(this.config.linkOpacity)
            .linkColor(link => this.getLinkColor(link))
            .linkLabel(link => this.getLinkLabel(link))
            .linkDirectionalParticles(2)
            .linkDirectionalParticleSpeed(this.config.particleSpeed)
            .backgroundColor('#1a1a2e')
            .warmupTicks(this.config.warmupTicks)
            .cooldownTicks(this.config.cooldownTicks)
            .d3AlphaDecay(this.config.d3AlphaDecay)
            .d3VelocityDecay(this.config.d3VelocityDecay)
            .onNodeClick(node => this.handleNodeClick(node))
            .onNodeHover(node => this.handleNodeHover(node))
            .onLinkClick(link => this.handleLinkClick(link));

        // Ajustar tamanho
        this.graph.width(this.container.clientWidth);
        this.graph.height(this.container.clientHeight || 500);

        // Adicionar controles
        this.addGraphControls();
    }

    /**
     * Renderiza grafo 2D com ForceGraph (fallback)
     */
    render2DGraph() {
        this.container.innerHTML = '';

        this.graph = ForceGraph()(this.container)
            .graphData(this.graphData)
            .nodeRelSize(this.config.nodeRelSize)
            .nodeColor(node => this.getNodeColor(node))
            .nodeLabel(node => this.getNodeLabel(node))
            .nodeVal(node => this.getNodeSize(node))
            .linkWidth(this.config.linkWidth)
            .linkColor(link => this.getLinkColor(link))
            .linkDirectionalParticles(2)
            .backgroundColor('#1a1a2e')
            .onNodeClick(node => this.handleNodeClick(node));

        this.graph.width(this.container.clientWidth);
        this.graph.height(this.container.clientHeight || 500);

        this.addGraphControls();
    }

    /**
     * Renderiza grafo fallback (sem biblioteca externa)
     */
    renderFallbackGraph() {
        const nodes = this.graphData.nodes || [];
        const links = this.graphData.links || [];

        // Estatísticas básicas
        const nodeTypes = {};
        nodes.forEach(n => {
            nodeTypes[n.type] = (nodeTypes[n.type] || 0) + 1;
        });

        this.container.innerHTML = `
            <div class="network-fallback">
                <div class="network-stats">
                    <h4>
                        <i class="fas fa-project-diagram"></i>
                        Estatísticas da Rede
                    </h4>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-number">${nodes.length}</span>
                            <span class="stat-label">Nós</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">${links.length}</span>
                            <span class="stat-label">Conexões</span>
                        </div>
                        ${Object.entries(nodeTypes).map(([type, count]) => `
                            <div class="stat-item">
                                <span class="stat-number">${count}</span>
                                <span class="stat-label">${this.getTypeLabel(type)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="network-nodes-list">
                    <h4>Principais Nós</h4>
                    <div class="nodes-list">
                        ${nodes.slice(0, 20).map(node => `
                            <div class="node-item" style="border-left-color: ${this.getNodeColor(node)}">
                                <span class="node-name">@${node.id || node.username}</span>
                                <span class="node-type">${this.getTypeLabel(node.type)}</span>
                                ${node.centrality ? `
                                    <span class="node-centrality">
                                        Centralidade: ${(node.centrality * 100).toFixed(1)}%
                                    </span>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <p class="fallback-note">
                    <i class="fas fa-info-circle"></i>
                    Para visualização 3D interativa, carregue a biblioteca ForceGraph3D
                </p>
            </div>
        `;
    }

    /**
     * Adiciona controles ao grafo
     */
    addGraphControls() {
        const controls = document.createElement('div');
        controls.className = 'graph-controls';
        controls.innerHTML = `
            <button class="graph-control-btn" id="btn-zoom-in" title="Zoom In">
                <i class="fas fa-plus"></i>
            </button>
            <button class="graph-control-btn" id="btn-zoom-out" title="Zoom Out">
                <i class="fas fa-minus"></i>
            </button>
            <button class="graph-control-btn" id="btn-reset-view" title="Resetar Vista">
                <i class="fas fa-compress-arrows-alt"></i>
            </button>
            <button class="graph-control-btn" id="btn-toggle-labels" title="Toggle Labels">
                <i class="fas fa-tags"></i>
            </button>
            <button class="graph-control-btn" id="btn-export-graph" title="Exportar">
                <i class="fas fa-download"></i>
            </button>
        `;

        this.container.appendChild(controls);

        // Event listeners dos controles
        controls.querySelector('#btn-zoom-in').addEventListener('click', () => {
            if (this.graph && this.graph.zoomToFit) {
                const currentZoom = this.graph.cameraPosition().z;
                this.graph.cameraPosition({ z: currentZoom * 0.8 });
            }
        });

        controls.querySelector('#btn-zoom-out').addEventListener('click', () => {
            if (this.graph && this.graph.zoomToFit) {
                const currentZoom = this.graph.cameraPosition().z;
                this.graph.cameraPosition({ z: currentZoom * 1.2 });
            }
        });

        controls.querySelector('#btn-reset-view').addEventListener('click', () => {
            if (this.graph && this.graph.zoomToFit) {
                this.graph.zoomToFit(1000);
            }
        });

        controls.querySelector('#btn-export-graph').addEventListener('click', () => {
            this.exportGraph();
        });
    }

    /**
     * Obtém cor do nó
     * @param {Object} node - Nó
     * @returns {string}
     */
    getNodeColor(node) {
        // Por comunidade
        if (node.community !== undefined) {
            return this.nodeColors[`community_${node.community % 3 + 1}`] || this.nodeColors.default;
        }

        // Por tipo
        return this.nodeColors[node.type] || this.nodeColors.default;
    }

    /**
     * Obtém label do nó
     * @param {Object} node - Nó
     * @returns {string}
     */
    getNodeLabel(node) {
        const username = node.id || node.username || 'Unknown';
        const type = this.getTypeLabel(node.type);
        const centrality = node.centrality ? ` (${(node.centrality * 100).toFixed(1)}%)` : '';

        return `@${username} - ${type}${centrality}`;
    }

    /**
     * Obtém tamanho do nó
     * @param {Object} node - Nó
     * @returns {number}
     */
    getNodeSize(node) {
        // Baseado em centralidade ou followers
        if (node.centrality) {
            return 1 + node.centrality * 10;
        }

        if (node.followers_count) {
            return Math.max(1, Math.log10(node.followers_count + 1) * 2);
        }

        // Nó alvo é maior
        if (node.type === 'target') {
            return 5;
        }

        return 1;
    }

    /**
     * Obtém cor do link
     * @param {Object} link - Link
     * @returns {string}
     */
    getLinkColor(link) {
        const typeColors = {
            'follows': 'rgba(102, 126, 234, 0.5)',
            'followed_by': 'rgba(40, 167, 69, 0.5)',
            'mutual': 'rgba(233, 30, 99, 0.5)',
            'interaction': 'rgba(33, 150, 243, 0.5)'
        };

        return typeColors[link.type] || 'rgba(153, 153, 153, 0.3)';
    }

    /**
     * Obtém label do link
     * @param {Object} link - Link
     * @returns {string}
     */
    getLinkLabel(link) {
        if (link.weight) {
            return `${link.type || 'conexão'} (peso: ${link.weight})`;
        }
        return link.type || 'conexão';
    }

    /**
     * Obtém label do tipo
     * @param {string} type - Tipo
     * @returns {string}
     */
    getTypeLabel(type) {
        const labels = {
            'target': 'Alvo',
            'follower': 'Seguidor',
            'following': 'Seguindo',
            'mutual': 'Mútuo',
            'interaction': 'Interação'
        };

        return labels[type] || type || 'Desconhecido';
    }

    /**
     * Handler de clique no nó
     * @param {Object} node - Nó clicado
     */
    handleNodeClick(node) {
        if (!node) return;

        const username = node.id || node.username;

        this.notifications.info(`Selecionado: @${username}`);

        // Destacar nó e conexões
        if (this.graph && this.graphData.nodes && this.graphData.links) {
            // Identificar nós conectados ao nó clicado
            const connectedNodes = new Set([node.id]);
            this.graphData.links.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                
                if (sourceId === node.id) connectedNodes.add(targetId);
                if (targetId === node.id) connectedNodes.add(sourceId);
            });

            // Atualizar opacidade de todos os nós baseado na conexão
            if (typeof this.graph.nodeOpacity === 'function') {
                this.graph.nodeOpacity(n => connectedNodes.has(n.id) ? 1 : 0.2);
            }
            
            // Atualizar opacidade dos links
            if (typeof this.graph.linkOpacity === 'function') {
                this.graph.linkOpacity(link => {
                    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                    const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                    return (sourceId === node.id || targetId === node.id) ? 0.8 : 0.05;
                });
            }

            // Centralizar câmera no nó clicado (3D)
            if (typeof this.graph.centerAt === 'function' && node.x !== undefined) {
                this.graph.centerAt(node.x, node.y, 1000);
            } else if (typeof this.graph.cameraPosition === 'function' && node.x !== undefined) {
                this.graph.cameraPosition(
                    { x: node.x, y: node.y, z: 300 },
                    node,
                    1000
                );
            }
        }

        // Emitir evento customizado
        document.dispatchEvent(new CustomEvent('graph:nodeClick', {
            detail: { node }
        }));
    }

    /**
     * Handler de hover no nó
     * @param {Object} node - Nó
     */
    handleNodeHover(node) {
        this.container.style.cursor = node ? 'pointer' : 'grab';
    }

    /**
     * Handler de clique no link
     * @param {Object} link - Link clicado
     */
    handleLinkClick(link) {
        if (!link) return;

        this.notifications.info(`Conexão: ${link.source?.id || link.source} ↔ ${link.target?.id || link.target}`);
    }

    /**
     * Exporta grafo
     */
    exportGraph() {
        const data = {
            exportedAt: new Date().toISOString(),
            nodes: this.graphData.nodes,
            links: this.graphData.links,
            stats: {
                totalNodes: this.graphData.nodes?.length || 0,
                totalLinks: this.graphData.links?.length || 0
            }
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `network-graph-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.notifications.success('Grafo exportado!');
    }

    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        const btnGenerate = this.container.querySelector('#btn-generate-graph');
        if (btnGenerate) {
            btnGenerate.addEventListener('click', () => this.loadGraphData());
        }
    }

    /**
     * Destrói o grafo (cleanup)
     */
    destroy() {
        if (this.graph) {
            this.graph._destructor && this.graph._destructor();
            this.graph = null;
        }
    }
}

// Factory function
export function createGraphVisualizer(container) {
    const visualizer = new GraphVisualizer(container);
    visualizer.init();
    return visualizer;
}

export default GraphVisualizer;
