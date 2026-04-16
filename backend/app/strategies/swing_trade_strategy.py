"""
Portal Sinais - Estratégia Swing Trade
Confluência de cruzamento RSI + MACD.
"""
from typing import Optional
import pandas as pd

from app.strategies.base import BaseStrategy, SignalResult


class SwingTradeStrategy(BaseStrategy):
    """
    Swing Trade:
    - LONG: MACD cruza para cima e RSI cruza para cima
    - SHORT: MACD cruza para baixo e RSI cruza para baixo
    """

    def __init__(self, **params):
        super().__init__(**params)
        self.macd_fast = params.get("macd_fast", 12)
        self.macd_slow = params.get("macd_slow", 26)
        self.macd_signal = params.get("macd_signal", 9)
        self.rsi_period = params.get("rsi_period", 14)
        self.rsi_signal = params.get("rsi_signal", 9)
        self.name = "SWING_TRADE"

    def _calculate_macd(self, closes: pd.Series) -> tuple:
        ema_fast = self.ema(closes, self.macd_fast)
        ema_slow = self.ema(closes, self.macd_slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, self.macd_signal)
        return macd_line, signal_line

    def analyze(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[SignalResult]:
        if not self.validate_dataframe(df, min_rows=80):
            return None

        closes = df["close"]
        macd_line, macd_signal = self._calculate_macd(closes)
        rsi = self.rsi_wilder(closes, self.rsi_period)
        rsi_signal = self.sma(rsi, self.rsi_signal)

        macd_prev = macd_line.iloc[-2]
        macd_curr = macd_line.iloc[-1]
        macd_sig_prev = macd_signal.iloc[-2]
        macd_sig_curr = macd_signal.iloc[-1]

        rsi_prev = rsi.iloc[-2]
        rsi_curr = rsi.iloc[-1]
        rsi_sig_prev = rsi_signal.iloc[-2]
        rsi_sig_curr = rsi_signal.iloc[-1]

        if (
            pd.isna(macd_prev)
            or pd.isna(macd_curr)
            or pd.isna(macd_sig_prev)
            or pd.isna(macd_sig_curr)
            or pd.isna(rsi_prev)
            or pd.isna(rsi_curr)
            or pd.isna(rsi_sig_prev)
            or pd.isna(rsi_sig_curr)
        ):
            return None

        macd_cross_up = macd_prev <= macd_sig_prev and macd_curr > macd_sig_curr
        macd_cross_down = macd_prev >= macd_sig_prev and macd_curr < macd_sig_curr
        rsi_cross_up = rsi_prev <= rsi_sig_prev and rsi_curr > rsi_sig_curr
        rsi_cross_down = rsi_prev >= rsi_sig_prev and rsi_curr < rsi_sig_curr

        if macd_cross_up and rsi_cross_up:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="LONG",
                price=closes.iloc[-1],
                message="SWING TRADE LONG: cruzamento RSI + MACD",
                rsi=rsi_curr,
                macd=macd_curr,
                macd_signal=macd_sig_curr,
            )

        if macd_cross_down and rsi_cross_down:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="SHORT",
                price=closes.iloc[-1],
                message="SWING TRADE SHORT: cruzamento RSI + MACD",
                rsi=rsi_curr,
                macd=macd_curr,
                macd_signal=macd_sig_curr,
            )

        return None
