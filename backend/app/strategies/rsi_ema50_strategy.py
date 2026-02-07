"""
Portal Sinais - Estratégia RSI + EMA50
RSI com filtro de EMA 50 para confirmar tendência.
"""
from typing import Optional
import pandas as pd
import numpy as np

from app.strategies.base import BaseStrategy, SignalResult


class RsiEma50Strategy(BaseStrategy):
    """
    Estratégia RSI + EMA50:
    - RSI cruza sua média de sinal
    - Preço deve estar na direção correta em relação à EMA50
    
    LONG: RSI cruza média para cima + preço acima EMA50
    SHORT: RSI cruza média para baixo + preço abaixo EMA50
    """
    
    def __init__(self, **params):
        super().__init__(**params)
        self.rsi_period = params.get("rsi_period", 14)
        self.rsi_signal = params.get("rsi_signal", 9)
        self.ema_period = params.get("ema_period", 50)
        self.rsi_overbought = params.get("rsi_overbought", 80)
        self.rsi_oversold = params.get("rsi_oversold", 20)
        self.name = "RSI_EMA50"
    
    def analyze(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> Optional[SignalResult]:
        """
        Analisa cruzamento RSI com filtro EMA50.
        """
        if not self.validate_dataframe(df, min_rows=60):
            return None
        
        closes = df['close']
        
        # Calcular indicadores
        rsi = self.rsi_wilder(closes, self.rsi_period)
        rsi_ma = self.sma(rsi, self.rsi_signal)
        ema50 = self.ema(closes, self.ema_period)
        
        # Valores atuais e anteriores
        current_rsi = rsi.iloc[-1]
        current_rsi_ma = rsi_ma.iloc[-1]
        prev_rsi = rsi.iloc[-2]
        prev_rsi_ma = rsi_ma.iloc[-2]
        current_ema50 = ema50.iloc[-1]
        current_price = closes.iloc[-1]
        
        if pd.isna(current_rsi) or pd.isna(current_rsi_ma) or pd.isna(current_ema50):
            return None
        
        # Detectar cruzamento RSI
        cross_up = prev_rsi <= prev_rsi_ma and current_rsi > current_rsi_ma
        cross_down = prev_rsi >= prev_rsi_ma and current_rsi < current_rsi_ma
        
        # Filtro EMA50
        price_above_ema = current_price > current_ema50
        price_below_ema = current_price < current_ema50

        rsi_state = None
        if current_rsi >= self.rsi_overbought:
            rsi_state = "overbought"
        elif current_rsi <= self.rsi_oversold:
            rsi_state = "oversold"
        
        if cross_up and price_above_ema and rsi_state == "oversold":
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="LONG",
                price=current_price,
                message=(
                    f"🟢 RSI+EMA50 LONG: RSI cruzou média, preço acima EMA{self.ema_period}"
                    f" | RSI {current_rsi:.2f} (min {self.rsi_oversold} / max {self.rsi_overbought})"
                ),
                rsi=current_rsi,
                ema50=current_ema50,
                raw_data={
                    "rsi": round(float(current_rsi), 2),
                    "rsi_signal": round(float(current_rsi_ma), 2),
                    "ema50": round(float(current_ema50), 6),
                    "rsi_overbought": self.rsi_overbought,
                    "rsi_oversold": self.rsi_oversold,
                    "rsi_state": rsi_state,
                    "cross_up": cross_up,
                    "cross_down": cross_down
                }
            )
        
        if cross_down and price_below_ema and rsi_state == "overbought":
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="SHORT",
                price=current_price,
                message=(
                    f"🔴 RSI+EMA50 SHORT: RSI cruzou média, preço abaixo EMA{self.ema_period}"
                    f" | RSI {current_rsi:.2f} (min {self.rsi_oversold} / max {self.rsi_overbought})"
                ),
                rsi=current_rsi,
                ema50=current_ema50,
                raw_data={
                    "rsi": round(float(current_rsi), 2),
                    "rsi_signal": round(float(current_rsi_ma), 2),
                    "ema50": round(float(current_ema50), 6),
                    "rsi_overbought": self.rsi_overbought,
                    "rsi_oversold": self.rsi_oversold,
                    "rsi_state": rsi_state,
                    "cross_up": cross_up,
                    "cross_down": cross_down
                }
            )
        
        return None
