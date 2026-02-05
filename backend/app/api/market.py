"""
Portal Sinais - Market Data API Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.services.exchange import exchange_service
from app.models.schemas import SymbolInfo, OHLCV

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str):
    """
    Retorna o ticker atual de um símbolo.
    """
    ticker = await exchange_service.fetch_ticker(symbol)
    
    if not ticker:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker not found for {symbol}"
        )
    
    return ticker


@router.get("/tickers")
async def get_multiple_tickers(
    symbols: str = Query(..., description="Símbolos separados por vírgula")
):
    """
    Retorna tickers de múltiplos símbolos.
    
    Exemplo: /market/tickers?symbols=BTCUSDT,ETHUSDT,SOLUSDT
    """
    symbol_list = [s.strip() for s in symbols.split(",")]
    
    tickers = await exchange_service.fetch_multiple_tickers(symbol_list)
    
    return {
        "count": len(tickers),
        "tickers": list(tickers.values())
    }


@router.get("/ohlcv/{symbol}")
async def get_ohlcv(
    symbol: str,
    timeframe: str = Query(default="1h", regex="^(1m|5m|15m|30m|1h|4h|1d|1w)$"),
    limit: int = Query(default=100, ge=10, le=500)
):
    """
    Retorna candles OHLCV de um símbolo.
    """
    df = await exchange_service.fetch_ohlcv(symbol, timeframe, limit)
    
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data available for {symbol} on {timeframe}"
        )
    
    # Converter para lista de dicts
    candles = df.reset_index().to_dict(orient="records")
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "count": len(candles),
        "candles": candles
    }


@router.get("/symbols")
async def list_available_symbols(quote: str = "USDT"):
    """
    Lista todos os símbolos disponíveis na exchange.
    """
    symbols = await exchange_service.get_all_symbols(quote)
    
    return {
        "quote": quote,
        "count": len(symbols),
        "symbols": symbols
    }


@router.get("/price/{symbol}")
async def get_current_price(symbol: str):
    """
    Retorna apenas o preço atual de um símbolo.
    """
    ticker = await exchange_service.fetch_ticker(symbol)
    
    if not ticker or not ticker.get("last"):
        raise HTTPException(
            status_code=404,
            detail=f"Price not found for {symbol}"
        )
    
    return {
        "symbol": symbol,
        "price": ticker["last"],
        "change_24h": ticker.get("change"),
        "timestamp": datetime.utcnow().isoformat()
    }
