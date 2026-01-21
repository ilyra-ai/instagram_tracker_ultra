/**
 * GeoHeatmap.js - Mapa de Localizações com Leaflet
 * 
 * Exibe mapa interativo com:
 * - Markers de localizações encontradas em posts
 * - Heatmap de concentração de atividade
 * - Clusters de markers próximos
 * - Popup com detalhes de cada localização
 * - Timeline de viagens/deslocamentos
 * 
 * @module GeoHeatmap
 * @version 1.0.0
 */

import { getAPIService } from '../core/APIService.js';
import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

export class GeoHeatmap {
    /**
     * Cria uma instância do GeoHeatmap
     * @param {HTMLElement} container - Container do mapa
     */
    constructor(container) {
        this.container = container;
        this.api = getAPIService();
        this.state = getStateManager();
        this.notifications = getNotificationService();
        
        // Instância do mapa Leaflet
        this.map = null;
        
        // Layers
        this.markersLayer = null;
        this.heatmapLayer = null;
        
        // Dados
        this.locations = [];
        
        // Configurações
        this.config = {
            defaultCenter: [-23.5505, -46.6333], // São Paulo
            defaultZoom: 4,
            maxZoom: 18,
            minZoom: 2,
            tileLayer: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            attribution: '© OpenStreetMap contributors'
        };
        
        // Cores por tipo de localização
        this.markerColors = {
            'post': '#667eea',
            'story': '#e91e63',
            'reel': '#ff9800',
            'home': '#28a745',
            'work': '#2196f3',
            'frequent': '#9c27b0',
            'default': '#999999'
        };
        
        // Bind methods
        this.render = this.render.bind(this);
        this.loadLocations = this.loadLocations.bind(this);
    }
    
    /**
     * Inicializa o componente
     */
    init() {
        // Subscribe para mudanças nas localizações
        this.state.subscribe('locations', (locations) => {
            this.locations = locations || [];
            this.updateMarkers();
        });
        
        // Render inicial
        this.render();
    }
    
    /**
     * Carrega localizações do usuário
     * @param {string} username - Username
     */
    async loadLocations(username) {
        if (!username) {
            username = this.state.get('currentUser');
        }
        
        if (!username) {
            this.notifications.warning('Selecione um usuário primeiro');
            return;
        }
        
        const loading = this.notifications.loading(`Carregando localizações de @${username}...`);
        
        try {
            const result = await this.api.getLocations(username);
            
            if (result.success && result.locations) {
                this.locations = result.locations;
                this.state.set('locations', result.locations);
                loading.success(`${result.locations.length} localizações encontradas!`);
                this.updateMarkers();
            } else {
                loading.error(result.error || 'Nenhuma localização encontrada');
            }
        } catch (error) {
            loading.error(`Erro: ${error.message}`);
        }
    }
    
    /**
     * Renderiza o mapa
     */
    render() {
        if (!this.container) return;
        
        // Verificar se Leaflet está disponível
        if (typeof L === 'undefined') {
            this.renderFallback();
            return;
        }
        
        // Criar estrutura HTML
        this.container.innerHTML = `
            <div class="map-wrapper">
                <div id="leaflet-map" class="leaflet-container"></div>
                <div class="map-controls">
                    <button class="map-control-btn" id="btn-load-locations" title="Carregar Localizações">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                    <button class="map-control-btn" id="btn-toggle-heatmap" title="Toggle Heatmap">
                        <i class="fas fa-fire"></i>
                    </button>
                    <button class="map-control-btn" id="btn-fit-bounds" title="Ajustar Zoom">
                        <i class="fas fa-compress-arrows-alt"></i>
                    </button>
                    <button class="map-control-btn" id="btn-export-locations" title="Exportar">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
                <div class="map-legend" id="map-legend">
                    <h4>Legenda</h4>
                    <div class="legend-items">
                        <div class="legend-item">
                            <span class="legend-color" style="background: ${this.markerColors.post}"></span>
                            <span>Posts</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background: ${this.markerColors.story}"></span>
                            <span>Stories</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background: ${this.markerColors.reel}"></span>
                            <span>Reels</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background: ${this.markerColors.frequent}"></span>
                            <span>Frequente</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="locations-sidebar" id="locations-sidebar">
                <h4>
                    <i class="fas fa-map-marker-alt"></i>
                    Localizações (<span id="locations-count">0</span>)
                </h4>
                <div class="locations-list" id="locations-list">
                    <p class="empty-message">Clique para carregar localizações</p>
                </div>
            </div>
        `;
        
        // Inicializar mapa Leaflet
        this.initializeMap();
        
        // Anexar event listeners
        this.attachEventListeners();
    }
    
