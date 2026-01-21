/**
 * ExportService.js - Serviço de Exportação de Dados
 * 
 * Exporta dados em múltiplos formatos:
 * - JSON
 * - CSV
 * - PDF (relatório)
 * - PNG (gráficos)
 * 
 * @module ExportService
 * @version 1.0.0
 */

import { getStateManager } from '../core/StateManager.js';
import { getNotificationService } from '../core/NotificationService.js';

// Singleton instance
let instance = null;

export class ExportService {
    /**
     * Cria uma instância do ExportService
     */
    constructor() {
        if (instance) {
            return instance;
        }

        this.state = getStateManager();
        this.notifications = getNotificationService();

        instance = this;
    }

    // ==========================================================================
    // EXPORTAÇÃO JSON
    // ==========================================================================

    /**
     * Exporta dados como JSON
     * @param {Object} data - Dados para exportar
     * @param {string} filename - Nome do arquivo
     * @param {Object} options - Opções
     */
    exportJSON(data, filename = 'export', options = {}) {
        try {
            const prettify = options.prettify !== false;
            const jsonString = prettify
                ? JSON.stringify(data, null, 2)
                : JSON.stringify(data);

            const blob = new Blob([jsonString], { type: 'application/json' });
            this.downloadBlob(blob, `${filename}.json`);

            this.notifications.success('Arquivo JSON exportado com sucesso');
            return true;
        } catch (error) {
            console.error('Erro ao exportar JSON:', error);
            this.notifications.error('Erro ao exportar JSON');
            return false;
        }
    }

    /**
     * Exporta perfil completo como JSON
     * @param {string} username - Username
     */
    async exportProfileJSON(username) {
        const loading = this.notifications.loading('Preparando exportação...');

        try {
            // Coletar dados do state
            const profile = this.state.get('profile') || {};
            const activities = this.state.get('activities') || [];
            const sentiment = this.state.get('sentiment') || {};
            const predictions = this.state.get('predictions') || {};
            const network = this.state.get('networkGraph') || {};
            const locations = this.state.get('locations') || [];
            const osint = this.state.get('osintResults') || {};

            const exportData = {
                export_info: {
                    username: username,
                    exported_at: new Date().toISOString(),
                    version: '1.0.0'
                },
                profile,
                activities,
                sentiment,
                predictions,
                network,
                locations,
                osint
            };

            const filename = `instagram_${username}_${this.getDateString()}`;
            this.exportJSON(exportData, filename);

            loading.success('Perfil exportado com sucesso!');
        } catch (error) {
            loading.error('Erro ao exportar perfil');
        }
    }

    // ==========================================================================
    // EXPORTAÇÃO CSV
    // ==========================================================================

    /**
     * Exporta dados como CSV
     * @param {Array} data - Array de objetos
     * @param {string} filename - Nome do arquivo
     * @param {Object} options - Opções
     */
    exportCSV(data, filename = 'export', options = {}) {
        try {
            if (!Array.isArray(data) || data.length === 0) {
                this.notifications.warning('Nenhum dado para exportar');
                return false;
            }

            const delimiter = options.delimiter || ',';
            const includeHeaders = options.includeHeaders !== false;

            // Obter headers
            const headers = this.getCSVHeaders(data);

            // Construir CSV
            let csv = '';

            if (includeHeaders) {
                csv += headers.map(h => this.escapeCSV(h)).join(delimiter) + '\n';
            }

            // Linhas de dados
            data.forEach(row => {
                const values = headers.map(header => {
                    const value = this.getNestedValue(row, header);
                    return this.escapeCSV(this.formatCSVValue(value));
                });
                csv += values.join(delimiter) + '\n';
            });

            // Adicionar BOM para UTF-8
            const bom = '\ufeff';
            const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8' });
            this.downloadBlob(blob, `${filename}.csv`);

            this.notifications.success('Arquivo CSV exportado com sucesso');
            return true;
        } catch (error) {
            console.error('Erro ao exportar CSV:', error);
            this.notifications.error('Erro ao exportar CSV');
            return false;
        }
    }

