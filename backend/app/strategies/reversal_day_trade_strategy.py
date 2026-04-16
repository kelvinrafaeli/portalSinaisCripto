"""
Portal Sinais - Estratégia Reversão Day Trade
Confirmação entre RSI extremo e GCM no mesmo candle.
"""
from typing import Optional
import pandas as pd

from app.strategies.base import BaseStrategy, SignalResult
from app.strategies.gcm_strategy import GCMStrategy


class ReversalDayTradeStrategy(BaseStrategy):
    """
    Reversão Day Trade:
    - RSI cruza média a partir de zona extrema
    - GCM confirma na mesma direção
    """

    def __init__(self, **params):
        super().__init__(**params)
        self.rsi_period = params.get("rsi_period", 14)
        self.rsi_signal = params.get("rsi_signal", 9)
        self.rsi_overbought = params.get("rsi_overbought", 80)
        self.rsi_oversold = params.get("rsi_oversold", 20)

        self.gcm = GCMStrategy(
            harsi_length=params.get("harsi_length", 10),
            harsi_smooth=params.get("harsi_smooth", 5),
            rsi_length=params.get("gcm_rsi_length", 7),
            rsi_mode=params.get("gcm_rsi_mode", True),
            rsi_buy_level=params.get("gcm_buy_level", -20.0),
            rsi_sell_level=params.get("gcm_sell_level", 20.0),
        )

        self.name = "REVERSAO_DAY_TRADE"

    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> Optional[SignalResult]:
        min_rows = max(self.rsi_period + self.rsi_signal + 5, 60)
        if not self.validate_dataframe(df, min_rows=min_rows):
            return None

        closes = df["close"]
        rsi = self.rsi_wilder(closes, self.rsi_period)
        rsi_signal = self.sma(rsi, self.rsi_signal)

        rsi_prev = rsi.iloc[-2]
        rsi_curr = rsi.iloc[-1]
        sig_prev = rsi_signal.iloc[-2]
        sig_curr = rsi_signal.iloc[-1]

        if pd.isna(rsi_prev) or pd.isna(rsi_curr) or pd.isna(sig_prev) or pd.isna(sig_curr):
            return None

        rsi_cross_up = rsi_prev < sig_prev and rsi_curr >= sig_curr
        rsi_cross_down = rsi_prev > sig_prev and rsi_curr <= sig_curr

        from_oversold = rsi_prev <= self.rsi_oversold
        from_overbought = rsi_prev >= self.rsi_overbought

        gcm_signal = self.gcm.analyze(df, symbol, timeframe)
        if not gcm_signal:
            return None

        direction = None
        if rsi_cross_up and from_oversold and gcm_signal.direction == "LONG":
            direction = "LONG"
        elif rsi_cross_down and from_overbought and gcm_signal.direction == "SHORT":
            direction = "SHORT"

        if not direction:
            return None

        return SignalResult(
            symbol=symbol,
            timeframe=timeframe,
            strategy=self.name,
            direction=direction,
            price=closes.iloc[-1],
            message="REVERSAO DAY TRADE: RSI extremo + confirmacao GCM",
            rsi=round(rsi_curr, 2),
            raw_data={
                "rsi": round(rsi_curr, 2),
                "rsi_signal": round(sig_curr, 2),
                "gcm_direction": gcm_signal.direction,
                "rsi_oversold": self.rsi_oversold,
                "rsi_overbought": self.rsi_overbought,
            },
        )
