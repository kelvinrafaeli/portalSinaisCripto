"""
Portal Sinais - Exchange Service
Conecta em exchanges usando ccxt para buscar dados de mercado.
"""
import ccxt
import ccxt.async_support as ccxt_async
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ExchangeService:
    """
    Serviço para conectar em exchanges e buscar dados de mercado.
    Suporta Binance, Bybit, OKX usando ccxt.
    """
    
    TIMEFRAME_MAPPING = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1w": "1w"
    }
    
    def __init__(self, exchange_id: str = "binance"):
        self.settings = get_settings()
        self.exchange_id = exchange_id
        self._sync_exchange = None
        self._async_exchange = None
    
    def _get_sync_exchange(self) -> ccxt.Exchange:
        """Retorna instância síncrona da exchange"""
        if self._sync_exchange is None:
            exchange_class = getattr(ccxt, self.exchange_id)
            self._sync_exchange = exchange_class({
                'apiKey': self.settings.binance_api_key,
                'secret': self.settings.binance_secret,
                'sandbox': False,
                'options': {
                    'defaultType': 'spot'
                }
            })
        return self._sync_exchange
    
    async def _get_async_exchange(self) -> ccxt_async.Exchange:
        """Retorna instância assíncrona da exchange"""
        if self._async_exchange is None:
            exchange_class = getattr(ccxt_async, self.exchange_id)
            self._async_exchange = exchange_class({
                'apiKey': self.settings.binance_api_key,
                'secret': self.settings.binance_secret,
                'sandbox': False,
                'options': {
                    'defaultType': 'spot'
                }
            })
        return self._async_exchange
    
    async def close(self):
        """Fecha conexões da exchange"""
        if self._async_exchange:
            await self._async_exchange.close()
            self._async_exchange = None
    
    async def fetch_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = "1h",
        limit: int = 200
    ) -> pd.DataFrame:
        """
        Busca candles OHLCV de um símbolo.
        
        Args:
            symbol: Par de trading (ex: BTC/USDT ou BTCUSDT)
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Número máximo de candles
            
        Returns:
            DataFrame com colunas [timestamp, open, high, low, close, volume]
        """
        # Converter formato do símbolo se necessário
        if "/" not in symbol:
            # BTCUSDT -> BTC/USDT
            symbol = self._convert_symbol(symbol)
        
        try:
            exchange = await self._get_async_exchange()
            tf = self.TIMEFRAME_MAPPING.get(timeframe, timeframe)
            
            ohlcv = await exchange.fetch_ohlcv(symbol, tf, limit=limit)
            
            if not ohlcv:
                logger.warning(f"No data returned for {symbol} {timeframe}")
                return pd.DataFrame()
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('timestamp')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()
    
    async def fetch_multiple_ohlcv(
        self, 
        symbols: List[str], 
        timeframe: str = "1h",
        limit: int = 200
    ) -> Dict[str, pd.DataFrame]:
        """
        Busca candles para múltiplos símbolos de forma assíncrona.
        
        Returns:
            Dict com {symbol: DataFrame}
        """
        results = {}
        
        # Limitar concorrência para evitar rate limits
        semaphore = asyncio.Semaphore(5)
        
        async def fetch_with_semaphore(sym: str):
            async with semaphore:
                df = await self.fetch_ohlcv(sym, timeframe, limit)
                # Atraso pequeno entre requisições
                await asyncio.sleep(0.1)
                return sym, df
        
        tasks = [fetch_with_semaphore(s) for s in symbols]
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed:
            if isinstance(result, Exception):
                logger.error(f"Error in batch fetch: {result}")
                continue
            symbol, df = result
            if not df.empty:
                results[symbol] = df
        
        return results
    
    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Busca ticker atual de um símbolo.
        
        Returns:
            Dict com last, high, low, volume, change, etc.
        """
        if "/" not in symbol:
            symbol = self._convert_symbol(symbol)
        
        try:
            exchange = await self._get_async_exchange()
            ticker = await exchange.fetch_ticker(symbol)
            
            return {
                "symbol": symbol,
                "last": ticker.get("last"),
                "high": ticker.get("high"),
                "low": ticker.get("low"),
                "volume": ticker.get("quoteVolume"),
                "change": ticker.get("percentage"),
                "bid": ticker.get("bid"),
                "ask": ticker.get("ask"),
                "timestamp": ticker.get("timestamp")
            }
            
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    async def fetch_multiple_tickers(
        self, 
        symbols: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Busca tickers para múltiplos símbolos.
        """
        results = {}
        
        try:
            exchange = await self._get_async_exchange()
            
            # Converter símbolos
            converted = [self._convert_symbol(s) if "/" not in s else s for s in symbols]
            
            tickers = await exchange.fetch_tickers(converted)
            
            for symbol, ticker in tickers.items():
                results[symbol] = {
                    "symbol": symbol,
                    "last": ticker.get("last"),
                    "high": ticker.get("high"),
                    "low": ticker.get("low"),
                    "volume": ticker.get("quoteVolume"),
                    "change": ticker.get("percentage"),
                    "timestamp": ticker.get("timestamp")
                }
                
        except Exception as e:
            logger.error(f"Error fetching multiple tickers: {e}")
        
        return results
    
    def _convert_symbol(self, symbol: str) -> str:
        """
        Converte BTCUSDT para BTC/USDT.
        """
        # Remover sufixos comuns
        base_quotes = [
            ("USDT", "/USDT"),
            ("BUSD", "/BUSD"),
            ("USDC", "/USDC"),
            ("BTC", "/BTC"),
            ("ETH", "/ETH"),
        ]
        
        for suffix, replacement in base_quotes:
            if symbol.endswith(suffix):
                base = symbol[:-len(suffix)]
                return f"{base}{replacement}"
        
        return symbol
    
    async def get_all_symbols(self, quote: str = "USDT") -> List[str]:
        """
        Retorna todos os pares de trading com a quote especificada.
        """
        try:
            exchange = await self._get_async_exchange()
            await exchange.load_markets()
            
            symbols = [
                s for s in exchange.symbols 
                if s.endswith(f"/{quote}")
            ]
            
            return sorted(symbols)
            
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            return []


# Instância global
exchange_service = ExchangeService("binance")
