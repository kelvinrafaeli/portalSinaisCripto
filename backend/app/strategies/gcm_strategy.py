"""
Portal Sinais - Estratégia GCM Heikin Ashi RSI Trend Cloud
Implementação do indicador GCM baseado em Heikin Ashi RSI.
"""
from typing import Optional
import pandas as pd
import numpy as np
from .base import BaseStrategy, SignalResult


class GCMStrategy(BaseStrategy):
    """
    GCM Heikin Ashi RSI Trend Cloud Strategy.
    
    Este indicador converte os preços em valores de RSI centralizados em zero
    e depois aplica a lógica de Heikin Ashi nesses valores.
    
    Sinais:
    - LONG (BULL START): HA-RSI muda de bearish para bullish
    - SHORT (BEAR START): HA-RSI muda de bullish para bearish
    """
    
    def __init__(
        self,
        harsi_length: int = 10,
        harsi_smooth: int = 5
    ):
        super().__init__(
            harsi_length=harsi_length,
            harsi_smooth=harsi_smooth
        )
        self.harsi_length = harsi_length
        self.harsi_smooth = harsi_smooth
    
    def _zrsi(self, series: pd.Series, period: int) -> pd.Series:
        """
        Calcula RSI centralizado em zero (RSI - 50).
        Baseado no f_zrsi do Pine Script original.
        """
        rsi = self.rsi_wilder(series, period)
        return rsi - 50
    
    def calculate_harsi(self, df: pd.DataFrame) -> tuple:
        """
        Calcula Heikin Ashi RSI.
        
        Returns:
            (ha_open, ha_high, ha_low, ha_close) como Series
        """
        n = len(df)
        
        # Calcular RSI centralizado para cada série OHLC
        rsi_open = self.rsi_wilder(df['open'], self.harsi_length)
        rsi_high = self.rsi_wilder(df['high'], self.harsi_length)
        rsi_low = self.rsi_wilder(df['low'], self.harsi_length)
        rsi_close = self.rsi_wilder(df['close'], self.harsi_length)
        
        # Centralizar em zero
        z_open = rsi_open - 50
        z_high = rsi_high - 50
        z_low = rsi_low - 50
        z_close = rsi_close - 50
        
        # Arrays para Heikin Ashi
        ha_close = pd.Series(index=df.index, dtype=float)
        ha_open = pd.Series(index=df.index, dtype=float)
        ha_high = pd.Series(index=df.index, dtype=float)
        ha_low = pd.Series(index=df.index, dtype=float)
        
        prev_ha_open_smoothed = None
        
        for i in range(n):
            if pd.isna(z_close.iloc[i]):
                ha_close.iloc[i] = np.nan
                ha_open.iloc[i] = np.nan
                ha_high.iloc[i] = np.nan
                ha_low.iloc[i] = np.nan
                continue
            
            # Pine: _openRSI = nz(_closeRSI[1], _closeRSI)
            # Usa o close RSI anterior como open RSI
            if i > 0 and not pd.isna(z_close.iloc[i-1]):
                open_rsi = z_close.iloc[i-1]
            else:
                open_rsi = z_close.iloc[i]
            
            # Pine: _highRSI = max(_highRSI_raw, _lowRSI_raw)
            #       _lowRSI  = min(_highRSI_raw, _lowRSI_raw)
            r_max = max(z_high.iloc[i], z_low.iloc[i])
            r_min = min(z_high.iloc[i], z_low.iloc[i])
            
            # Pine: _close = (_openRSI + _highRSI + _lowRSI + _closeRSI) / 4
            ha_close_val = (open_rsi + r_max + r_min + z_close.iloc[i]) / 4
            
            # Pine: _open := na(_open[i_smoothing]) ? (_openRSI + _closeRSI) / 2 
            #                : ((_open[1] * i_smoothing) + _close[1]) / (i_smoothing + 1)
            if prev_ha_open_smoothed is None:
                ha_open_val = (open_rsi + z_close.iloc[i]) / 2
            else:
                prev_ha_close = ha_close.iloc[i-1]
                if pd.isna(prev_ha_close):
                    ha_open_val = (open_rsi + z_close.iloc[i]) / 2
                else:
                    ha_open_val = ((prev_ha_open_smoothed * self.harsi_smooth) + prev_ha_close) / (self.harsi_smooth + 1)
            
            prev_ha_open_smoothed = ha_open_val
            
            # Pine: _high = max(_highRSI, max(_open, _close))
            #       _low  = min(_lowRSI, min(_open, _close))
            ha_high_val = max(r_max, max(ha_open_val, ha_close_val))
            ha_low_val = min(r_min, min(ha_open_val, ha_close_val))
            
            ha_close.iloc[i] = ha_close_val
            ha_open.iloc[i] = ha_open_val
            ha_high.iloc[i] = ha_high_val
            ha_low.iloc[i] = ha_low_val
        
        return ha_open, ha_high, ha_low, ha_close
    
    def analyze(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> Optional[SignalResult]:
        """Analisa GCM e retorna sinal se houver mudança de tendência"""
        
        min_rows = self.harsi_length + self.harsi_smooth + 10
        if not self.validate_dataframe(df, min_rows=min_rows):
            return None
        
        # Calcular Heikin Ashi RSI
        ha_open, ha_high, ha_low, ha_close = self.calculate_harsi(df)
        
        # Índices para análise
        curr_idx = len(df) - 1
        prev_idx = len(df) - 2
        
        ha_close_curr = ha_close.iloc[curr_idx]
        ha_open_curr = ha_open.iloc[curr_idx]
        ha_close_prev = ha_close.iloc[prev_idx]
        ha_open_prev = ha_open.iloc[prev_idx]
        
        # Verificar valores válidos
        if any(pd.isna([ha_close_curr, ha_open_curr, ha_close_prev, ha_open_prev])):
            return None
        
        # Determinar se candle é bullish (verde) ou bearish (vermelho)
        is_green_curr = ha_close_curr > ha_open_curr
        is_green_prev = ha_close_prev > ha_open_prev
        
        # Detectar mudanças de tendência
        # harsiBull = (C > O) and not (C[1] > O[1])  -> Virou de vermelho para verde
        # harsiBear = not(C > O) and (C[1] > O[1])   -> Virou de verde para vermelho
        harsi_bull = is_green_curr and not is_green_prev
        harsi_bear = not is_green_curr and is_green_prev
        
        last_close = df['close'].iloc[-1]
        direction = None
        message = ""
        
        if harsi_bull:
            direction = "LONG"
            message = (
                f"🚀 GCM TREND CLOUD: BULL START 🟢\n"
                f"Símbolo: {symbol}\n"
                f"Timeframe: {timeframe}\n"
                f"HA-RSI virou positivo\n"
                f"Cloud mudou de vermelho para verde"
            )
        
        elif harsi_bear:
            direction = "SHORT"
            message = (
                f"🔻 GCM TREND CLOUD: BEAR START 🔴\n"
                f"Símbolo: {symbol}\n"
                f"Timeframe: {timeframe}\n"
                f"HA-RSI virou negativo\n"
                f"Cloud mudou de verde para vermelho"
            )
        
        if direction:
            # Calcular EMA50 e RSI para contexto adicional
            ema50 = self.ema(df['close'], 50).iloc[-1]
            rsi = self.rsi_wilder(df['close'], 14).iloc[-1]
            
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy="GCM",
                direction=direction,
                price=last_close,
                message=message,
                rsi=round(rsi, 2) if not pd.isna(rsi) else None,
                ema50=round(ema50, 2) if not pd.isna(ema50) else None,
                raw_data={
                    "ha_close": round(ha_close_curr, 4),
                    "ha_open": round(ha_open_curr, 4),
                    "ha_high": round(ha_high.iloc[curr_idx], 4),
                    "ha_low": round(ha_low.iloc[curr_idx], 4),
                    "cloud_status": "BULLISH" if is_green_curr else "BEARISH",
                    "harsi_bull": harsi_bull,
                    "harsi_bear": harsi_bear
                }
            )
        
        return None
