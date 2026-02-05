"""
Portal Sinais - Estratégia Day Trade
MACD + RSI - quando ambos cruzam na mesma direção
Ideal para timeframes de 15m e 1h.
"""
from typing import Optional
import pandas as pd
import numpy as np

from app.strategies.base import BaseStrategy, SignalResult


class DayTradeStrategy(BaseStrategy):
    """
    Estratégia de Day Trade baseada em:
    - Cruzamento MACD na mesma direção
    - Cruzamento RSI na mesma direção
    - Ambos devem confirmar dentro de uma janela de candles
    
    LONG: MACD cruza bullish + RSI cruza média para cima
    SHORT: MACD cruza bearish + RSI cruza média para baixo
    """
    
    def __init__(self, **params):
        super().__init__(**params)
        # MACD
        self.macd_fast = params.get("macd_fast", 12)
        self.macd_slow = params.get("macd_slow", 26)
        self.macd_signal = params.get("macd_signal", 9)
        
        # RSI
        self.rsi_period = params.get("rsi_period", 14)
        self.rsi_ma_period = params.get("rsi_ma_period", 9)
        
        # Janela de confirmação
        self.confirm_window = params.get("confirm_window", 6)
        
        self.name = "DAY_TRADE"
    
    def _calculate_macd(
        self, 
        closes: pd.Series
    ) -> tuple:
        """Calcula MACD Line, Signal e Histogram"""
        ema_fast = self.ema(closes, self.macd_fast)
        ema_slow = self.ema(closes, self.macd_slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, self.macd_signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def _find_recent_cross(
        self, 
        series_a: pd.Series, 
        series_b: pd.Series, 
        direction: str, 
        window: int
    ) -> bool:
        """
        Verifica se houve cruzamento recente dentro da janela.
        direction: 'up' ou 'down'
        """
        for i in range(1, min(window + 1, len(series_a))):
            idx = -i
            prev_idx = idx - 1
            
            if abs(prev_idx) >= len(series_a):
                break
            
            curr_a = series_a.iloc[idx]
            curr_b = series_b.iloc[idx]
            prev_a = series_a.iloc[prev_idx]
            prev_b = series_b.iloc[prev_idx]
            
            if pd.isna(curr_a) or pd.isna(curr_b) or pd.isna(prev_a) or pd.isna(prev_b):
                continue
            
            if direction == 'up':
                if prev_a <= prev_b and curr_a > curr_b:
                    return True
            else:  # down
                if prev_a >= prev_b and curr_a < curr_b:
                    return True
        
        return False
    
    def analyze(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> Optional[SignalResult]:
        """
        Analisa confluência MACD + RSI para Day Trade.
        """
        if not self.validate_dataframe(df, min_rows=50):
            return None
        
        closes = df['close']
        
        # Calcular indicadores
        macd_line, signal_line, histogram = self._calculate_macd(closes)
        rsi = self.rsi_wilder(closes, self.rsi_period)
        rsi_ma = self.sma(rsi, self.rsi_ma_period)
        
        current_price = closes.iloc[-1]
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_rsi = rsi.iloc[-1]
        
        if pd.isna(current_rsi) or pd.isna(current_macd):
            return None
        
        # Verificar cruzamentos recentes
        macd_cross_up = self._find_recent_cross(macd_line, signal_line, 'up', self.confirm_window)
        macd_cross_down = self._find_recent_cross(macd_line, signal_line, 'down', self.confirm_window)
        rsi_cross_up = self._find_recent_cross(rsi, rsi_ma, 'up', self.confirm_window)
        rsi_cross_down = self._find_recent_cross(rsi, rsi_ma, 'down', self.confirm_window)
        
        # LONG: Ambos cruzam para cima
        if macd_cross_up and rsi_cross_up:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="LONG",
                price=current_price,
                message=f"🟢 DAY TRADE LONG: MACD + RSI cruzaram na mesma direção",
                rsi=current_rsi,
                macd=current_macd,
                macd_signal=current_signal
            )
        
        # SHORT: Ambos cruzam para baixo
        if macd_cross_down and rsi_cross_down:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="SHORT",
                price=current_price,
                message=f"🔴 DAY TRADE SHORT: MACD + RSI cruzaram na mesma direção",
                rsi=current_rsi,
                macd=current_macd,
                macd_signal=current_signal
            )
        
        return None
