"""
Portal Sinais - Configurações Centralizadas
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache
import json


class Settings(BaseSettings):
    """Configurações carregadas do .env ou variáveis de ambiente"""
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/portal_sinais"
    redis_url: str = "redis://localhost:6379/0"
    
    # Exchange
    binance_api_key: str = ""
    binance_secret: str = ""
    
    # Strategy Settings (como JSON strings no .env)
    active_strategies: str = '["DAY_TRADE", "REVERSAO_DAY_TRADE", "SWING_TRADE", "SCALPING", "BTC_PRO", "DAY_TRADE_PRO"]'
    timeframes: str = '["3m", "15m", "1h", "1d"]'
    symbols: str = '["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT", "TRXUSDT", "LINKUSDT", "AVAXUSDT", "SUIUSDT", "SHIBUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT", "HBARUSDT", "XLMUSDT", "UNIUSDT", "NEARUSDT", "APTUSDT", "PEPEUSDT", "ICPUSDT", "ETCUSDT", "FILUSDT", "ATOMUSDT", "OPUSDT", "ARBUSDT", "INJUSDT", "VETUSDT", "RENDERUSDT"]'
    
    # RSI
    rsi_period: int = 14
    rsi_signal: int = 9
    rsi_overbought: int = 85
    rsi_oversold: int = 15
    
    # MACD
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    # GCM
    harsi_len: int = 10
    harsi_smooth: int = 5
    
    confirm_window: int = 6
    
    # Scalping
    scalping_ema_fast: int = 9
    scalping_ema_slow: int = 50
    
    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_enabled: bool = True
    telegram_include_disclaimer: bool = True
    
    # Worker
    chunk_size: int = 200
    worker_interval_seconds: int = 60
    
    # CryptoBubbles
    use_cryptobubbles: bool = False  # Usar lista fixa de symbols por padrao
    cryptobubbles_top_limit: int = 100  # Quantidade de pares com maior variação
    cryptobubbles_exclude_stablecoins: bool = True
    cryptobubbles_min_volume: float = 0  # Volume mínimo em USD
    
    @property
    def strategies_list(self) -> List[str]:
        return json.loads(self.active_strategies)
    
    @property
    def timeframes_list(self) -> List[str]:
        return json.loads(self.timeframes)
    
    @property
    def symbols_list(self) -> List[str]:
        return json.loads(self.symbols)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Retorna settings cacheado"""
    return Settings()
