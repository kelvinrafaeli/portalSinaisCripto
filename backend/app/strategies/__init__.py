"""Portal Sinais - Strategies Module"""
from .base import BaseStrategy, SignalResult
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .gcm_strategy import GCMStrategy
from .combo_strategy import ComboStrategy
from .scalping_strategy import ScalpingStrategy
from .swing_trade_strategy import SwingTradeStrategy
from .day_trade_strategy import DayTradeStrategy
from .rsi_ema50_strategy import RsiEma50Strategy

__all__ = [
    "BaseStrategy", "SignalResult",
    "RSIStrategy", "MACDStrategy", "GCMStrategy", "ComboStrategy",
    "ScalpingStrategy", "SwingTradeStrategy", "DayTradeStrategy", "RsiEma50Strategy"
]
