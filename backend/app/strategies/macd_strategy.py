"""
Portal Sinais - Estratégia MACD
Detecta cruzamentos do MACD com a linha de sinal.
"""
from typing import Optional
import pandas as pd
from .base import BaseStrategy, SignalResult


class MACDStrategy(BaseStrategy):
    """
    Estratégia baseada em cruzamentos do MACD.
    
    Sinais:
    - LONG: MACD cruza acima da linha de sinal
    - SHORT: MACD cruza abaixo da linha de sinal
    """
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ):
        super().__init__(
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period
        )
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def calculate_macd(self, closes: pd.Series) -> tuple:
        """
        Calcula MACD, Linha de Sinal e Histograma.
        
        Returns:
            (macd_line, signal_line, histogram)
        """
        ema_fast = self.ema(closes, self.fast_period)
        ema_slow = self.ema(closes, self.slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, self.signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def analyze(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> Optional[SignalResult]:
        """Analisa MACD e retorna sinal se houver cruzamento"""
        
        if not self.validate_dataframe(df, min_rows=self.slow_period + self.signal_period + 5):
            return None
        
        # Calcular MACD
        macd_line, signal_line, histogram = self.calculate_macd(df['close'])
        
        # Valores atuais e anteriores
        macd_curr = macd_line.iloc[-1]
        macd_prev = macd_line.iloc[-2]
        sig_curr = signal_line.iloc[-1]
        sig_prev = signal_line.iloc[-2]
        hist_curr = histogram.iloc[-1]
        last_close = df['close'].iloc[-1]
        
        # Verificar valores válidos
        if pd.isna(macd_curr) or pd.isna(sig_curr) or pd.isna(macd_prev) or pd.isna(sig_prev):
            return None
        
        # Detectar cruzamentos
        cross_up = macd_prev < sig_prev and macd_curr >= sig_curr
        cross_down = macd_prev > sig_prev and macd_curr <= sig_curr
        
        direction = None
        message = ""
        
        if cross_up:
            direction = "LONG"
            message = (
                f"🟢 MACD CROSS UP\n"
                f"Símbolo: {symbol}\n"
                f"Timeframe: {timeframe}\n"
                f"MACD: {macd_curr:.6f}\n"
                f"Sinal({self.signal_period}): {sig_curr:.6f}\n"
                f"Histograma: {hist_curr:.6f}"
            )
        
        elif cross_down:
            direction = "SHORT"
            message = (
                f"🔴 MACD CROSS DOWN\n"
                f"Símbolo: {symbol}\n"
                f"Timeframe: {timeframe}\n"
                f"MACD: {macd_curr:.6f}\n"
                f"Sinal({self.signal_period}): {sig_curr:.6f}\n"
                f"Histograma: {hist_curr:.6f}"
            )
        
        if direction:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy="MACD",
                direction=direction,
                price=last_close,
                message=message,
                macd=round(macd_curr, 6),
                macd_signal=round(sig_curr, 6),
                raw_data={
                    "macd": round(macd_curr, 6),
                    "signal": round(sig_curr, 6),
                    "histogram": round(hist_curr, 6),
                    "cross_up": cross_up,
                    "cross_down": cross_down
                }
            )
        
        return None
