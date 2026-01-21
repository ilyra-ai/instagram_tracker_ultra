/**
 * CacheService.js - Serviço de Cache Local
 * 
 * Gerencia cache de dados no cliente:
 * - Cache em memória (L1)
 * - Cache em localStorage (L2)
 * - Cache em IndexedDB (L3)
 * - TTL (Time To Live) configurável
 * - Invalidação seletiva
 * - Compressão de dados grandes
 * 
 * @module CacheService
 * @version 1.0.0
 */

// Singleton instance
let instance = null;

export class CacheService {
    /**
     * Cria uma instância do CacheService
     * @param {Object} options - Opções de configuração
     */
    constructor(options = {}) {
        if (instance) {
            return instance;
        }

        // Configurações
        this.config = {
            prefix: options.prefix || 'ig_tracker_',
            defaultTTL: options.defaultTTL || 60 * 60 * 1000, // 1 hora
            maxMemoryItems: options.maxMemoryItems || 100,
            maxLocalStorageSize: options.maxLocalStorageSize || 5 * 1024 * 1024, // 5MB
            enableIndexedDB: options.enableIndexedDB !== false,
            dbName: options.dbName || 'IGTrackerCache',
            dbVersion: options.dbVersion || 1,
            storeName: options.storeName || 'cache'
        };

        // Cache L1 - Memória
        this.memoryCache = new Map();

        // Cache L2 - localStorage disponível
        this.localStorageAvailable = this.checkLocalStorage();

        // Cache L3 - IndexedDB
        this.db = null;
        this.indexedDBAvailable = false;

        // Estatísticas
        this.stats = {
            hits: 0,
            misses: 0,
            sets: 0,
            deletes: 0
        };

        // Bind methods
        this.get = this.get.bind(this);
        this.set = this.set.bind(this);
        this.delete = this.delete.bind(this);

        instance = this;

        // Inicializar IndexedDB
        if (this.config.enableIndexedDB) {
            this.initIndexedDB();
        }

        // Limpar cache expirado periodicamente
        this.startCleanupInterval();
    }

