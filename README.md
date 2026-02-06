# 🚀 Portal Alertas

Sistema de Alertas de Trading em Tempo Real com análise de múltiplos indicadores técnicos.

## 📊 Features

- **Múltiplas Estratégias**: RSI, MACD, GCM Heikin Ashi, COMBO
- **WebSocket**: Alertas em tempo real
- **Configurável**: Parâmetros ajustáveis via UI
- **Multi-Timeframe**: Suporte a 1m, 5m, 15m, 1h, 4h, 1d
- **Dark Mode**: Interface estilo TradingView

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js 14)                    │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│   │   Sidebar   │  │   Header    │  │   Signal Feed       │ │
│   │  (Config)   │  │  (Filters)  │  │  (Real-time)        │ │
│   └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket / REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│   │ Signal Engine│  │  Exchange    │  │   WebSocket      │  │
│   │   (Worker)   │  │   Service    │  │    Manager       │  │
│   └──────────────┘  └──────────────┘  └──────────────────┘  │
│           │                 │                               │
│           ▼                 ▼                               │
│   ┌──────────────────────────────┐                         │
│   │         Strategies           │                         │
│   │  RSI │ MACD │ GCM │ COMBO   │                         │
│   └──────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│   ┌──────────────┐           ┌──────────────────────────┐   │
│   │  PostgreSQL  │           │         Redis            │   │
│   │  (Configs &  │           │  (Cache & Queue)         │   │
│   │   Signals)   │           │                          │   │
│   └──────────────┘           └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │     Binance     │
                    │    (via CCXT)   │
                    └─────────────────┘
```

## 🛠️ Estratégias

### RSI
- Detecta cruzamentos do RSI com a média de sinal
- Filtro EMA50 para confirmar tendência
- Alertas de sobrecompra/sobrevenda

### MACD
- Cruzamento clássico MACD (12, 26, 9)
- Detecta mudanças de momentum

### GCM Heikin Ashi RSI Trend Cloud
- Converte RSI para formato Heikin Ashi
- Detecta mudanças de tendência no cloud

### COMBO
- Confirmação quando MACD e RSI cruzam juntos
- Janela de confirmação configurável
- Filtro EMA50 obrigatório

## 🚀 Quick Start

### Com Docker (Recomendado)

```bash
# Clonar/acessar o projeto
cd PortalSinais

# Subir todos os serviços
docker-compose up -d

# Acessar
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Sem Docker

#### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OU
.\venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Copiar e configurar .env
cp .env.example .env

# Rodar
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Copiar e configurar .env
cp .env.example .env.local

# Rodar
npm run dev
```

## 📡 API Endpoints

### Signals
- `GET /api/v1/signals/` - Lista alertas recentes
- `POST /api/v1/signals/analyze` - Executa análise manual
- `GET /api/v1/signals/analyze/{symbol}/{timeframe}` - Analisa símbolo específico
- `GET /api/v1/signals/stats` - Estatísticas do dashboard

### Configuration
- `GET /api/v1/config/` - Retorna configuração atual
- `PUT /api/v1/config/update` - Atualiza configurações
- `GET /api/v1/config/symbols` - Lista símbolos disponíveis
- `GET /api/v1/config/timeframes` - Lista timeframes

### Market Data
- `GET /api/v1/market/ticker/{symbol}` - Ticker atual
- `GET /api/v1/market/ohlcv/{symbol}` - Candles OHLCV
- `GET /api/v1/market/price/{symbol}` - Preço atual

### WebSocket
- `WS /ws` - Stream de alertas em tempo real
- `WS /ws/signals?symbols=...&timeframes=...` - Stream com filtros

### Engine Control
- `POST /api/v1/engine/start` - Inicia o worker
- `POST /api/v1/engine/stop` - Para o worker
- `GET /api/v1/engine/status` - Status do engine

## ⚙️ Configuração

### Parâmetros Principais

| Parâmetro | Tipo | Descrição | Padrão |
|-----------|------|-----------|--------|
| `ACTIVE_STRATEGIES` | List | Estratégias ativas | `["GCM", "COMBO", "MACD", "RSI"]` |
| `TIMEFRAMES` | List | Timeframes analisados | `["5m", "15m", "1h", "4h"]` |
| `SYMBOLS` | List | Pares monitorados | `["BTCUSDT", "ETHUSDT", ...]` |
| `RSI_PERIOD` | Int | Período do RSI | `14` |
| `RSI_SIGNAL` | Int | Período da média do RSI | `9` |
| `MACD_FAST` | Int | EMA rápida do MACD | `12` |
| `MACD_SLOW` | Int | EMA lenta do MACD | `26` |
| `MACD_SIGNAL` | Int | Linha de sinal | `9` |
| `HARSI_LEN` | Int | Período do HA-RSI | `10` |
| `HARSI_SMOOTH` | Int | Suavização do HA-RSI | `5` |
| `WORKER_INTERVAL_SECONDS` | Int | Intervalo de análise | `60` |

## 📱 Interface

### Sidebar (Esquerda)
- Checkboxes para ativar/desativar estratégias
- Inputs para configurar períodos
- Botão de controle do Engine

### Header (Topo)
- Status de conexão
- Contadores de alertas Long/Short
- Filtros rápidos por Timeframe
- Filtros rápidos por Estratégia

### Feed (Centro)
- Lista de alertas em tempo real
- Cards coloridos (verde=Long, vermelho=Short)
- Detalhes do sinal (RSI, MACD, EMA50)

## 🔔 Notificações

O sistema suporta:
- Browser Push Notifications
- Alertas visuais (flash e glow)
- Som (configurável)

## 📄 Licença

MIT License
