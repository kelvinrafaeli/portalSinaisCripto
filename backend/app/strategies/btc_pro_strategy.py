"""
Portal Sinais - Estratégia BTC PRO
RSI crossover exclusivo para BTC.
"""
from typing import Optional
import pandas as pd

from app.strategies.base import BaseStrategy, SignalResult
from app.strategies.rsi_strategy import RSIStrategy


class BTCProStrategy(BaseStrategy):
    """
    BTC PRO:
    - Aplica RSI crossover apenas em BTCUSDT
    - Focado em sinais para alavancagem
    """

    def __init__(self, **params):
        super().__init__(**params)
        self.rsi = RSIStrategy(
            period=params.get("period", 14),
            signal_period=params.get("signal_period", 9),
            overbought=params.get("overbought", 80),
            oversold=params.get("oversold", 20),
            use_ema_filter=params.get("use_ema_filter", False),
        )
        self.name = "BTC_PRO"

    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> Optional[SignalResult]:
        if symbol.upper() != "BTCUSDT":
            return None

        base_signal = self.rsi.analyze(df, symbol, timeframe)
        if not base_signal:
            return None

        return SignalResult(
            symbol=symbol,
            timeframe=timeframe,
            strategy=self.name,
            direction=base_signal.direction,
            price=base_signal.price,
            message="BTC PRO: cruzamento de linhas RSI no BTC",
            rsi=base_signal.rsi,
            ema50=base_signal.ema50,
            raw_data=base_signal.raw_data,
        )
