"""
Portal Sinais - Signals API Routes
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime

from app.services.engine import signal_engine
from app.services.exchange import exchange_service
from app.models.schemas import (
    SignalResponse, StrategyType, TimeFrame,
    DashboardStats, StrategyStatus
)

router = APIRouter(prefix="/signals", tags=["Signals"])


@router.get("/", response_model=List[dict])
async def get_recent_signals(
    symbol: Optional[str] = None,
    strategy: Optional[StrategyType] = None,
    timeframe: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """
    Retorna os sinais mais recentes.
    
    Filtros opcionais:
    - symbol: Filtrar por símbolo (ex: BTCUSDT)
    - strategy: Filtrar por estratégia (RSI, MACD, GCM)
    - timeframe: Filtrar por timeframe (1h, 4h, etc)
    """
    # TODO: Implementar busca do banco de dados
    # Por enquanto retorna lista vazia
    return []


@router.post("/analyze")
async def run_analysis(
    symbols: Optional[List[str]] = None,
    timeframes: Optional[List[str]] = None,
    strategies: Optional[List[str]] = None
):
    """
    Executa uma análise manual para os parâmetros especificados.
    
    Retorna os sinais gerados imediatamente.
    """
    try:
        signals = await signal_engine.run_analysis_cycle(
            symbols=symbols,
            timeframes=timeframes,
            active_strategies=strategies
        )
        
        return {
            "success": True,
            "signals_count": len(signals),
            "signals": [s.to_dict() for s in signals]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/{symbol}/{timeframe}")
async def analyze_single(
    symbol: str,
    timeframe: str,
    strategies: Optional[List[str]] = Query(default=None)
):
    """
    Analisa um símbolo específico em um timeframe.
    """
    try:
        # Buscar dados
        df = await exchange_service.fetch_ohlcv(symbol, timeframe)
        
        if df.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"No data available for {symbol}"
            )
        
        # Analisar
        signals = await signal_engine.analyze_symbol(
            symbol, timeframe, df, strategies
        )
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": len(df),
            "signals": [s.to_dict() for s in signals],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=DashboardStats)
async def get_stats():
    """
    Retorna estatísticas do dashboard.
    """
    # TODO: Implementar com dados reais do banco
    return DashboardStats(
        total_signals_today=0,
        long_signals=0,
        short_signals=0,
        active_symbols=len(signal_engine.settings.symbols_list),
        last_update=datetime.utcnow()
    )


@router.get("/strategies", response_model=List[StrategyStatus])
async def get_strategies_status():
    """
    Retorna status de cada estratégia.
    """
    strategies = []
    
    for name in signal_engine.strategies.keys():
        strategies.append(StrategyStatus(
            name=name,
            enabled=name in signal_engine.settings.strategies_list,
            signals_today=0,  # TODO: Buscar do banco
            last_signal=None
        ))
    
    return strategies
