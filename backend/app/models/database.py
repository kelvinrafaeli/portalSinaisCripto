"""
Portal Sinais - Database Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class AlertConfig(Base):
    """Configuração de alertas persistida no banco"""
    __tablename__ = "alert_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    
    # Estratégias ativas
    use_rsi = Column(Boolean, default=True)
    use_macd = Column(Boolean, default=True)
    use_combo = Column(Boolean, default=True)
    use_gcm = Column(Boolean, default=True)
    
    # RSI Settings
    rsi_period = Column(Integer, default=14)
    rsi_signal = Column(Integer, default=9)
    rsi_overbought = Column(Integer, default=85)
    rsi_oversold = Column(Integer, default=15)
    
    # MACD Settings
    macd_fast = Column(Integer, default=12)
    macd_slow = Column(Integer, default=26)
    macd_signal = Column(Integer, default=9)
    
    # GCM Settings
    harsi_len = Column(Integer, default=10)
    harsi_smooth = Column(Integer, default=5)
    
    # COMBO Settings
    combo_require_ema50 = Column(Boolean, default=True)
    confirm_window = Column(Integer, default=6)
    
    # Símbolos e Timeframes (JSON array)
    symbols = Column(JSON, default=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    timeframes = Column(JSON, default=["1h", "4h"])
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Signal(Base):
    """Sinais gerados pelo sistema"""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    strategy = Column(String(20), nullable=False)  # GCM, COMBO, RSI, MACD
    direction = Column(String(10), nullable=False)  # LONG, SHORT
    
    # Valores do indicador no momento do sinal
    rsi_value = Column(Float, nullable=True)
    macd_value = Column(Float, nullable=True)
    macd_signal_value = Column(Float, nullable=True)
    ema50_value = Column(Float, nullable=True)
    price = Column(Float, nullable=False)
    
    message = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)


class WatchlistItem(Base):
    """Itens da watchlist do usuário"""
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
