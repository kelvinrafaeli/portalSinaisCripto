"""
Portal Sinais - Config API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict
from pydantic import BaseModel
import json
from pathlib import Path

from app.core.config import get_settings, Settings
from app.services.engine import signal_engine
from app.models.schemas import (
    AlertConfigBase, AlertConfigCreate, AlertConfigUpdate, AlertConfigResponse
)

router = APIRouter(prefix="/config", tags=["Configuration"])

# Arquivo de configuração de timeframes por estratégia
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
STRATEGY_TIMEFRAMES_FILE = CONFIG_DIR / "strategy_timeframes.json"

# Timeframes padrão por estratégia
DEFAULT_STRATEGY_TIMEFRAMES = {
    "GCM": ["15m", "1h", "4h"],
    "RSI": ["15m", "1h", "4h"],
    "MACD": ["15m", "1h", "4h"],
    "RSI_EMA50": ["1h", "4h"],
    "SCALPING": ["3m", "5m"],
    "SWING_TRADE": ["4h", "1d"],
    "DAY_TRADE": ["15m", "1h"],
    "JFN": ["15m", "1h", "4h"],
}


def load_strategy_timeframes() -> Dict[str, List[str]]:
    """Carrega configuração de timeframes por estratégia"""
    try:
        if STRATEGY_TIMEFRAMES_FILE.exists():
            with open(STRATEGY_TIMEFRAMES_FILE, 'r') as f:
                loaded = json.load(f)
                merged = DEFAULT_STRATEGY_TIMEFRAMES.copy()
                merged.update(loaded)
                return merged
    except Exception:
        pass
    return DEFAULT_STRATEGY_TIMEFRAMES.copy()


def save_strategy_timeframes(timeframes: Dict[str, List[str]]):
    """Salva configuração de timeframes por estratégia"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(STRATEGY_TIMEFRAMES_FILE, 'w') as f:
        json.dump(timeframes, f, indent=2)


class StrategyTimeframesUpdate(BaseModel):
    strategy_timeframes: Dict[str, List[str]]


@router.get("/")
async def get_current_config():
    """
    Retorna a configuração atual do sistema.
    """
    settings = get_settings()
    strategy_timeframes = load_strategy_timeframes()
    
    return {
        "strategies": {
            "active": settings.strategies_list,
            "available": ["RSI", "MACD", "GCM", "RSI_EMA50", "SCALPING", "SWING_TRADE", "DAY_TRADE", "JFN"],
            "timeframes": strategy_timeframes
        },
        "strategy_params": signal_engine.get_strategy_params(),
        "symbols": settings.symbols_list,
        "timeframes": settings.timeframes_list,
        "rsi": {
            "period": settings.rsi_period,
            "signal": settings.rsi_signal,
            "overbought": settings.rsi_overbought,
            "oversold": settings.rsi_oversold
        },
        "macd": {
            "fast": settings.macd_fast,
            "slow": settings.macd_slow,
            "signal": settings.macd_signal
        },
        "gcm": {
            "harsi_len": settings.harsi_len,
            "harsi_smooth": settings.harsi_smooth
        },
        "worker": {
            "chunk_size": settings.chunk_size,
            "interval_seconds": settings.worker_interval_seconds
        }
    }


@router.put("/update")
async def update_config(config: dict):
    """
    Atualiza configurações em tempo de execução.
    
    Nota: Alterações não são persistidas permanentemente.
    Para persistir, altere o .env ou banco de dados.
    """
    try:
        # Atualizar estratégias no engine
        signal_engine.update_strategies(config)
        
        return {
            "success": True,
            "message": "Configuration updated",
            "applied": config
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/symbols")
async def get_available_symbols():
    """
    Retorna símbolos disponíveis para monitoramento.
    """
    settings = get_settings()
    
    return {
        "configured": settings.symbols_list,
        "popular": [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
            "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
            "DOTUSDT", "MATICUSDT", "LINKUSDT", "UNIUSDT",
            "ATOMUSDT", "LTCUSDT", "NEARUSDT", "APTUSDT"
        ]
    }


@router.put("/symbols")
async def update_symbols(symbols: List[str]):
    """
    Atualiza lista de símbolos monitorados.
    """
    if not symbols:
        raise HTTPException(status_code=400, detail="Symbol list cannot be empty")
    
    # Validar formato dos símbolos
    for symbol in symbols:
        if not symbol.endswith("USDT") and not symbol.endswith("BTC"):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid symbol format: {symbol}"
            )
    
    # TODO: Persistir no banco ou atualizar .env
    
    return {
        "success": True,
        "symbols": symbols
    }


@router.get("/timeframes")
async def get_available_timeframes():
    """
    Retorna timeframes disponíveis.
    """
    return {
        "available": ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"],
        "configured": get_settings().timeframes_list,
        "recommended": ["1h", "4h", "1d"]
    }


@router.put("/timeframes")
async def update_timeframes(timeframes: List[str]):
    """
    Atualiza timeframes monitorados.
    """
    valid_tfs = {"1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"}
    
    for tf in timeframes:
        if tf not in valid_tfs:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe: {tf}"
            )
    
    # TODO: Persistir no banco
    
    return {
        "success": True,
        "timeframes": timeframes
    }


@router.get("/strategy-timeframes")
async def get_strategy_timeframes():
    """
    Retorna os timeframes configurados por estratégia.
    """
    return load_strategy_timeframes()


@router.put("/strategy-timeframes")
async def update_strategy_timeframes(data: StrategyTimeframesUpdate):
    """
    Atualiza os timeframes para cada estratégia.
    
    Exemplo:
    {
        "strategy_timeframes": {
            "GCM": ["15m", "1h", "4h"],
            "RSI": ["1h", "4h"],
            "SCALPING": ["3m", "5m"]
        }
    }
    """
    valid_tfs = {"1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"}
    
    # Validar timeframes
    for strategy, timeframes in data.strategy_timeframes.items():
        for tf in timeframes:
            if tf not in valid_tfs:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid timeframe '{tf}' for strategy '{strategy}'"
                )
    
    # Carregar configuração atual e mesclar
    current = load_strategy_timeframes()
    current.update(data.strategy_timeframes)
    
    # Salvar
    save_strategy_timeframes(current)
    
    # Atualizar engine se necessário
    signal_engine.update_strategy_timeframes(current)
    
    return {
        "success": True,
        "strategy_timeframes": current
    }