    /**
     * Renderiza fallback sem Leaflet
     */
    renderFallback() {
        this.container.innerHTML = `
            <div class="map-fallback">
                <div class="fallback-icon">
                    <i class="fas fa-map-marked-alt"></i>
                </div>
                <h3>Mapa de Localizações</h3>
                <p>Para visualização interativa, carregue a biblioteca Leaflet.js</p>
                
                <div class="locations-stats" id="locations-stats">
                    <p>Carregando...</p>
                </div>
                
                <button class="btn btn-primary" id="btn-load-locations-fallback">
                    <i class="fas fa-sync-alt"></i>
                    Carregar Localizações
                </button>
            </div>
        `;
        
        const btn = this.container.querySelector('#btn-load-locations-fallback');
        if (btn) {
            btn.addEventListener('click', () => this.loadLocations());
        }
    }
    
    /**
     * Inicializa mapa Leaflet
     */
    initializeMap() {
        const mapContainer = this.container.querySelector('#leaflet-map');
        if (!mapContainer || typeof L === 'undefined') return;
        
        // Criar mapa
        this.map = L.map(mapContainer, {
            center: this.config.defaultCenter,
            zoom: this.config.defaultZoom,
            maxZoom: this.config.maxZoom,
            minZoom: this.config.minZoom,
            zoomControl: true,
            scrollWheelZoom: true
        });
        
        // Adicionar tile layer
        L.tileLayer(this.config.tileLayer, {
            attribution: this.config.attribution,
            maxZoom: this.config.maxZoom
        }).addTo(this.map);
        
        // Criar layer group para markers
        this.markersLayer = L.layerGroup().addTo(this.map);
        
        // Atualizar markers se já houver dados
        if (this.locations.length > 0) {
            this.updateMarkers();
        }
    }
    
