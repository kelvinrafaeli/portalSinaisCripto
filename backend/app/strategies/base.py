"""
Portal Sinais - Classe Base de Estratégia
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np


@dataclass
class SignalResult:
    """Resultado de um sinal gerado"""
    symbol: str
    timeframe: str
    strategy: str
    direction: str  # "LONG" ou "SHORT"
    price: float
    message: str
    
    # Valores opcionais dos indicadores
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    ema50: Optional[float] = None
    
    # Metadados
    timestamp: datetime = None
    raw_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "strategy": self.strategy,
            "direction": self.direction,
            "price": self.price,
            "message": self.message,
            "rsi": self.rsi,
            "macd": self.macd,
            "macd_signal": self.macd_signal,
            "ema50": self.ema50,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "raw_data": self.raw_data
        }


class BaseStrategy(ABC):
    """
    Classe base para todas as estratégias de trading.
    Cada estratégia deve implementar o método `analyze`.
    """
    
    def __init__(self, **params):
        self.params = params
        self.name = self.__class__.__name__
    
    @abstractmethod
    def analyze(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> Optional[SignalResult]:
        """
        Analisa o DataFrame de candles e retorna um sinal se houver.
        
        Args:
            df: DataFrame com colunas ['open', 'high', 'low', 'close', 'volume']
            symbol: Par de trading (ex: BTCUSDT)
            timeframe: Timeframe analisado (ex: 1h)
            
        Returns:
            SignalResult se houver sinal, None caso contrário
        """
        pass
    
    def validate_dataframe(self, df: pd.DataFrame, min_rows: int = 50) -> bool:
        """Valida se o DataFrame tem dados suficientes"""
        if df is None or df.empty:
            return False
        if len(df) < min_rows:
            return False
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        return all(col in df.columns for col in required_cols)
    
    @staticmethod
    def rsi_wilder(closes: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcula RSI usando o método de suavização de Wilder (igual ao TradingView).
        """
        delta = closes.diff()
        gains = delta.where(delta > 0, 0.0)
        losses = (-delta).where(delta < 0, 0.0)
        
        # Primeira média (SMA)
        first_avg_gain = gains.iloc[:period].mean()
        first_avg_loss = losses.iloc[:period].mean()
        
        avg_gain = pd.Series(index=closes.index, dtype=float)
        avg_loss = pd.Series(index=closes.index, dtype=float)
        
        avg_gain.iloc[period - 1] = first_avg_gain
        avg_loss.iloc[period - 1] = first_avg_loss
        
        # Suavização de Wilder
        for i in range(period, len(closes)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gains.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + losses.iloc[i]) / period
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        """Calcula EMA"""
        return series.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        """Calcula SMA"""
        return series.rolling(window=period).mean()
