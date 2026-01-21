# 🔍 Instagram Intelligence System 2026 (God Mode Ultimate)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)
![AI](https://img.shields.io/badge/AI-Powered-FF6F61?style=for-the-badge&logo=tensorflow&logoColor=white)
![OSINT](https://img.shields.io/badge/OSINT-Tools-4CAF50?style=for-the-badge&logo=searchengineland&logoColor=white)
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-FFA500?style=for-the-badge)
![Versão](https://img.shields.io/badge/Versão-2026.1.0-blue?style=for-the-badge)

**Sistema de Inteligência Digital para análise avançada de perfis do Instagram**

*Rastreamento de atividades • Análise de sentimento • Visão computacional • Previsão comportamental*

</div>

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura Técnica](#-arquitetura-técnica)
- [Estrutura de Arquivos](#-estrutura-de-arquivos)
- [Requisitos do Sistema](#-requisitos-do-sistema)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [API Reference](#-api-reference)
- [Módulos de IA](#-módulos-de-ia)
- [Roadmap](#-roadmap)
- [Licença](#-licença)

---

## 🎯 Sobre o Projeto

O **Instagram Intelligence System 2026** é uma plataforma de inteligência digital de última geração, projetada para análise profunda de perfis do Instagram. O sistema combina técnicas avançadas de web scraping, inteligência artificial e análise de dados para fornecer insights comportamentais, emocionais e preditivos sobre perfis de usuários.

### 🌟 Diferenciais

| Característica           | Descrição                                                               |
| ------------------------ | ----------------------------------------------------------------------- |
| **Self-Healing Scraper** | Sistema de scraping com fallback automático entre múltiplas estratégias |
| **TLS Fingerprinting**   | Rotação de fingerprints JA3 para evitar detecção                        |
| **Cache Hierárquico**    | Cache L1 (memória) + L2 (disco) com TTL configurável                    |
| **IA Integrada**         | Análise de sentimento, visão computacional e previsão comportamental    |
| **Arquitetura Async**    | Fila de tarefas assíncrona com workers paralelos                        |
| **WebSocket**            | Notificações em tempo real via Flask-SocketIO                           |

---

## 🚀 Funcionalidades

### ✅ Implementado (Fases 0-5.5)

#### 🏗️ Backend Foundation (Fase 1)
- **Sistema de Cache Inteligente** - Cache hierárquico L1/L2 com decorator `@cached(ttl=600)`
- **Backoff Exponencial** - Retry automático com jitter estocástico via `tenacity`
- **Rotação de Fingerprints TLS** - Pool de 10 fingerprints (Chrome, Safari, Edge)
- **Self-Healing Scraper** - Fallback: GraphQL → API v1 → HTML Parsing → Nodriver
- **Detector de Mudanças de API** - Comparação de schema com hashing
- **Fila Assíncrona** - Workers paralelos com prioridade (low, normal, high, critical)

#### 🛡️ Anti-Detecção 2026 (Fase 1.5)
- **JA4+ Fingerprinting** - Sucessor do JA3 com suporte HTTP/3 e QUIC
- **Canvas/WebGL Spoofing** - Ruído determinístico com Proxy injection
- **Audio Context Spoofing** - Fingerprint de áudio mascarado
- **Evasão Comportamental** - Curvas de Bézier, delays Poisson, typing patterns

#### 🧠 Inteligência Artificial (Fase 2)
- **Análise de Sentimento** - VADER + Léxico PT-BR + Mapeamento de 60+ emojis
- **Detecção de Nuances** - Ironia, sarcasmo, flerte, agressividade, entusiasmo
- **Motor Preditivo** - Análise de séries temporais com scipy/statsmodels
- **Score de Previsibilidade** - 0-100 com níveis: muito_baixo, baixo, médio, alto, muito_alto
- **Visão Computacional** - YOLOv8 Nano ONNX (~6MB) com 15 categorias semânticas

#### � OSINT Tático (Fase 3, 3.5, 3.6)
- **Account Health Check** - Detecção de shadowban, engagement drop
- **Device Fingerprinting** - Análise de dispositivos utilizados
- **Breach Check** - Verificação HIBP (Have I Been Pwned)
- **Cross-Platform Resolution** - Busca em 40+ plataformas (Sherlock-like)
- **GraphQL Monitor** - Auto-descoberta de doc_ids, circuit breaker
- **Advanced Analytics** - Stories, Reels, Hashtags, Audience Quality, Best Time

#### 🕸️ Inteligência de Redes (Fase 4)
- **Graph Engine** - Mapeamento de redes com NetworkX
- **Métricas de Centralidade** - PageRank, Betweenness, Closeness, Degree
- **Detecção de Comunidades** - Algoritmo Louvain
- **Exportação 3D** - JSON compatível com ForceGraph3D

#### 🥷 Stealth Ops (Fase 5)
- **Proxy Manager** - Pool com rotação inteligente e health check
- **Rate Limiter** - Backoff adaptativo e quota management
- **Navegação Biomimética** - Curvas de Bézier, delays estocásticos

#### 🧪 Testes de Integração (Fase 5.5)
- **Integration Test Runner** - 30+ endpoints testados
- **Edge Case Tests** - XSS, body vazio, usernames inválidos
- **Rate Limit Observer** - Documentação de limits por endpoint

### 🔄 Próximas Etapas (Fases 6-7)

- [ ] **Frontend Premium (Fase 6)** - Dashboard com CSS Variables, ES6 Modules, Gráficos 3D
- [ ] **Empacotamento (Fase 7)** - Docker, CI/CD, Documentação final


---

## 🏛️ Arquitetura Técnica

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (HTML/CSS/JS)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ index_fixed  │  │ styles_fixed │  │ script_fixed │              │
│  │    .html     │  │    .css      │  │     .js      │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FLASK API (flask_api_fixed.py)                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  REST Endpoints    │  WebSocket (SocketIO)  │  CORS Enabled    │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐
│  TASK QUEUE     │  │  CACHE MANAGER  │  │  INSTAGRAM SCRAPER 2025 │
│ (task_queue.py) │  │(cache_manager.py│  │(instagram_scraper_2025) │
│                 │  │                 │  │                         │
│ • AsyncQueue    │  │ • L1: Memória   │  │ • TLS Fingerprinting    │
│ • Workers (3)   │  │ • L2: Disco     │  │ • Self-Healing          │
│ • Prioridade    │  │ • TTL Config    │  │ • Multi-Strategy        │
└─────────────────┘  └─────────────────┘  └─────────────────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        MÓDULOS DE INTELIGÊNCIA                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │
│  │ SENTIMENTO     │  │ PREDITIVO      │  │ VISÃO COMPUTACIONAL    │ │
│  │ sentiment_     │  │ predictive_    │  │ ai_vision.py           │ │
│  │ analyzer.py    │  │ engine.py      │  │                        │ │
│  │                │  │                │  │                        │ │
│  │ • VADER PT-BR  │  │ • Séries Temp. │  │ • YOLOv8 ONNX          │ │
│  │ • Emojis (60+) │  │ • scipy/stats  │  │ • 15 Categorias        │ │
│  │ • Nuances      │  │ • Score 0-100  │  │ • Tags Semânticas      │ │
│  └────────────────┘  └────────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Padrões de Projeto Utilizados

| Padrão        | Aplicação                                                       |
| ------------- | --------------------------------------------------------------- |
| **Strategy**  | Self-Healing Scraper com múltiplas estratégias de scraping      |
| **Singleton** | CacheManager e TaskQueue com instância global única             |
| **Observer**  | WebSocket para notificações de tarefas em tempo real            |
| **Decorator** | `@cached()`, `@with_backoff_jitter()`, `@with_tenacity_retry()` |
| **Factory**   | Criação de sessões TLS com fingerprints diferentes              |

---

## 📁 Estrutura de Arquivos

```
instagram_tracker_fixed/
│
├── 📄 main.py                   # Ponto de entrada principal
├── 📦 requirements.txt          # Dependências Python
├── 📋 task.md                   # Plano de tarefas
├── 📋 implementation_plan.md    # Plano de implementação
├── 📖 README.md                 # Esta documentação
│
├── 📁 src/                      # Código fonte principal
│   ├── __init__.py
│   │
│   ├── 📁 ai/                   # Módulos de IA Generativa (LLM)
│   │   ├── gemini_client.py            # Cliente Google Gemini (11.4 KB)
│   │   └── ollama_client.py            # Cliente Ollama local (11.4 KB)
│   │
│   ├── 📁 core/                 # Módulos centrais
│   │   ├── instagram_scraper_2025.py   # Scraper com self-healing (986 linhas)
│   │   ├── browser_manager.py          # Gerenciador Nodriver + 2FA (1092 linhas)
│   │   ├── activity_tracker_2025.py    # Rastreador de atividades (980 linhas)
│   │   ├── cache_manager.py            # Cache hierárquico L1/L2 (498 linhas)
│   │   └── task_queue.py               # Fila de tarefas async (559 linhas)
│   │
│   ├── 📁 analytics/            # Módulos de análise de dados
│   │   ├── sentiment_analyzer.py       # Análise de sentimento (797 linhas)
│   │   ├── predictive_engine.py        # Motor preditivo (704 linhas)
│   │   └── advanced_analytics.py       # Analytics avançado (1476 linhas)
│   │
│   ├── 📁 intelligence/         # Módulos de IA
│   │   ├── ai_vision.py                # Visão computacional YOLO (693 linhas)
│   │   └── graph_engine.py             # Motor de grafos SNA (1291 linhas)
│   │
│   ├── 📁 osint/                # Módulos OSINT
│   │   ├── osint_toolkit.py            # Toolkit OSINT completo (1278 linhas)
│   │   └── graphql_monitor.py          # Monitor de GraphQL (1029 linhas)
│   │
│   ├── 📁 stealth/              # Módulos de anti-detecção
│   │   ├── anti_detection.py           # Anti-detecção 2026 (1458 linhas)
│   │   └── stealth_ops.py              # Operações furtivas (1262 linhas)
│   │
│   ├── 📁 api/                  # API REST
│   │   ├── flask_api_fixed.py          # Flask API (1628 linhas)
│   │   └── init_db.py                  # Inicialização do banco
│   │
│   └── 📁 tests/                # Testes
│       └── integration_tests.py        # Testes de integração (31.8 KB)
│
├── 📁 static/                   # Arquivos estáticos
│   ├── 📁 css/
│   │   └── dashboard-extensions.css    # Extensões CSS do dashboard (46.6 KB)
│   ├── 📁 js/
│   │   ├── 📁 core/             # 10 serviços JS (APIService, StateManager, etc.)
│   │   ├── 📁 components/       # 17 componentes JS (Dashboard, widgets, etc.)
│   │   └── main.js                     # Entry point JavaScript
│   ├── styles_fixed.css                # Estilos CSS principais
│   ├── script_fixed.js                 # JavaScript principal
│   ├── login.css                       # Estilos do login
│   └── login.js                        # JavaScript do login
│
├── 📁 templates/                # Templates HTML
│   ├── dashboard.html                  # Dashboard principal (24.1 KB)
│   ├── index_fixed.html                # Interface web principal
│   ├── sidebar_fixed.html              # Sidebar do dashboard
│   └── login.html                      # Página de login
│
├── 📁 data/                     # Dados persistidos
│   └── instagram_tracker.db            # Banco de dados SQLite
│
└── 📁 venv/                     # Ambiente virtual Python
```

**Total de linhas de código Python: ~17.000+** (atualizado em 20/01/2026)


---

## 💻 Requisitos do Sistema

### Obrigatórios

| Requisito         | Versão Mínima | Verificação               |
| ----------------- | ------------- | ------------------------- |
| **Python**        | 3.11+         | `python --version`        |
| **Google Chrome** | 120+          | `google-chrome --version` |
| **pip**           | 23.0+         | `pip --version`           |

### Hardware Recomendado

| Componente | Mínimo      | Recomendado |
| ---------- | ----------- | ----------- |
| **RAM**    | 4 GB        | 8 GB+       |
| **CPU**    | 2 cores     | 4+ cores    |
| **Disco**  | 2 GB livres | 5 GB+       |

---

## 🔧 Instalação

### 1. Clonar/Baixar o Projeto

```bash
cd d:\01-PROJETOS\instagram_tracker_fixed
```

### 2. Criar Ambiente Virtual

```bash
python -m venv venv
```

### 3. Ativar Ambiente Virtual

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.\venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 4. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 5. Inicializar Banco de Dados (se necessário)

```bash
python init_db.py
```

### 6. Executar o Servidor

```bash
python flask_api_fixed.py
```

O servidor iniciará em: **http://localhost:5000**

---

## 🖥️ Uso

### Interface Web

1. Acesse `http://localhost:5000` no navegador
2. Use o painel de controle para:
   - Rastrear atividades de um perfil
   - Obter informações de usuário
   - Visualizar posts e localizações
   - Analisar sentimentos e previsões

### Via Terminal (cURL)

```bash
# Verificar status da API
curl http://localhost:5000/api/instagram/status

# Obter informações de usuário
curl http://localhost:5000/api/instagram/user/username

# Analisar sentimento
curl http://localhost:5000/api/intelligence/sentiment/username

# Obter previsões
curl http://localhost:5000/api/intelligence/prediction/username

# Análise visual
curl http://localhost:5000/api/intelligence/visual/username
```

---

## 📚 API Reference

### Endpoints Principais

#### Status da API
```http
GET /api/instagram/status
```
**Resposta:**
```json
{
  "status": "online",
  "version": "3.0.0",
  "scraper_available": true,
  "cache_available": true,
  "socketio_available": true
}
```

---

#### Informações do Usuário
```http
GET /api/instagram/user/<username>
```
**Resposta:**
```json
{
  "success": true,
  "data": {
    "username": "exemplo",
    "full_name": "Nome Completo",
    "biography": "Bio do perfil",
    "followers_count": 1234,
    "following_count": 567,
    "posts_count": 89,
    "is_private": false,
    "profile_pic_url": "https://..."
  }
}
```

---

#### Posts do Usuário
```http
GET /api/instagram/posts/<username>?limit=20
```

---

#### Rastreamento de Atividades
```http
POST /api/instagram/track
```
**Body:**
```json
{
  "target": "username",
  "max_following": 50,
  "ignored_users": ["user1", "user2"]
}
```

---

### Endpoints de Inteligência

#### Análise de Sentimento
```http
GET /api/intelligence/sentiment/<username>?include_posts=true&max_posts=20
```
**Resposta:**
```json
{
  "success": true,
  "data": {
    "username": "exemplo",
    "analise_bio": {
      "polaridade": 0.75,
      "categoria": "positivo",
      "nuances": ["entusiasmo"]
    },
    "analise_agregada": {
      "polaridade_media": 0.68,
      "distribuicao": {"positivo": 15, "neutro": 3, "negativo": 2}
    }
  }
}
```

---

#### Previsão Comportamental
```http
GET /api/intelligence/prediction/<username>?max_posts=50
```
**Resposta:**
```json
{
  "success": true,
  "data": {
    "username": "exemplo",
    "score_previsibilidade": 78.5,
    "nivel_previsibilidade": "alto",
    "padroes_horarios": [...],
    "padroes_diarios": [...],
    "proximas_previsoes": [...],
    "tendencia": "estavel"
  }
}
```

---

#### Análise Visual
```http
GET /api/intelligence/visual/<username>?max_posts=20
```
**Resposta:**
```json
{
  "success": true,
  "data": {
    "username": "exemplo",
    "total_imagens": 20,
    "categorias_dominantes": ["viagem", "social", "comida"],
    "tags_frequentes": ["praia", "amigos", "restaurante"],
    "perfil_visual": {
      "tipo_conteudo": "lifestyle"
    }
  }
}
```

---

### Endpoints de Tarefas Assíncronas

#### Enfileirar Tarefa
```http
POST /api/tasks/enqueue
```
**Body:**
```json
{
  "task_type": "scrape_profile",
  "metadata": {"username": "exemplo"},
  "priority": "high"
}
```

---

#### Status da Tarefa
```http
GET /api/tasks/status/<task_id>
```

---

#### Listar Tarefas
```http
GET /api/tasks/list?status=pending
```

---

#### Estatísticas da Fila
```http
GET /api/tasks/stats
```

---

## 🧠 Módulos de IA

### 1. Análise de Sentimento (`sentiment_analyzer.py`)

| Componente       | Descrição                                       |
| ---------------- | ----------------------------------------------- |
| **VADER**        | Análise base com léxico inglês                  |
| **Léxico PT-BR** | 100+ palavras com valência customizada          |
| **Emojis**       | 60+ emojis mapeados para sentimento             |
| **Nuances**      | Detecta ironia, sarcasmo, flerte, agressividade |

**Métricas de Saída:**
- **Polaridade**: -1.0 (muito negativo) a +1.0 (muito positivo)
- **Subjetividade**: 0.0 (objetivo) a 1.0 (subjetivo)
- **Intensidade**: 0.0 a 1.0
- **Categoria**: muito_negativo, negativo, neutro, positivo, muito_positivo

---

### 2. Motor Preditivo (`predictive_engine.py`)

| Análise                      | Descrição                                  |
| ---------------------------- | ------------------------------------------ |
| **Padrões Horários**         | Probabilidade de atividade por hora (0-23) |
| **Padrões Diários**          | Frequência por dia da semana               |
| **Intervalo Médio**          | Tempo médio entre posts                    |
| **Tendência**                | crescente, decrescente ou estável          |
| **Score de Previsibilidade** | 0-100 baseado em consistência              |

**Níveis de Previsibilidade:**
- `muito_baixo`: 0-20
- `baixo`: 21-40
- `médio`: 41-60
- `alto`: 61-80
- `muito_alto`: 81-100

---

### 3. Visão Computacional (`ai_vision.py`)

| Feature        | Descrição                        |
| -------------- | -------------------------------- |
| **Modelo**     | YOLOv8 Nano ONNX (~6MB)          |
| **Classes**    | 80 classes COCO                  |
| **Categorias** | 15 categorias semânticas         |
| **Tags**       | Tags automatizadas por categoria |

**Categorias Semânticas:**
- Luxo, Viagem, Esporte, Social, Trabalho
- Comida, Pets, Natureza, Moda, Arte
- Tecnologia, Família, Fitness, Selfie, Outro

---

## 🗺️ Roadmap

### ✅ Fase 0: Validação (Concluída)
- [x] Verificação de ambiente
- [x] Auditoria de código legado

### ✅ Fase 1: Backend Foundation (Concluída)
- [x] Cache Manager
- [x] Task Queue
- [x] TLS Fingerprinting
- [x] Self-Healing Scraper

### ✅ Fase 2: AI Core (Concluída)
- [x] Sentiment Analyzer
- [x] Predictive Engine
- [x] AI Vision

### 🔄 Fase 3: OSINT Toolkit (Próxima)
- [ ] Account Health Check
- [ ] Device Fingerprinting
- [ ] Breach Check
- [ ] Cross-Platform Search

### 📋 Fase 4: Graph Engine
- [ ] NetworkX Integration
- [ ] Louvain Communities
- [ ] ForceGraph3D Export

### 📋 Fase 5: Stealth Ops
- [ ] SOCKS5/Tor Support
- [ ] Navegação Biomimética

### 📋 Fase 6: Frontend Premium
- [ ] CSS Variables
- [ ] BEM Refactoring
- [ ] ES6 Modules

### 📋 Fase 7: Empacotamento
- [ ] Documentação técnica
- [ ] Testes automatizados
- [ ] Release package

---

## 📊 Estatísticas do Projeto (Atualizado em 20/01/2026)

| Métrica                    | Valor                                  |
| -------------------------- | -------------------------------------- |
| **Total de Linhas Python** | ~17.000+                               |
| **Arquivos Python**        | 19 (principais)                        |
| **Componentes JavaScript** | 28 (10 core + 17 components + main.js) |
| **Endpoints da API**       | 49+                                    |
| **Dependências**           | 45+                                    |
| **Classes Principais**     | 100+                                   |
| **Templates HTML**         | 4                                      |
| **Arquivos CSS**           | 4                                      |

---

## ⚠️ Avisos Importantes

> [!CAUTION]
> Este projeto é destinado **exclusivamente para fins educacionais e de pesquisa**. O uso indevido para violação de privacidade ou termos de serviço é **estritamente proibido**.

> [!WARNING]
> O scraping de redes sociais pode violar os Termos de Serviço da plataforma. Use com responsabilidade e dentro dos limites legais.

> [!IMPORTANT]
> Não realize buscas ativas via hashtags. Toda análise deve ser sobre o conteúdo do perfil alvo e suas conexões diretas.

---

## 📄 Licença

Este projeto é de uso privado e educacional.

---

## 👨‍💻 Desenvolvido por

**Instagram Intelligence System 2026**

*Versão God Mode Ultimate - Atualizado em 20/01/2026*

---

<div align="center">

**⭐ Se este projeto foi útil, considere dar uma estrela! ⭐**

</div>
