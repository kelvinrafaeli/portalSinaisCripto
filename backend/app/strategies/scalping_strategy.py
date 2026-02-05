"""
Portal Sinais - Estratégia de Scalping
EMA 50 + EMA 9 Crossover com confirmação RSI (acima/abaixo de 50)
Ideal para timeframe de 3m
"""
from typing import Optional
import pandas as pd
import numpy as np

from app.strategies.base import BaseStrategy, SignalResult


class ScalpingStrategy(BaseStrategy):
    """
    Estratégia de Scalping baseada em:
    - Cruzamento EMA 9 com EMA 50
    - Confirmação RSI acima/abaixo de 50
    
    LONG: EMA9 cruza acima da EMA50 + RSI > 50
    SHORT: EMA9 cruza abaixo da EMA50 + RSI < 50
    """
    
    def __init__(self, **params):
        super().__init__(**params)
        self.ema_fast = params.get("ema_fast", 9)
        self.ema_slow = params.get("ema_slow", 50)
        self.rsi_period = params.get("rsi_period", 14)
        self.rsi_neutral = params.get("rsi_neutral", 50)
        self.name = "SCALPING"
    
    def analyze(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> Optional[SignalResult]:
        """
        Analisa cruzamento EMA 9/50 com confirmação RSI.
        """
        if not self.validate_dataframe(df, min_rows=60):
            return None
        
        closes = df['close']
        
        # Calcular EMAs
        ema_fast = self.ema(closes, self.ema_fast)
        ema_slow = self.ema(closes, self.ema_slow)
        
        # Calcular RSI
        rsi = self.rsi_wilder(closes, self.rsi_period)
        
        # Valores atuais e anteriores
        current_ema_fast = ema_fast.iloc[-1]
        current_ema_slow = ema_slow.iloc[-1]
        prev_ema_fast = ema_fast.iloc[-2]
        prev_ema_slow = ema_slow.iloc[-2]
        current_rsi = rsi.iloc[-1]
        current_price = closes.iloc[-1]
        
        if pd.isna(current_rsi) or pd.isna(current_ema_fast) or pd.isna(current_ema_slow):
            return None
        
        # Detectar cruzamento
        cross_up = prev_ema_fast <= prev_ema_slow and current_ema_fast > current_ema_slow
        cross_down = prev_ema_fast >= prev_ema_slow and current_ema_fast < current_ema_slow
        
        # Confirmar com RSI
        rsi_bullish = current_rsi > self.rsi_neutral
        rsi_bearish = current_rsi < self.rsi_neutral
        
        if cross_up and rsi_bullish:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="LONG",
                price=current_price,
                message=f"🟢 SCALPING LONG: EMA{self.ema_fast} cruzou acima EMA{self.ema_slow}, RSI={current_rsi:.1f} (>{self.rsi_neutral})",
                rsi=current_rsi,
                ema50=current_ema_slow
            )
        
        if cross_down and rsi_bearish:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="SHORT",
                price=current_price,
                message=f"🔴 SCALPING SHORT: EMA{self.ema_fast} cruzou abaixo EMA{self.ema_slow}, RSI={current_rsi:.1f} (<{self.rsi_neutral})",
                rsi=current_rsi,
                ema50=current_ema_slow
            )
        
        return None
