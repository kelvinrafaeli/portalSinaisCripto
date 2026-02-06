"""
Portal Sinais - Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class StrategyType(str, Enum):
    RSI = "RSI"
    MACD = "MACD"
    GCM = "GCM"


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class TimeFrame(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


# ============ Signal Schemas ============

class SignalBase(BaseModel):
    symbol: str
    timeframe: str
    strategy: StrategyType
    direction: Direction
    price: float
    message: Optional[str] = None


class SignalCreate(SignalBase):
    rsi_value: Optional[float] = None
    macd_value: Optional[float] = None
    macd_signal_value: Optional[float] = None
    ema50_value: Optional[float] = None
    raw_data: Optional[dict] = None


class SignalResponse(SignalBase):
    id: int
    rsi_value: Optional[float] = None
    macd_value: Optional[float] = None
    ema50_value: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SignalWebSocket(BaseModel):
    """Formato do sinal enviado via WebSocket"""
    type: str = "signal"
    symbol: str
    timeframe: str
    strategy: str
    direction: str
    price: float
    message: str
    timestamp: str
    
    # Valores dos indicadores
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    ema50: Optional[float] = None


# ============ Config Schemas ============

class AlertConfigBase(BaseModel):
    name: str = "default"
    use_rsi: bool = True
    use_macd: bool = True
    use_gcm: bool = True
    
    rsi_period: int = 14
    rsi_signal: int = 9
    rsi_overbought: int = 85
    rsi_oversold: int = 15
    
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    harsi_len: int = 10
    harsi_smooth: int = 5
    
    confirm_window: int = 6
    
    symbols: List[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    timeframes: List[str] = ["1h", "4h"]
    is_active: bool = True


class AlertConfigCreate(AlertConfigBase):
    pass


class AlertConfigUpdate(BaseModel):
    name: Optional[str] = None
    use_rsi: Optional[bool] = None
    use_macd: Optional[bool] = None
    use_gcm: Optional[bool] = None
    rsi_period: Optional[int] = None
    rsi_signal: Optional[int] = None
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AlertConfigResponse(AlertConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Market Data Schemas ============

class OHLCV(BaseModel):
    """Candle OHLCV"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class SymbolInfo(BaseModel):
    """Informações de um par de trading"""
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    last_signal: Optional[SignalResponse] = None


# ============ Dashboard Schemas ============

class DashboardStats(BaseModel):
    """Estatísticas do dashboard"""
    total_signals_today: int
    long_signals: int
    short_signals: int
    active_symbols: int
    last_update: datetime


class StrategyStatus(BaseModel):
    """Status de uma estratégia"""
    name: str
    enabled: bool
    signals_today: int
    last_signal: Optional[datetime] = None
