"""
Portal Sinais - Estratégia Swing Trade
Baseada em GCM com filtros adicionais para operações mais longas.
Ideal para timeframes de 1h e 4h.
"""
from typing import Optional
import pandas as pd
import numpy as np

from app.strategies.base import BaseStrategy, SignalResult


class SwingTradeStrategy(BaseStrategy):
    """
    Estratégia de Swing Trade baseada em:
    - GCM Heikin Ashi RSI Trend Cloud
    - Análise de tendência de longo prazo
    - Ideal para operações de dias/semanas
    
    Usa Heikin Ashi RSI para identificar mudanças de tendência
    mais significativas.
    """
    
    def __init__(self, **params):
        super().__init__(**params)
        self.harsi_len = params.get("harsi_len", 14)  # Maior para swing
        self.harsi_smooth = params.get("harsi_smooth", 7)  # Maior suavização
        self.ema_filter = params.get("ema_filter", 100)  # EMA 100 como filtro
        self.name = "SWING_TRADE"
    
    def _heikin_ashi_rsi(
        self, 
        closes: pd.Series, 
        length: int, 
        smooth: int
    ) -> pd.Series:
        """
        Calcula Heikin Ashi RSI.
        """
        rsi = self.rsi_wilder(closes, length)
        
        # Suavização com EMA
        smoothed_rsi = self.ema(rsi, smooth)
        
        # Normalizar para comportamento Heikin Ashi
        ha_rsi = pd.Series(index=closes.index, dtype=float)
        
        for i in range(len(closes)):
            if i == 0 or pd.isna(smoothed_rsi.iloc[i]):
                ha_rsi.iloc[i] = smoothed_rsi.iloc[i] if not pd.isna(smoothed_rsi.iloc[i]) else 50
            else:
                prev = ha_rsi.iloc[i-1] if not pd.isna(ha_rsi.iloc[i-1]) else 50
                curr = smoothed_rsi.iloc[i]
                ha_rsi.iloc[i] = (prev + curr) / 2
        
        return ha_rsi
    
    def analyze(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> Optional[SignalResult]:
        """
        Analisa tendência para Swing Trade.
        """
        if not self.validate_dataframe(df, min_rows=120):
            return None
        
        closes = df['close']
        
        # Calcular indicadores
        ha_rsi = self._heikin_ashi_rsi(closes, self.harsi_len, self.harsi_smooth)
        ema_filter = self.ema(closes, self.ema_filter)
        
        # Valores atuais
        current_ha_rsi = ha_rsi.iloc[-1]
        prev_ha_rsi = ha_rsi.iloc[-2]
        current_ema = ema_filter.iloc[-1]
        current_price = closes.iloc[-1]
        
        if pd.isna(current_ha_rsi) or pd.isna(current_ema):
            return None
        
        # Detectar mudança de tendência
        # Linha de 50 como divisor
        cross_up = prev_ha_rsi <= 50 and current_ha_rsi > 50
        cross_down = prev_ha_rsi >= 50 and current_ha_rsi < 50
        
        # Filtro de tendência com EMA
        price_above_ema = current_price > current_ema
        price_below_ema = current_price < current_ema
        
        if cross_up and price_above_ema:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="LONG",
                price=current_price,
                message=f"🟢 SWING TRADE LONG: HA-RSI cruzou 50, preço acima EMA{self.ema_filter}",
                rsi=current_ha_rsi,
                ema50=current_ema
            )
        
        if cross_down and price_below_ema:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy=self.name,
                direction="SHORT",
                price=current_price,
                message=f"🔴 SWING TRADE SHORT: HA-RSI cruzou 50, preço abaixo EMA{self.ema_filter}",
                rsi=current_ha_rsi,
                ema50=current_ema
            )
        
        return None
