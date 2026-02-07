"""
Portal Sinais - Estratégia RSI
Detecta cruzamentos de RSI com a média de sinal.
"""
from typing import Optional
import pandas as pd
from .base import BaseStrategy, SignalResult


class RSIStrategy(BaseStrategy):
    """
    Estratégia baseada em RSI com cruzamento de média de sinal.
    
    Sinais:
    - LONG: RSI cruza acima da média de sinal + preço > EMA50
    - SHORT: RSI cruza abaixo da média de sinal + preço < EMA50
    """
    
    def __init__(
        self,
        period: int = 14,
        signal_period: int = 9,
        overbought: int = 70,
        oversold: int = 30,
        use_ema_filter: bool = True
    ):
        super().__init__(
            period=period,
            signal_period=signal_period,
            overbought=overbought,
            oversold=oversold,
            use_ema_filter=use_ema_filter
        )
        self.period = period
        self.signal_period = signal_period
        self.overbought = overbought
        self.oversold = oversold
        self.use_ema_filter = use_ema_filter
    
    def analyze(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> Optional[SignalResult]:
        """Analisa RSI e retorna sinal se houver cruzamento"""
        
        if not self.validate_dataframe(df, min_rows=self.period + self.signal_period + 5):
            return None
        
        # Calcular RSI
        rsi = self.rsi_wilder(df['close'], self.period)
        
        # Calcular média de sinal do RSI
        rsi_signal = self.sma(rsi, self.signal_period)
        
        # Calcular EMA50 para filtro
        ema50 = self.ema(df['close'], 50)
        
        # Valores atuais e anteriores
        rsi_curr = rsi.iloc[-1]
        rsi_prev = rsi.iloc[-2]
        sig_curr = rsi_signal.iloc[-1]
        sig_prev = rsi_signal.iloc[-2]
        last_close = df['close'].iloc[-1]
        last_ema50 = ema50.iloc[-1]
        
        # Verificar valores válidos
        if pd.isna(rsi_curr) or pd.isna(sig_curr) or pd.isna(rsi_prev) or pd.isna(sig_prev):
            return None
        
        # Detectar cruzamentos
        cross_up = rsi_prev < sig_prev and rsi_curr >= sig_curr
        cross_down = rsi_prev > sig_prev and rsi_curr <= sig_curr
        
        direction = None
        message = ""
        
        # LONG: RSI cruzou pra cima E estava/está na zona de sobrevenda (abaixo do oversold)
        if cross_up:
            # Verificar se RSI saiu da zona de sobrevenda (estava abaixo ou perto do oversold)
            if rsi_prev <= self.oversold or rsi_curr <= self.oversold + 5:
                # Filtro EMA50 para LONG
                if not self.use_ema_filter or last_close > last_ema50:
                    direction = "LONG"
                    message = (
                        f"🟢 RSI CROSS UP (saindo de sobrevenda)\n"
                        f"Símbolo: {symbol}\n"
                        f"Timeframe: {timeframe}\n"
                        f"RSI({self.period}): {rsi_curr:.2f}\n"
                        f"Média({self.signal_period}): {sig_curr:.2f}\n"
                        f"Nível oversold: {self.oversold}\n"
                        f"Preço > EMA50 ✓" if self.use_ema_filter else ""
                    )
        
        # SHORT: RSI cruzou pra baixo E estava/está na zona de sobrecompra (acima do overbought)
        elif cross_down:
            # Verificar se RSI saiu da zona de sobrecompra (estava acima ou perto do overbought)
            if rsi_prev >= self.overbought or rsi_curr >= self.overbought - 5:
                # Filtro EMA50 para SHORT
                if not self.use_ema_filter or last_close < last_ema50:
                    direction = "SHORT"
                    message = (
                        f"🔴 RSI CROSS DOWN (saindo de sobrecompra)\n"
                        f"Símbolo: {symbol}\n"
                        f"Timeframe: {timeframe}\n"
                        f"RSI({self.period}): {rsi_curr:.2f}\n"
                        f"Média({self.signal_period}): {sig_curr:.2f}\n"
                        f"Nível overbought: {self.overbought}\n"
                        f"Preço < EMA50 ✓" if self.use_ema_filter else ""
                    )
        
        if direction:
            return SignalResult(
                symbol=symbol,
                timeframe=timeframe,
                strategy="RSI",
                direction=direction,
                price=last_close,
                message=message,
                rsi=round(rsi_curr, 2),
                ema50=round(last_ema50, 2) if not pd.isna(last_ema50) else None,
                raw_data={
                    "rsi": round(rsi_curr, 2),
                    "rsi_signal": round(sig_curr, 2),
                    "ema50": round(last_ema50, 2) if not pd.isna(last_ema50) else None,
                    "cross_up": cross_up,
                    "cross_down": cross_down
                }
            )
        
        return None