    /**
     * Exporta atividades como CSV
     */
    exportActivitiesCSV() {
        const activities = this.state.get('activities') || [];

        if (activities.length === 0) {
            this.notifications.warning('Nenhuma atividade para exportar');
            return;
        }

        const data = activities.map(a => ({
            tipo: this.translateActivityType(a.type),
            usuario_alvo: a.target_username || '',
            conteudo: a.content || '',
            data: a.timestamp ? new Date(a.timestamp).toLocaleString('pt-BR') : '',
            url: a.url || ''
        }));

        const username = this.state.get('currentUser') || 'usuario';
        this.exportCSV(data, `atividades_${username}_${this.getDateString()}`);
    }

    /**
     * Exporta localizações como CSV
     */
    exportLocationsCSV() {
        const locations = this.state.get('locations') || [];

        if (locations.length === 0) {
            this.notifications.warning('Nenhuma localização para exportar');
            return;
        }

        const data = locations.map(l => ({
            nome: l.name || '',
            endereco: l.address || '',
            cidade: l.city || '',
            pais: l.country || '',
            latitude: l.lat || '',
            longitude: l.lng || '',
            frequencia: l.frequency || 1,
            ultima_visita: l.last_visit ? new Date(l.last_visit).toLocaleString('pt-BR') : ''
        }));

        const username = this.state.get('currentUser') || 'usuario';
        this.exportCSV(data, `localizacoes_${username}_${this.getDateString()}`);
    }

    /**
     * Obtém headers do CSV
     * @param {Array} data - Dados
     * @returns {Array}
     */
    getCSVHeaders(data) {
        const headers = new Set();

        data.forEach(row => {
            if (typeof row === 'object' && row !== null) {
                Object.keys(row).forEach(key => headers.add(key));
            }
        });

        return Array.from(headers);
    }

    /**
     * Escapa valor para CSV
     * @param {string} value - Valor
     * @returns {string}
     */
    escapeCSV(value) {
        if (value === null || value === undefined) return '';

        let str = String(value);

        // Se contém vírgula, aspas ou quebra de linha, envolver em aspas
        if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
            str = '"' + str.replace(/"/g, '""') + '"';
        }

        return str;
    }

    /**
     * Formata valor para CSV
     * @param {any} value - Valor
     * @returns {string}
     */
    formatCSVValue(value) {
        if (value === null || value === undefined) return '';
        if (typeof value === 'object') return JSON.stringify(value);
        return String(value);
    }

    /**
     * Obtém valor aninhado
     * @param {Object} obj - Objeto
     * @param {string} path - Caminho
     * @returns {any}
     */
    getNestedValue(obj, path) {
        const keys = path.split('.');
        let value = obj;

        for (const key of keys) {
            if (value === null || value === undefined) return '';
            value = value[key];
        }

        return value;
    }

    // ==========================================================================
    // EXPORTAÇÃO PDF
    // ==========================================================================

