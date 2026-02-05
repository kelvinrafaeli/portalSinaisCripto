"""
Portal Sinais - FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.core.config import get_settings
from app.api import api_router
from app.services.engine import signal_engine
from app.api.websocket import router as websocket_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager para iniciar/parar o worker.
    """
    settings = get_settings()
    
    logger.info("=" * 50)
    logger.info("🚀 Portal Sinais - Starting...")
    logger.info(f"📊 Strategies: {settings.strategies_list}")
    logger.info(f"💹 Symbols: {len(settings.symbols_list)} configured")
    logger.info(f"⏱️  Timeframes: {settings.timeframes_list}")
    logger.info(f"🔄 Worker interval: {settings.worker_interval_seconds}s")
    logger.info("=" * 50)
    
    # Iniciar engine em background
    await signal_engine.start()
    
    yield
    
    # Parar engine
    logger.info("Shutting down Signal Engine...")
    await signal_engine.stop()
    logger.info("Portal Sinais stopped.")


# Criar aplicação FastAPI
app = FastAPI(
    title="Portal Sinais",
    description="""
    🚀 Sistema de Sinais de Trading em Tempo Real
    
    ## Features
    
    * **Múltiplas Estratégias**: RSI, MACD, GCM Heikin Ashi, COMBO
    * **WebSocket**: Sinais em tempo real
    * **Configurável**: Parâmetros ajustáveis via API
    * **Multi-Timeframe**: Suporte a 1m, 5m, 15m, 1h, 4h, 1d
    
    ## Estratégias
    
    - **RSI**: Cruzamento de RSI com média de sinal + filtro EMA50
    - **MACD**: Cruzamento MACD clássico (12, 26, 9)
    - **GCM**: GCM Heikin Ashi RSI Trend Cloud
    - **COMBO**: Confirmação MACD + RSI na mesma direção
    
    ## WebSocket
    
    Conecte em `/ws` para receber sinais em tempo real.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(api_router, prefix="/api/v1")

# WebSocket na raiz (sem prefixo)
app.include_router(websocket_router)


@app.get("/")
async def root():
    """Health check e informações básicas"""
    settings = get_settings()
    
    return {
        "name": "Portal Sinais",
        "status": "running",
        "version": "1.0.0",
        "engine_status": signal_engine.status,
        "endpoints": {
            "api": "/api/v1",
            "docs": "/docs",
            "websocket": "/ws"
        }
    }


@app.get("/health")
async def health_check():
    """Health check para load balancers"""
    return {
        "status": "healthy",
        "engine_running": signal_engine.is_running
    }


@app.post("/api/v1/engine/start")
async def start_engine():
    """Inicia o engine manualmente"""
    if signal_engine.is_running:
        return {"message": "Engine already running"}
    
    await signal_engine.start()
    return {"message": "Engine started", "status": signal_engine.status}


@app.post("/api/v1/engine/stop")
async def stop_engine():
    """Para o engine manualmente"""
    if not signal_engine.is_running:
        return {"message": "Engine not running"}
    
    await signal_engine.stop()
    return {"message": "Engine stopped"}


@app.get("/api/v1/engine/status")
async def engine_status():
    """Retorna status do engine"""
    return signal_engine.status


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
