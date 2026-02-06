"""Portal Sinais - API Routes"""
from fastapi import APIRouter
from .signals import router as signals_router
from .config import router as config_router
from .market import router as market_router
from .websocket import router as websocket_router
from .telegram import router as telegram_router
from .cryptobubbles import router as cryptobubbles_router

# Router principal
api_router = APIRouter()

# Incluir sub-routers
api_router.include_router(signals_router)
api_router.include_router(config_router)
api_router.include_router(market_router)
api_router.include_router(websocket_router)
api_router.include_router(telegram_router)
api_router.include_router(cryptobubbles_router)

__all__ = ["api_router"]
