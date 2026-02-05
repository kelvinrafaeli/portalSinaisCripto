"""
Portal Sinais - Estratégia COMBO (MACD + RSI)
Detecta confirmação de sinais quando MACD e RSI cruzam na mesma direção.
"""
from typing import Optional, Tuple
import pandas as pd
from .base import BaseStrategy, SignalResult
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy


class ComboStrategy(BaseStrategy):
    """
    Estratégia COMBO que combina MACD + RSI.
    
    Regras:
    - Se MACD cruzou nos últimos N candles e RSI acaba de cruzar (ou vice-versa)
    - Ambos na mesma direção
    - Filtro EMA50 opcional
    
    Sinais:
    - LONG: Ambos cruzando para cima + preço > EMA50
    - SHORT: Ambos cruzando para baixo + preço < EMA50
    """
    
    def __init__(
        self,
        rsi_period: int = 14,
        rsi_signal: int = 9,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        confirm_window: int = 6,
        require_ema50: bool = True,
        allow_mixed_dir: bool = False
    ):
        super().__init__(
            rsi_period=rsi_period,
            rsi_signal=rsi_signal,
            macd_fast=macd_fast,
            macd_slow=macd_slow,
            macd_signal=macd_signal,
            confirm_window=confirm_window,
            require_ema50=require_ema50,
            allow_mixed_dir=allow_mixed_dir
        )
        self.rsi_period = rsi_period
        self.rsi_signal = rsi_signal
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.confirm_window = confirm_window
        self.require_ema50 = require_ema50
        self.allow_mixed_dir = allow_mixed_dir
    
    def _detect_cross_at(
        self, 
        series: pd.Series, 
        signal_series: pd.Series, 
        idx: int
    ) -> Optional[str]:
        """
        Detecta se houve cruzamento no índice especificado.
        
        Returns:
            'UP', 'DOWN', ou None
        """
        if idx <= 0 or idx >= len(series):
            return None
        
        curr = series.iloc[idx]
        prev = series.iloc[idx - 1]
        sig_curr = signal_series.iloc[idx]
        sig_prev = signal_series.iloc[idx - 1]
        
        if pd.isna(curr) or pd.isna(prev) or pd.isna(sig_curr) or pd.isna(sig_prev):
            return None
        
        if prev < sig_prev and curr >= sig_curr:
            return 'UP'
        if prev > sig_prev and curr <= sig_curr:
            return 'DOWN'
        
        return None
    
    def _find_recent_cross(
        self, 
        series: pd.Series, 
        signal_series: pd.Series, 
        window: int
    ) -> Optional[Tuple[int, str]]:
        """
        Encontra o cruzamento mais recente dentro da janela.
        
        Returns:
            (índice, direção) ou None
        """
        n = len(series)
        start_idx = max(1, n - 1 - window)
        
        for i in range(start_idx, n):
            cross = self._detect_cross_at(series, signal_series, i)
            if cross:
                return (i, cross)
        
        return None
    
    def analyze(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> Optional[SignalResult]:
        """Analisa COMBO e retorna sinal se houver confirmação"""
        
        min_rows = max(self.macd_slow, self.rsi_period) + self.macd_signal + 20
        if not self.validate_dataframe(df, min_rows=min_rows):
            return None
        
        n = len(df)
        last_close = df['close'].iloc[-1]
        
        # Calcular RSI e média
        rsi = self.rsi_wilder(df['close'], self.rsi_period)
        rsi_sig = self.sma(rsi, self.rsi_signal)
        
        # Calcular MACD
        ema_fast = self.ema(df['close'], self.macd_fast)
        ema_slow = self.ema(df['close'], self.macd_slow)
        macd_line = ema_fast - ema_slow
        macd_sig = self.ema(macd_line, self.macd_signal)
        
        # Calcular EMA50
        ema50 = self.ema(df['close'], 50).iloc[-1]
        
        # Detectar cruzamento atual no RSI e MACD
        rsi_now = self._detect_cross_at(rsi, rsi_sig, n - 1)
        macd_now = self._detect_cross_at(macd_line, macd_sig, n - 1)
        
        # Buscar cruzamentos recentes na janela de confirmação
        rsi_recent = self._find_recent_cross(rsi, rsi_sig, self.confirm_window)
        macd_recent = self._find_recent_cross(macd_line, macd_sig, self.confirm_window)
        
        direction = None
        combo_type = ""
        
        # Caso 1: MACD cruzou antes, RSI cruza agora
        if macd_recent and rsi_now:
            macd_dir = macd_recent[1]
            if self.allow_mixed_dir or macd_dir == rsi_now:
                dir_check = rsi_now
                # Verificar EMA50
                ema_ok = not self.require_ema50 or (
                    (dir_check == 'UP' and last_close > ema50) or
                    (dir_check == 'DOWN' and last_close < ema50)
                )
                if ema_ok:
                    direction = "LONG" if dir_check == "UP" else "SHORT"
                    combo_type = "MACD_PAST_RSI_NOW"
        
        # Caso 2: RSI cruzou antes, MACD cruza agora
        elif rsi_recent and macd_now:
            rsi_dir = rsi_recent[1]
            if self.allow_mixed_dir or rsi_dir == macd_now:
                dir_check = macd_now
                ema_ok = not self.require_ema50 or (
                    (dir_check == 'UP' and last_close > ema50) or
                    (dir_check == 'DOWN' and last_close < ema50)
                )
                if ema_ok:
                    direction = "LONG" if dir_check == "UP" else "SHORT"
                    combo_type = "RSI_PAST_MACD_NOW"
        
        # Caso 3: Ambos cruzam agora
        elif rsi_now and macd_now:
            if self.allow_mixed_dir or rsi_now == macd_now:
                dir_check = rsi_now
                ema_ok = not self.require_ema50 or (
                    (dir_check == 'UP' and last_close > ema50) or
                    (dir_check == 'DOWN' and last_close < ema50)
                )
                if ema_ok:
                    direction = "LONG" if dir_check == "UP" else "SHORT"
                    combo_type = "BOTH_NOW"
        
        if direction:
            action = "LONG 🟢" if direction == "LONG" else "SHORT 🔴"
            
            message = (
                f"⚡ COMBO CONFIRMADO!\n"
                f"Tempo analisado: {timeframe}\n"
                f"MOEDA: {symbol.upper()}\n"
                f"AÇÃO: {action}\n"
                f"RSI + MACD confluência"
            )
            
            rsi_val = rsi.iloc[-1]
            macd_val = macd_line.iloc[-1]
            macd_sig_val = macd_sig.iloc[-1]
            
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy="COMBO",
                direction=direction,
                price=last_close,
                message=message,
                rsi=round(rsi_val, 2) if not pd.isna(rsi_val) else None,
                macd=round(macd_val, 6) if not pd.isna(macd_val) else None,
                macd_signal=round(macd_sig_val, 6) if not pd.isna(macd_sig_val) else None,
                ema50=round(ema50, 2) if not pd.isna(ema50) else None,
                raw_data={
                    "combo_type": combo_type,
                    "rsi": round(rsi_val, 2) if not pd.isna(rsi_val) else None,
                    "macd": round(macd_val, 6) if not pd.isna(macd_val) else None,
                    "macd_signal": round(macd_sig_val, 6) if not pd.isna(macd_sig_val) else None,
                    "ema50": round(ema50, 2) if not pd.isna(ema50) else None,
                    "confirm_window": self.confirm_window
                }
            )
        
        return None