    /**
     * Exporta relatório como PDF
     * @param {Object} options - Opções
     */
    async exportPDF(options = {}) {
        const loading = this.notifications.loading('Gerando relatório PDF...');

        try {
            // Verificar se jsPDF está disponível
            if (typeof jspdf === 'undefined' && typeof window.jspdf === 'undefined') {
                // Carregar jsPDF dinamicamente
                await this.loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js');
            }

            const { jsPDF } = window.jspdf || jspdf;
            const doc = new jsPDF();

            // Configurações
            const marginLeft = 15;
            const marginTop = 20;
            let yPosition = marginTop;

            // Título
            doc.setFontSize(20);
            doc.setTextColor(59, 130, 246); // Azul
            doc.text('Relatório de Análise de Perfil', marginLeft, yPosition);
            yPosition += 15;

            // Data
            doc.setFontSize(10);
            doc.setTextColor(100, 100, 100);
            doc.text(`Gerado em: ${new Date().toLocaleString('pt-BR')}`, marginLeft, yPosition);
            yPosition += 15;

            // Perfil
            const profile = this.state.get('profile') || {};
            if (profile.username) {
                doc.setFontSize(14);
                doc.setTextColor(0, 0, 0);
                doc.text(`Perfil: @${profile.username}`, marginLeft, yPosition);
                yPosition += 8;

                doc.setFontSize(10);
                if (profile.full_name) {
                    doc.text(`Nome: ${profile.full_name}`, marginLeft, yPosition);
                    yPosition += 6;
                }
                if (profile.followers_count !== undefined) {
                    doc.text(`Seguidores: ${this.formatNumber(profile.followers_count)}`, marginLeft, yPosition);
                    yPosition += 6;
                }
                if (profile.following_count !== undefined) {
                    doc.text(`Seguindo: ${this.formatNumber(profile.following_count)}`, marginLeft, yPosition);
                    yPosition += 6;
                }
                if (profile.posts_count !== undefined) {
                    doc.text(`Posts: ${this.formatNumber(profile.posts_count)}`, marginLeft, yPosition);
                    yPosition += 6;
                }
                yPosition += 10;
            }

            // Sentimento
            const sentiment = this.state.get('sentiment') || {};
            if (sentiment.score !== undefined) {
                doc.setFontSize(14);
                doc.text('Análise de Sentimento', marginLeft, yPosition);
                yPosition += 8;

                doc.setFontSize(10);
                doc.text(`Score: ${sentiment.score}`, marginLeft, yPosition);
                yPosition += 6;
                doc.text(`Classificação: ${sentiment.classification || 'N/A'}`, marginLeft, yPosition);
                yPosition += 15;
            }

            // Previsões
            const predictions = this.state.get('predictions') || {};
            if (predictions.predictability_score !== undefined) {
                doc.setFontSize(14);
                doc.text('Previsibilidade', marginLeft, yPosition);
                yPosition += 8;

                doc.setFontSize(10);
                doc.text(`Score de Previsibilidade: ${predictions.predictability_score}%`, marginLeft, yPosition);
                yPosition += 6;
                if (predictions.next_post_prediction) {
                    doc.text(`Próximo Post: ${predictions.next_post_prediction}`, marginLeft, yPosition);
                    yPosition += 6;
                }
                yPosition += 15;
            }

            // Atividades resumidas
            const activities = this.state.get('activities') || [];
            if (activities.length > 0) {
                doc.setFontSize(14);
                doc.text('Resumo de Atividades', marginLeft, yPosition);
                yPosition += 8;

                doc.setFontSize(10);
                doc.text(`Total de atividades rastreadas: ${activities.length}`, marginLeft, yPosition);
                yPosition += 6;

                // Contar por tipo
                const typeCounts = {};
                activities.forEach(a => {
                    typeCounts[a.type] = (typeCounts[a.type] || 0) + 1;
                });

                Object.entries(typeCounts).forEach(([type, count]) => {
                    doc.text(`- ${this.translateActivityType(type)}: ${count}`, marginLeft + 5, yPosition);
                    yPosition += 5;
                });
                yPosition += 10;
            }

            // Localizações
            const locations = this.state.get('locations') || [];
            if (locations.length > 0) {
                doc.setFontSize(14);
                doc.text('Localizações', marginLeft, yPosition);
                yPosition += 8;

                doc.setFontSize(10);
                doc.text(`Total de locais detectados: ${locations.length}`, marginLeft, yPosition);
                yPosition += 6;

                // Top 5 locais
                const topLocations = locations
                    .sort((a, b) => (b.frequency || 0) - (a.frequency || 0))
                    .slice(0, 5);

                topLocations.forEach(loc => {
                    const text = `${loc.name || loc.city || 'Desconhecido'} (${loc.frequency || 1}x)`;
                    doc.text(`- ${text}`, marginLeft + 5, yPosition);
                    yPosition += 5;
                });
            }

            // Disclaimer
            if (yPosition < 280) {
                yPosition = 280;
            }
            doc.setFontSize(8);
            doc.setTextColor(150, 150, 150);
            doc.text('Este relatório foi gerado automaticamente pelo Instagram Tracker.', marginLeft, yPosition);

            // Salvar
            const username = this.state.get('currentUser') || 'usuario';
            doc.save(`relatorio_${username}_${this.getDateString()}.pdf`);

            loading.success('Relatório PDF gerado com sucesso!');
            return true;
        } catch (error) {
            console.error('Erro ao gerar PDF:', error);
            loading.error('Erro ao gerar PDF. Verifique se a biblioteca jsPDF está disponível.');
            return false;
        }
    }

