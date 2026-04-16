"""
Portal Sinais - Estratégia Day Trade PRO
GCM em extremos para top 20 moedas.
"""
from typing import Optional
import pandas as pd

from app.strategies.base import BaseStrategy, SignalResult
from app.strategies.gcm_strategy import GCMStrategy


class DayTradeProStrategy(BaseStrategy):
    """
    Day Trade PRO:
    - Mesma leitura de extremos do GCM
    - Escopo de símbolos é aplicado no engine (top 20)
    """

    def __init__(self, **params):
        super().__init__(**params)
        self.gcm = GCMStrategy(
            harsi_length=params.get("harsi_length", 10),
            harsi_smooth=params.get("harsi_smooth", 5),
            rsi_length=params.get("rsi_length", 7),
            rsi_mode=params.get("rsi_mode", True),
            rsi_buy_level=params.get("rsi_buy_level", -25.0),
            rsi_sell_level=params.get("rsi_sell_level", 25.0),
        )
        self.name = "DAY_TRADE_PRO"

    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> Optional[SignalResult]:
        gcm_signal = self.gcm.analyze(df, symbol, timeframe)
        if not gcm_signal:
            return None

        return SignalResult(
            symbol=symbol,
            timeframe=timeframe,
            strategy=self.name,
            direction=gcm_signal.direction,
            price=gcm_signal.price,
            message="DAY TRADE PRO: GCM em zona extrema",
            rsi=gcm_signal.rsi,
            ema50=gcm_signal.ema50,
            raw_data=gcm_signal.raw_data,
        )
