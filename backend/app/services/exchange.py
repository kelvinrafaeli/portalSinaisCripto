"""
Portal Sinais - Exchange Service
Conecta em exchanges usando ccxt para buscar dados de mercado.
Com fallback para requisições diretas via DNS alternativo para contornar problemas de DNS.
"""
import ccxt
import ccxt.async_support as ccxt_async
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging
import aiohttp
import socket

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# DNS alternativo (Google, Cloudflare)
ALTERNATIVE_DNS = [
    ("8.8.8.8", 53),
    ("1.1.1.1", 53),
]

async def resolve_with_custom_dns(hostname: str) -> Optional[str]:
    """Resolve hostname usando DNS alternativo"""
    import struct
    
    # Constrói query DNS simples
    def build_dns_query(domain):
        transaction_id = b'\xAA\xBB'
        flags = b'\x01\x00'  # Standard query
        qdcount = b'\x00\x01'
        ancount = b'\x00\x00'
        nscount = b'\x00\x00'
        arcount = b'\x00\x00'
        
        header = transaction_id + flags + qdcount + ancount + nscount + arcount
        
        # Question section
        question = b''
        for part in domain.split('.'):
            question += bytes([len(part)]) + part.encode()
        question += b'\x00'  # End of domain
        question += b'\x00\x01'  # Type A
        question += b'\x00\x01'  # Class IN
        
        return header + question
    
    for dns_server, port in ALTERNATIVE_DNS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            
            query = build_dns_query(hostname)
            sock.sendto(query, (dns_server, port))
            
            response, _ = sock.recvfrom(512)
            sock.close()
            
            # Parse response - skip header (12 bytes) and question
            offset = 12
            while response[offset] != 0:
                offset += 1 + response[offset]
            offset += 5  # Skip null byte and QTYPE/QCLASS
            
            # Read answers
            while offset < len(response):
                # Skip name pointer or name
                if response[offset] & 0xC0 == 0xC0:
                    offset += 2
                else:
                    while response[offset] != 0:
                        offset += 1 + response[offset]
                    offset += 1
                
                if offset + 10 > len(response):
                    break
                    
                rtype = struct.unpack('>H', response[offset:offset+2])[0]
                offset += 8  # Skip type, class, ttl
                rdlength = struct.unpack('>H', response[offset:offset+2])[0]
                offset += 2
                
                if rtype == 1 and rdlength == 4:  # Type A, IPv4
                    ip = '.'.join(str(b) for b in response[offset:offset+4])
                    logger.info(f"Resolved {hostname} to {ip} via {dns_server}")
                    return ip
                
                offset += rdlength
                
        except Exception as e:
            logger.warning(f"DNS resolution via {dns_server} failed: {e}")
            continue
    
    return None


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
        
        # Primeiro tenta via ccxt
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
            logger.warning(f"CCXT failed for {symbol}, trying direct IP fallback: {e}")
            
            # Fallback: requisição direta para Binance via IP
            return await self._fetch_ohlcv_direct(symbol, timeframe, limit)
    
    async def _fetch_ohlcv_direct(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 200
    ) -> pd.DataFrame:
        """
        Fallback: busca dados diretamente da Binance via DNS alternativo.
        """
        # Converter símbolo: BTC/USDT -> BTCUSDT
        binance_symbol = symbol.replace("/", "")
        tf = self.TIMEFRAME_MAPPING.get(timeframe, timeframe)
        
        # Resolve IP via DNS alternativo
        resolved_ip = await resolve_with_custom_dns("api.binance.com")
        
        if not resolved_ip:
            logger.error(f"Could not resolve api.binance.com via alternative DNS")
            return pd.DataFrame()
        
        try:
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                "symbol": binance_symbol,
                "interval": tf,
                "limit": limit
            }
            
            # Criar connector com IP resolvido
            connector = aiohttp.TCPConnector(
                resolver=aiohttp.resolver.AsyncResolver(nameservers=["8.8.8.8", "1.1.1.1"])
            )
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if not data:
                            return pd.DataFrame()
                        
                        # Binance retorna: [open_time, open, high, low, close, volume, ...]
                        ohlcv = [
                            [
                                candle[0],  # timestamp
                                float(candle[1]),  # open
                                float(candle[2]),  # high
                                float(candle[3]),  # low
                                float(candle[4]),  # close
                                float(candle[5])   # volume
                            ]
                            for candle in data
                        ]
                        
                        df = pd.DataFrame(
                            ohlcv,
                            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                        )
                        
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df = df.set_index('timestamp')
                        
                        logger.info(f"Successfully fetched {symbol} via alternative DNS")
                        return df
                    else:
                        logger.warning(f"Binance API returned status {response.status}")
                        return pd.DataFrame()
                        
        except Exception as e:
            logger.error(f"Direct fetch failed for {symbol}: {e}")
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