    /**
     * Atualiza markers no mapa
     */
    updateMarkers() {
        if (!this.map || !this.markersLayer) return;
        
        // Limpar markers existentes
        this.markersLayer.clearLayers();
        
        // Adicionar novos markers
        const bounds = [];
        
        this.locations.forEach((location, index) => {
            if (!location.lat || !location.lng) return;
            
            const lat = parseFloat(location.lat);
            const lng = parseFloat(location.lng);
            
            if (isNaN(lat) || isNaN(lng)) return;
            
            bounds.push([lat, lng]);
            
            // Criar custom icon
            const icon = this.createMarkerIcon(location);
            
            // Criar marker
            const marker = L.marker([lat, lng], { icon })
                .bindPopup(this.createPopupContent(location))
                .on('click', () => this.handleMarkerClick(location, index));
            
            this.markersLayer.addLayer(marker);
        });
        
        // Atualizar contador
        const countEl = this.container.querySelector('#locations-count');
        if (countEl) {
            countEl.textContent = this.locations.length;
        }
        
        // Atualizar lista de localizações
        this.updateLocationsList();
        
        // Ajustar bounds se houver markers
        if (bounds.length > 0) {
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
    }
    
    /**
     * Cria ícone customizado para marker
     * @param {Object} location - Dados da localização
     * @returns {L.DivIcon}
     */
    createMarkerIcon(location) {
        const color = this.markerColors[location.type] || this.markerColors.default;
        const frequency = location.frequency || 1;
        const size = Math.min(40, 20 + frequency * 5);
        
        return L.divIcon({
            className: 'custom-marker',
            html: `
                <div class="marker-pin" style="background-color: ${color}; width: ${size}px; height: ${size}px;">
                    <i class="fas fa-map-marker-alt"></i>
                    ${frequency > 1 ? `<span class="marker-count">${frequency}</span>` : ''}
                </div>
            `,
            iconSize: [size, size],
            iconAnchor: [size / 2, size]
        });
    }
    
    /**
     * Cria conteúdo do popup
     * @param {Object} location - Dados da localização
     * @returns {string}
     */
    createPopupContent(location) {
        return `
            <div class="location-popup">
                <h4>${this.escapeHtml(location.name || 'Local desconhecido')}</h4>
                ${location.address ? `<p class="popup-address"><i class="fas fa-map-pin"></i> ${this.escapeHtml(location.address)}</p>` : ''}
                ${location.city ? `<p class="popup-city"><i class="fas fa-city"></i> ${this.escapeHtml(location.city)}</p>` : ''}
                ${location.country ? `<p class="popup-country"><i class="fas fa-globe"></i> ${this.escapeHtml(location.country)}</p>` : ''}
                ${location.frequency ? `<p class="popup-frequency"><i class="fas fa-chart-bar"></i> ${location.frequency} visita(s)</p>` : ''}
                ${location.last_seen ? `<p class="popup-date"><i class="far fa-clock"></i> Última vez: ${this.formatDate(location.last_seen)}</p>` : ''}
                ${location.post_url ? `<a href="${location.post_url}" target="_blank" class="popup-link"><i class="fas fa-external-link-alt"></i> Ver post</a>` : ''}
            </div>
        `;
    }
    
    /**
     * Atualiza lista de localizações na sidebar
     */
    updateLocationsList() {
        const listEl = this.container.querySelector('#locations-list');
        if (!listEl) return;
        
        if (this.locations.length === 0) {
            listEl.innerHTML = '<p class="empty-message">Nenhuma localização encontrada</p>';
            return;
        }
        
        // Ordenar por frequência
        const sorted = [...this.locations].sort((a, b) => (b.frequency || 1) - (a.frequency || 1));
        
        listEl.innerHTML = sorted.map((loc, index) => `
            <div class="location-item" data-index="${index}" data-lat="${loc.lat}" data-lng="${loc.lng}">
                <div class="location-item__color" style="background: ${this.markerColors[loc.type] || this.markerColors.default}"></div>
                <div class="location-item__info">
                    <span class="location-name">${this.escapeHtml(loc.name || 'Local desconhecido')}</span>
                    <span class="location-meta">
                        ${loc.city ? loc.city : ''}
                        ${loc.frequency ? ` • ${loc.frequency}x` : ''}
                    </span>
                </div>
                <button class="location-item__action" title="Ir para localização">
                    <i class="fas fa-crosshairs"></i>
                </button>
            </div>
        `).join('');
        
        // Adicionar event listeners
        listEl.querySelectorAll('.location-item').forEach(item => {
            item.addEventListener('click', () => {
                const lat = parseFloat(item.dataset.lat);
                const lng = parseFloat(item.dataset.lng);
                if (!isNaN(lat) && !isNaN(lng)) {
                    this.flyToLocation(lat, lng);
                }
            });
        });
    }
    
    /**
     * Anima o mapa para uma localização
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @param {number} zoom - Nível de zoom
     */
    flyToLocation(lat, lng, zoom = 15) {
        if (!this.map) return;
        this.map.flyTo([lat, lng], zoom, {
            duration: 1.5,
            easeLinearity: 0.25
        });
    }
    
    /**
     * Handler de clique no marker
     * @param {Object} location - Localização
     * @param {number} index - Índice
     */
    handleMarkerClick(location, index) {
        // Destacar item na lista
        const listItems = this.container.querySelectorAll('.location-item');
        listItems.forEach((item, i) => {
            item.classList.toggle('active', i === index);
        });
        
        // Emitir evento
        document.dispatchEvent(new CustomEvent('map:markerClick', {
            detail: { location, index }
        }));
    }
    
    /**
     * Toggle heatmap layer
     */
    toggleHeatmap() {
        if (!this.map || typeof L.heatLayer === 'undefined') {
            this.notifications.warning('Plugin de heatmap não disponível');
            return;
        }
        
        if (this.heatmapLayer) {
            this.map.removeLayer(this.heatmapLayer);
            this.heatmapLayer = null;
            return;
        }
        
        // Criar dados do heatmap
        const heatData = this.locations
            .filter(loc => loc.lat && loc.lng)
            .map(loc => [
                parseFloat(loc.lat),
                parseFloat(loc.lng),
                (loc.frequency || 1) * 0.5
            ]);
        
        if (heatData.length === 0) {
            this.notifications.warning('Sem dados para gerar heatmap');
            return;
        }
        
        this.heatmapLayer = L.heatLayer(heatData, {
            radius: 25,
            blur: 15,
            maxZoom: 17,
            gradient: {
                0.0: 'blue',
                0.5: 'lime',
                0.7: 'yellow',
                1.0: 'red'
            }
        }).addTo(this.map);
    }
    
    /**
     * Ajusta bounds para mostrar todos os markers
     */
    fitBounds() {
        if (!this.map) return;
        
        const bounds = this.locations
            .filter(loc => loc.lat && loc.lng)
            .map(loc => [parseFloat(loc.lat), parseFloat(loc.lng)]);
        
        if (bounds.length > 0) {
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
    }
    
    /**
     * Exporta localizações
     */
    exportLocations() {
        const data = {
            exportedAt: new Date().toISOString(),
            totalLocations: this.locations.length,
            locations: this.locations
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `locations-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.notifications.success('Localizações exportadas!');
    }
    
    /**
     * Anexa event listeners
     */
    attachEventListeners() {
        const btnLoad = this.container.querySelector('#btn-load-locations');
        if (btnLoad) {
            btnLoad.addEventListener('click', () => this.loadLocations());
        }
        
        const btnHeatmap = this.container.querySelector('#btn-toggle-heatmap');
        if (btnHeatmap) {
            btnHeatmap.addEventListener('click', () => this.toggleHeatmap());
        }
        
        const btnFit = this.container.querySelector('#btn-fit-bounds');
        if (btnFit) {
            btnFit.addEventListener('click', () => this.fitBounds());
        }
        
        const btnExport = this.container.querySelector('#btn-export-locations');
        if (btnExport) {
            btnExport.addEventListener('click', () => this.exportLocations());
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
            year: 'numeric'
        });
    }
    
    /**
     * Destrói o mapa (cleanup)
     */
    destroy() {
        if (this.map) {
            this.map.remove();
            this.map = null;
        }
    }
}

// Factory function
export function createGeoHeatmap(container) {
    const heatmap = new GeoHeatmap(container);
    heatmap.init();
    return heatmap;
}

export default GeoHeatmap;
