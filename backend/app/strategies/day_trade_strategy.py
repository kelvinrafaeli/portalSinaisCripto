"""
Portal Sinais - Estratégia Day Trade
Baseada em cruzamento do preço com EMA50.
"""
from typing import Optional
import pandas as pd

from app.strategies.base import BaseStrategy, SignalResult


class DayTradeStrategy(BaseStrategy):
    """
    Estratégia Day Trade (EMA50):
    - LONG: preço cruza acima da EMA50
    - SHORT: preço cruza abaixo da EMA50
    """

    def __init__(self, **params):
        super().__init__(**params)
        self.ema_period = params.get("ema_period", 50)
        self.name = "DAY_TRADE"

    def analyze(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[SignalResult]:
        if not self.validate_dataframe(df, min_rows=self.ema_period + 5):
            return None

        closes = df["close"]
        ema = self.ema(closes, self.ema_period)

        prev_close = closes.iloc[-2]
        curr_close = closes.iloc[-1]
        prev_ema = ema.iloc[-2]
        curr_ema = ema.iloc[-1]

        if pd.isna(prev_ema) or pd.isna(curr_ema):
            return None

        cross_up = prev_close <= prev_ema and curr_close > curr_ema
        cross_down = prev_close >= prev_ema and curr_close < curr_ema

        if cross_up:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="LONG",
                price=curr_close,
                message=f"DAY TRADE LONG: preco cruzou acima da EMA{self.ema_period}",
                ema50=curr_ema,
                raw_data={"ema_period": self.ema_period}
            )

        if cross_down:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="SHORT",
                price=curr_close,
                message=f"DAY TRADE SHORT: preco cruzou abaixo da EMA{self.ema_period}",
                ema50=curr_ema,
                raw_data={"ema_period": self.ema_period}
            )

        return None