    /**
     * Verifica se localStorage está disponível
     * @returns {boolean}
     */
    checkLocalStorage() {
        try {
            const test = '__storage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * Inicializa IndexedDB
     * @returns {Promise<boolean>}
     */
    async initIndexedDB() {
        return new Promise((resolve) => {
            if (!window.indexedDB) {
                console.warn('IndexedDB não disponível');
                resolve(false);
                return;
            }

            try {
                const request = indexedDB.open(this.config.dbName, this.config.dbVersion);

                request.onerror = () => {
                    console.warn('Erro ao abrir IndexedDB');
                    resolve(false);
                };

                request.onsuccess = (event) => {
                    this.db = event.target.result;
                    this.indexedDBAvailable = true;
                    console.log('IndexedDB inicializado');
                    resolve(true);
                };

                request.onupgradeneeded = (event) => {
                    const db = event.target.result;

                    // Criar object store se não existir
                    if (!db.objectStoreNames.contains(this.config.storeName)) {
                        const store = db.createObjectStore(this.config.storeName, { keyPath: 'key' });
                        store.createIndex('expiresAt', 'expiresAt', { unique: false });
                    }
                };

            } catch (error) {
                console.warn('Erro ao inicializar IndexedDB:', error);
                resolve(false);
            }
        });
    }

    /**
     * Obtém valor do cache
     * @param {string} key - Chave
     * @param {Object} options - Opções
     * @returns {Promise<any>}
     */
    async get(key, options = {}) {
        const fullKey = this.getFullKey(key);

        // Tentar L1 (memória)
        const memoryResult = this.getFromMemory(fullKey);
        if (memoryResult !== undefined) {
            this.stats.hits++;
            return memoryResult;
        }

        // Tentar L2 (localStorage)
        if (this.localStorageAvailable) {
            const localResult = this.getFromLocalStorage(fullKey);
            if (localResult !== undefined) {
                // Promover para L1
                this.setInMemory(fullKey, localResult.value, localResult.expiresAt);
                this.stats.hits++;
                return localResult.value;
            }
        }

        // Tentar L3 (IndexedDB)
        if (this.indexedDBAvailable && !options.skipIndexedDB) {
            const dbResult = await this.getFromIndexedDB(fullKey);
            if (dbResult !== undefined) {
                // Promover para L1 e L2
                const ttl = dbResult.expiresAt - Date.now();
                if (ttl > 0) {
                    this.setInMemory(fullKey, dbResult.value, dbResult.expiresAt);
                    this.stats.hits++;
                    return dbResult.value;
                }
            }
        }

        this.stats.misses++;
        return undefined;
    }

    /**
     * Define valor no cache
     * @param {string} key - Chave
     * @param {any} value - Valor
     * @param {Object} options - Opções
     * @returns {Promise<boolean>}
     */
    async set(key, value, options = {}) {
        const fullKey = this.getFullKey(key);
        const ttl = options.ttl || this.config.defaultTTL;
        const expiresAt = Date.now() + ttl;

        this.stats.sets++;

        // Salvar em L1 (memória)
        this.setInMemory(fullKey, value, expiresAt);

        // Salvar em L2 (localStorage) se não for muito grande
        if (this.localStorageAvailable && !options.skipLocalStorage) {
            this.setInLocalStorage(fullKey, value, expiresAt);
        }

        // Salvar em L3 (IndexedDB) para dados maiores ou persistentes
        if (this.indexedDBAvailable && (options.persistent || options.useIndexedDB)) {
            await this.setInIndexedDB(fullKey, value, expiresAt);
        }

        return true;
    }

    /**
     * Remove valor do cache
     * @param {string} key - Chave
     * @returns {Promise<boolean>}
     */
    async delete(key) {
        const fullKey = this.getFullKey(key);

        this.stats.deletes++;

        // Remover de L1
        this.memoryCache.delete(fullKey);

        // Remover de L2
        if (this.localStorageAvailable) {
            localStorage.removeItem(fullKey);
        }

        // Remover de L3
        if (this.indexedDBAvailable) {
            await this.deleteFromIndexedDB(fullKey);
        }

        return true;
    }

    /**
     * Verifica se chave existe no cache
     * @param {string} key - Chave
     * @returns {Promise<boolean>}
     */
    async has(key) {
        const value = await this.get(key);
        return value !== undefined;
    }

    /**
     * Limpa todo o cache
     * @returns {Promise<void>}
     */
    async clear() {
        // Limpar L1
        this.memoryCache.clear();

        // Limpar L2
        if (this.localStorageAvailable) {
            this.clearLocalStorage();
        }

        // Limpar L3
        if (this.indexedDBAvailable) {
            await this.clearIndexedDB();
        }

        console.log('Cache limpo');
    }

    /**
     * Invalida cache por padrão
     * @param {string} pattern - Padrão (ex: "user:*")
     * @returns {Promise<number>} Número de itens removidos
     */
    async invalidateByPattern(pattern) {
        let count = 0;
        const regex = new RegExp(pattern.replace('*', '.*'));
        const prefix = this.config.prefix;

        // Limpar de L1
        for (const key of this.memoryCache.keys()) {
            if (regex.test(key.replace(prefix, ''))) {
                this.memoryCache.delete(key);
                count++;
            }
        }

        // Limpar de L2
        if (this.localStorageAvailable) {
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                if (key && key.startsWith(prefix) && regex.test(key.replace(prefix, ''))) {
                    localStorage.removeItem(key);
                    count++;
                }
            }
        }

        return count;
    }

    // ==========================================================================
    // CACHE L1 - MEMÓRIA
    // ==========================================================================

    /**
     * Obtém valor da memória
     * @param {string} key - Chave
     * @returns {any}
     */
    getFromMemory(key) {
        const item = this.memoryCache.get(key);

        if (!item) return undefined;

        // Verificar expiração
        if (item.expiresAt && item.expiresAt < Date.now()) {
            this.memoryCache.delete(key);
            return undefined;
        }

        return item.value;
    }

    /**
     * Define valor na memória
     * @param {string} key - Chave
     * @param {any} value - Valor
     * @param {number} expiresAt - Timestamp de expiração
     */
    setInMemory(key, value, expiresAt) {
        // Verificar limite de itens
        if (this.memoryCache.size >= this.config.maxMemoryItems) {
            this.evictFromMemory();
        }

        this.memoryCache.set(key, { value, expiresAt });
    }

    /**
     * Remove itens antigos da memória (LRU simplificado)
     */
    evictFromMemory() {
        // Remover primeiro 20% dos itens (mais antigos)
        const toRemove = Math.ceil(this.config.maxMemoryItems * 0.2);
        const keys = Array.from(this.memoryCache.keys()).slice(0, toRemove);

        keys.forEach(key => this.memoryCache.delete(key));
    }

    // ==========================================================================
    // CACHE L2 - LOCALSTORAGE
    // ==========================================================================

    /**
     * Obtém valor do localStorage
     * @param {string} key - Chave
     * @returns {Object|undefined}
     */
    getFromLocalStorage(key) {
        try {
            const item = localStorage.getItem(key);
            if (!item) return undefined;

            const parsed = JSON.parse(item);

            // Verificar expiração
            if (parsed.expiresAt && parsed.expiresAt < Date.now()) {
                localStorage.removeItem(key);
                return undefined;
            }

            return parsed;
        } catch (error) {
            console.warn('Erro ao ler localStorage:', error);
            return undefined;
        }
    }

    /**
     * Define valor no localStorage
     * @param {string} key - Chave
     * @param {any} value - Valor
     * @param {number} expiresAt - Timestamp de expiração
     */
    setInLocalStorage(key, value, expiresAt) {
        try {
            const data = JSON.stringify({ value, expiresAt });

            // Verificar tamanho
            if (data.length > this.config.maxLocalStorageSize / 10) {
                // Dados muito grandes, pular localStorage
                return;
            }

            localStorage.setItem(key, data);
        } catch (error) {
            if (error.name === 'QuotaExceededError') {
                // Limpar cache antigo e tentar novamente
                this.cleanupLocalStorage();
                try {
                    localStorage.setItem(key, JSON.stringify({ value, expiresAt }));
                } catch (e) {
                    console.warn('localStorage cheio, não foi possível salvar');
                }
            } else {
                console.warn('Erro ao salvar localStorage:', error);
            }
        }
    }

    /**
     * Limpa localStorage do app
     */
    clearLocalStorage() {
        const prefix = this.config.prefix;

        for (let i = localStorage.length - 1; i >= 0; i--) {
            const key = localStorage.key(i);
            if (key && key.startsWith(prefix)) {
                localStorage.removeItem(key);
            }
        }
    }

    /**
     * Limpa itens expirados do localStorage
     */
    cleanupLocalStorage() {
        const prefix = this.config.prefix;
        const now = Date.now();

        for (let i = localStorage.length - 1; i >= 0; i--) {
            const key = localStorage.key(i);
            if (key && key.startsWith(prefix)) {
                try {
                    const item = JSON.parse(localStorage.getItem(key));
                    if (item && item.expiresAt && item.expiresAt < now) {
                        localStorage.removeItem(key);
                    }
                } catch (e) {
                    // Item inválido, remover
                    localStorage.removeItem(key);
                }
            }
        }
    }

    // ==========================================================================
    // CACHE L3 - INDEXEDDB
    // ==========================================================================

    /**
     * Obtém valor do IndexedDB
     * @param {string} key - Chave
     * @returns {Promise<Object|undefined>}
     */
    getFromIndexedDB(key) {
        return new Promise((resolve) => {
            if (!this.db) {
                resolve(undefined);
                return;
            }

            try {
                const transaction = this.db.transaction([this.config.storeName], 'readonly');
                const store = transaction.objectStore(this.config.storeName);
                const request = store.get(key);

                request.onsuccess = () => {
                    const result = request.result;

                    if (!result) {
                        resolve(undefined);
                        return;
                    }

                    // Verificar expiração
                    if (result.expiresAt && result.expiresAt < Date.now()) {
                        this.deleteFromIndexedDB(key);
                        resolve(undefined);
                        return;
                    }

                    resolve(result);
                };

                request.onerror = () => {
                    resolve(undefined);
                };
            } catch (error) {
                console.warn('Erro ao ler IndexedDB:', error);
                resolve(undefined);
            }
        });
    }

    /**
     * Define valor no IndexedDB
     * @param {string} key - Chave
     * @param {any} value - Valor
     * @param {number} expiresAt - Timestamp de expiração
     * @returns {Promise<boolean>}
     */
    setInIndexedDB(key, value, expiresAt) {
        return new Promise((resolve) => {
            if (!this.db) {
                resolve(false);
                return;
            }

            try {
                const transaction = this.db.transaction([this.config.storeName], 'readwrite');
                const store = transaction.objectStore(this.config.storeName);
                const request = store.put({ key, value, expiresAt });

                request.onsuccess = () => resolve(true);
                request.onerror = () => resolve(false);
            } catch (error) {
                console.warn('Erro ao salvar IndexedDB:', error);
                resolve(false);
            }
        });
    }

    /**
     * Remove valor do IndexedDB
     * @param {string} key - Chave
     * @returns {Promise<boolean>}
     */
    deleteFromIndexedDB(key) {
        return new Promise((resolve) => {
            if (!this.db) {
                resolve(false);
                return;
            }

            try {
                const transaction = this.db.transaction([this.config.storeName], 'readwrite');
                const store = transaction.objectStore(this.config.storeName);
                const request = store.delete(key);

                request.onsuccess = () => resolve(true);
                request.onerror = () => resolve(false);
            } catch (error) {
                resolve(false);
            }
        });
    }

    /**
     * Limpa IndexedDB
     * @returns {Promise<boolean>}
     */
    clearIndexedDB() {
        return new Promise((resolve) => {
            if (!this.db) {
                resolve(false);
                return;
            }

            try {
                const transaction = this.db.transaction([this.config.storeName], 'readwrite');
                const store = transaction.objectStore(this.config.storeName);
                const request = store.clear();

                request.onsuccess = () => resolve(true);
                request.onerror = () => resolve(false);
            } catch (error) {
                resolve(false);
            }
        });
    }

    /**
     * Limpa itens expirados do IndexedDB
     * @returns {Promise<number>}
     */
    cleanupIndexedDB() {
        return new Promise((resolve) => {
            if (!this.db) {
                resolve(0);
                return;
            }

            try {
                const transaction = this.db.transaction([this.config.storeName], 'readwrite');
                const store = transaction.objectStore(this.config.storeName);
                const index = store.index('expiresAt');
                const now = Date.now();
                const range = IDBKeyRange.upperBound(now);

                let count = 0;
                const request = index.openCursor(range);

                request.onsuccess = (event) => {
                    const cursor = event.target.result;
                    if (cursor) {
                        store.delete(cursor.primaryKey);
                        count++;
                        cursor.continue();
                    } else {
                        resolve(count);
                    }
                };

                request.onerror = () => resolve(0);
            } catch (error) {
                resolve(0);
            }
        });
    }

    // ==========================================================================
    // UTILIDADES
    // ==========================================================================

    /**
     * Obtém chave completa com prefixo
     * @param {string} key - Chave
     * @returns {string}
     */
    getFullKey(key) {
        return `${this.config.prefix}${key}`;
    }

    /**
     * Inicia limpeza periódica
     */
    startCleanupInterval() {
        // Limpar a cada 5 minutos
        setInterval(() => {
            this.cleanup();
        }, 5 * 60 * 1000);
    }

    /**
     * Limpa cache expirado
     */
    async cleanup() {
        const now = Date.now();

        // Limpar L1
        for (const [key, item] of this.memoryCache.entries()) {
            if (item.expiresAt && item.expiresAt < now) {
                this.memoryCache.delete(key);
            }
        }

        // Limpar L2
        if (this.localStorageAvailable) {
            this.cleanupLocalStorage();
        }

        // Limpar L3
        if (this.indexedDBAvailable) {
            await this.cleanupIndexedDB();
        }
    }

    /**
     * Obtém estatísticas do cache
     * @returns {Object}
     */
    getStats() {
        const hitRate = this.stats.hits + this.stats.misses > 0
            ? (this.stats.hits / (this.stats.hits + this.stats.misses) * 100).toFixed(2)
            : 0;

        return {
            ...this.stats,
            hitRate: `${hitRate}%`,
            memorySize: this.memoryCache.size,
            localStorageAvailable: this.localStorageAvailable,
            indexedDBAvailable: this.indexedDBAvailable
        };
    }

    /**
     * Reseta estatísticas
     */
    resetStats() {
        this.stats = {
            hits: 0,
            misses: 0,
            sets: 0,
            deletes: 0
        };
    }

    /**
     * Wrapper para cache de função (memoização)
     * @param {Function} fn - Função a ser cacheada
     * @param {Object} options - Opções
     * @returns {Function}
     */
    memoize(fn, options = {}) {
        const keyPrefix = options.keyPrefix || fn.name || 'memoized';
        const ttl = options.ttl || this.config.defaultTTL;

        return async (...args) => {
            const key = `${keyPrefix}:${JSON.stringify(args)}`;

            // Tentar obter do cache
            const cached = await this.get(key);
            if (cached !== undefined) {
                return cached;
            }

            // Executar função
            const result = await fn(...args);

            // Salvar no cache
            await this.set(key, result, { ttl });

            return result;
        };
    }
}

/**
 * Obtém instância singleton do CacheService
 * @param {Object} options - Opções
 * @returns {CacheService}
 */
export function getCacheService(options = {}) {
    if (!instance) {
        instance = new CacheService(options);
    }
    return instance;
}

export default CacheService;