    // ==========================================================================
    // EXPORTAÇÃO PNG (GRÁFICOS)
    // ==========================================================================

    /**
     * Exporta elemento como PNG
     * @param {HTMLElement|string} element - Elemento ou seletor
     * @param {string} filename - Nome do arquivo
     * @param {Object} options - Opções
     */
    async exportPNG(element, filename = 'chart', options = {}) {
        const loading = this.notifications.loading('Capturando imagem...');

        try {
            // Obter elemento
            const el = typeof element === 'string'
                ? document.querySelector(element)
                : element;

            if (!el) {
                loading.error('Elemento não encontrado');
                return false;
            }

            // Verificar se html2canvas está disponível
            if (typeof html2canvas === 'undefined') {
                await this.loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js');
            }

            // Capturar
            const canvas = await html2canvas(el, {
                backgroundColor: options.backgroundColor || '#ffffff',
                scale: options.scale || 2,
                logging: false,
                useCORS: true
            });

            // Converter para blob
            canvas.toBlob(blob => {
                this.downloadBlob(blob, `${filename}.png`);
                loading.success('Imagem exportada com sucesso!');
            }, 'image/png');

            return true;
        } catch (error) {
            console.error('Erro ao exportar PNG:', error);
            loading.error('Erro ao exportar imagem');
            return false;
        }
    }

    /**
     * Exporta canvas como PNG
     * @param {HTMLCanvasElement} canvas - Elemento canvas
     * @param {string} filename - Nome do arquivo
     */
    exportCanvasPNG(canvas, filename = 'chart') {
        try {
            const dataUrl = canvas.toDataURL('image/png');
            const link = document.createElement('a');
            link.download = `${filename}.png`;
            link.href = dataUrl;
            link.click();

            this.notifications.success('Gráfico exportado com sucesso!');
            return true;
        } catch (error) {
            console.error('Erro ao exportar canvas:', error);
            this.notifications.error('Erro ao exportar gráfico');
            return false;
        }
    }

    /**
     * Exporta gráfico Chart.js
     * @param {Object} chart - Instância do Chart.js
     * @param {string} filename - Nome do arquivo
     */
    exportChartJS(chart, filename = 'chart') {
        if (!chart || !chart.canvas) {
            this.notifications.error('Gráfico inválido');
            return false;
        }

        return this.exportCanvasPNG(chart.canvas, filename);
    }

    // ==========================================================================
    // UTILITÁRIOS
    // ==========================================================================

    /**
     * Faz download de blob
     * @param {Blob} blob - Blob
     * @param {string} filename - Nome do arquivo
     */
    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    /**
     * Carrega script dinamicamente
     * @param {string} src - URL do script
     * @returns {Promise}
     */
    loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    /**
     * Obtém string de data formatada
     * @returns {string}
     */
    getDateString() {
        const now = new Date();
        return now.toISOString().split('T')[0].replace(/-/g, '');
    }

    /**
     * Formata número
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
     * Traduz tipo de atividade
     * @param {string} type - Tipo
     * @returns {string}
     */
    translateActivityType(type) {
        const translations = {
            'like': 'Curtida',
            'comment': 'Comentário',
            'follow': 'Seguiu',
            'unfollow': 'Deixou de seguir',
            'mention': 'Menção',
            'story_view': 'Visualização de Story',
            'post': 'Publicação'
        };
        return translations[type] || type;
    }
}

/**
 * Obtém instância singleton do ExportService
 * @returns {ExportService}
 */
export function getExportService() {
    if (!instance) {
        instance = new ExportService();
    }
    return instance;
}

export default ExportService;
