"""
Portal Sinais - CryptoBubbles API Routes
Endpoints para acessar dados do CryptoBubbles.
"""
from fastapi import APIRouter, Query
from typing import Optional

from app.services.cryptobubbles import cryptobubbles_service
from app.core.config import get_settings

router = APIRouter(prefix="/cryptobubbles", tags=["CryptoBubbles"])


@router.get("/summary")
async def get_summary():
    """
    Retorna um resumo dos dados do CryptoBubbles.
    
    Inclui:
    - Total de moedas disponíveis
    - Quantidade negociável na Binance
    - Top 5 maiores altas
    - Top 5 maiores quedas
    """
    return await cryptobubbles_service.get_summary()


@router.get("/top-volatile")
async def get_top_volatile(
    limit: int = Query(default=100, ge=1, le=500, description="Quantidade de pares"),
    exclude_stablecoins: bool = Query(default=True, description="Excluir stablecoins"),
    min_volume: float = Query(default=0, ge=0, description="Volume mínimo em USD"),
    force_refresh: bool = Query(default=False, description="Forçar atualização do cache")
):
    """
    Retorna os símbolos com maior variação nas últimas 24h.
    
    A variação é calculada em valor absoluto (considera tanto altas quanto quedas).
    
    Returns:
        Lista de símbolos no formato Binance (ex: BTCUSDT)
    """
    symbols = await cryptobubbles_service.get_top_volatile_symbols(
        limit=limit,
        exclude_stablecoins=exclude_stablecoins,
        min_volume=min_volume,
        force_refresh=force_refresh
    )
    
    return {
        "count": len(symbols),
        "symbols": symbols
    }


@router.get("/gainers")
async def get_top_gainers(
    limit: int = Query(default=50, ge=1, le=200, description="Quantidade de pares"),
    exclude_stablecoins: bool = Query(default=True, description="Excluir stablecoins"),
    force_refresh: bool = Query(default=False, description="Forçar atualização do cache")
):
    """
    Retorna os símbolos com maiores ganhos nas últimas 24h.
    """
    symbols = await cryptobubbles_service.get_top_gainers(
        limit=limit,
        exclude_stablecoins=exclude_stablecoins,
        force_refresh=force_refresh
    )
    
    return {
        "count": len(symbols),
        "symbols": symbols
    }


@router.get("/losers")
async def get_top_losers(
    limit: int = Query(default=50, ge=1, le=200, description="Quantidade de pares"),
    exclude_stablecoins: bool = Query(default=True, description="Excluir stablecoins"),
    force_refresh: bool = Query(default=False, description="Forçar atualização do cache")
):
    """
    Retorna os símbolos com maiores quedas nas últimas 24h.
    """
    symbols = await cryptobubbles_service.get_top_losers(
        limit=limit,
        exclude_stablecoins=exclude_stablecoins,
        force_refresh=force_refresh
    )
    
    return {
        "count": len(symbols),
        "symbols": symbols
    }


@router.get("/active-pairs")
async def get_active_pairs(
    force_refresh: bool = Query(default=False, description="Forçar atualização do cache")
):
    """
    Retorna os pares atualmente monitorados pelo sistema com suas variações.
    
    Este endpoint retorna os pares que estão sendo analisados pelo engine,
    com base nas configurações de CryptoBubbles.
    
    Returns:
        Lista de pares com símbolo, nome, preço e variações (1h, 24h, 7d)
    """
    settings = get_settings()
    
    if not settings.use_cryptobubbles:
        # Se não usa CryptoBubbles, retorna os símbolos estáticos sem variações
        return {
            "source": "config",
            "count": len(settings.symbols_list),
            "pairs": [{"binance_symbol": s, "symbol": s.replace("USDT", ""), "name": s} for s in settings.symbols_list]
        }
    
    # Buscar dados detalhados dos pares ativos
    pairs = await cryptobubbles_service.get_top_volatile_with_details(
        limit=settings.cryptobubbles_top_limit,
        exclude_stablecoins=settings.cryptobubbles_exclude_stablecoins,
        min_volume=settings.cryptobubbles_min_volume,
        force_refresh=force_refresh
    )
    
    # Fallback para config se CryptoBubbles falhar (sem dados)
    if not pairs:
        return {
            "source": "config_fallback",
            "count": len(settings.symbols_list),
            "message": "CryptoBubbles indisponível, usando símbolos do config",
            "pairs": [{"binance_symbol": s, "symbol": s.replace("USDT", ""), "name": s} for s in settings.symbols_list]
        }
    
    return {
        "source": "cryptobubbles",
        "count": len(pairs),
        "limit": settings.cryptobubbles_top_limit,
        "pairs": pairs
    }


@router.get("/coin/{symbol}")
async def get_coin_details(symbol: str):
    """
    Retorna detalhes de uma moeda específica.
    
    Args:
        symbol: Símbolo da moeda (ex: BTC, ETH)
    """
    coin = await cryptobubbles_service.get_coin_details(symbol)
    
    if not coin:
        return {"error": f"Coin {symbol} not found"}
    
    return {
        "id": coin.id,
        "name": coin.name,
        "symbol": coin.symbol,
        "rank": coin.rank,
        "price": coin.price,
        "marketcap": coin.marketcap,
        "volume": coin.volume,
        "binance_symbol": coin.binance_symbol,
        "performance": {
            "hour": coin.performance_hour,
            "day": coin.performance_day,
            "week": coin.performance_week
        }
    }


@router.get("/all")
async def get_all_coins(
    limit: int = Query(default=100, ge=1, le=1000, description="Limite de moedas"),
    exclude_stablecoins: bool = Query(default=True, description="Excluir stablecoins"),
    force_refresh: bool = Query(default=False, description="Forçar atualização do cache")
):
    """
    Retorna lista completa de moedas com todos os dados.
    """
    coins = await cryptobubbles_service.fetch_all_coins(force_refresh=force_refresh)
    
    # Filtrar stablecoins se necessário
    if exclude_stablecoins:
        coins = [c for c in coins if not c.stable]
    
    # Aplicar limite
    coins = coins[:limit]
    
    return {
        "count": len(coins),
        "coins": [
            {
                "id": c.id,
                "name": c.name,
                "symbol": c.symbol,
                "rank": c.rank,
                "price": c.price,
                "marketcap": c.marketcap,
                "volume": c.volume,
                "binance_symbol": c.binance_symbol,
                "performance_day": c.performance_day,
                "performance_hour": c.performance_hour,
                "performance_week": c.performance_week
            }
            for c in coins
        ]
    }
