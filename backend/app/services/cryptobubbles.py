"""
Portal Sinais - CryptoBubbles Service
Captura os top pares de moedas com maior variação nas últimas 24h.
"""
import aiohttp
from aiohttp import TCPConnector
from aiohttp.resolver import AsyncResolver
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import socket

logger = logging.getLogger(__name__)

# URL da API do CryptoBubbles
CRYPTOBUBBLES_API_URL = "https://cryptobubbles.net/backend/data/bubbles1000.usd.json"

# IPs conhecidos do CryptoBubbles (fallback se DNS falhar)
CRYPTOBUBBLES_IPS = ["104.20.25.124", "172.66.167.210"]

# Headers para simular requisição de browser
CRYPTOBUBBLES_HEADERS = {
    "accept": "*/*",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "priority": "u=1, i",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "referer": "https://cryptobubbles.net/",
    "Host": "cryptobubbles.net",
}


@dataclass
class CryptoBubblesCoin:
    """Dados de uma moeda do CryptoBubbles"""
    id: str
    name: str
    symbol: str
    slug: str
    rank: int
    price: float
    marketcap: float
    volume: float
    stable: bool
    performance_day: float  # Variação em 24h (%)
    performance_hour: float
    performance_week: float
    binance_symbol: Optional[str] = None
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> Optional["CryptoBubblesCoin"]:
        """Cria instância a partir dos dados da API"""
        try:
            # Extrair símbolo da Binance
            symbols = data.get("symbols", {})
            binance_symbol = symbols.get("binance")
            
            # Converter formato se necessário (BTC_USDT -> BTCUSDT)
            if binance_symbol:
                binance_symbol = binance_symbol.replace("_", "")
            
            performance = data.get("performance", {})
            
            return cls(
                id=str(data.get("id", "")),
                name=data.get("name", ""),
                symbol=data.get("symbol", ""),
                slug=data.get("slug", ""),
                rank=data.get("rank", 0),
                price=float(data.get("price", 0)),
                marketcap=float(data.get("marketcap", 0)),
                volume=float(data.get("volume", 0)),
                stable=data.get("stable", False),
                performance_day=float(performance.get("day", 0)),
                performance_hour=float(performance.get("hour", 0)),
                performance_week=float(performance.get("week", 0)),
                binance_symbol=binance_symbol
            )
        except Exception as e:
            logger.warning(f"Error parsing coin data: {e}")
            return None


class CryptoBubblesService:
    """
    Serviço para capturar dados do CryptoBubbles.
    
    Fornece os top N pares com maior variação nas últimas 24h.
    """
    
    def __init__(self):
        self._cache: List[CryptoBubblesCoin] = []
        self._cache_time: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)  # Cache por 5 minutos
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Retorna sessão HTTP reutilizável com DNS customizado"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            # Usar Google DNS para resolver nomes
            try:
                resolver = AsyncResolver(nameservers=["8.8.8.8", "1.1.1.1"])
                connector = TCPConnector(resolver=resolver, ssl=False)
                self._session = aiohttp.ClientSession(
                    timeout=timeout,
                    connector=connector
                )
            except Exception as e:
                logger.warning(f"Failed to create session with custom DNS: {e}")
                self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Fecha a sessão HTTP"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _fetch_with_fallback(self) -> Optional[List[Dict]]:
        """
        Tenta buscar dados via URL normal, com fallback para IP direto.
        """
        # Tentar URL normal primeiro
        try:
            session = await self._get_session()
            async with session.get(
                CRYPTOBUBBLES_API_URL,
                headers=CRYPTOBUBBLES_HEADERS,
                ssl=True
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.warning(f"Normal request failed: {e}")
        
        # Fallback: tentar via IP direto
        for ip in CRYPTOBUBBLES_IPS:
            try:
                url = f"https://{ip}/backend/data/bubbles1000.usd.json"
                timeout = aiohttp.ClientTimeout(total=15)
                connector = TCPConnector(ssl=False)
                
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.get(url, headers=CRYPTOBUBBLES_HEADERS) as response:
                        if response.status == 200:
                            logger.info(f"Fetched CryptoBubbles via IP fallback: {ip}")
                            return await response.json()
            except Exception as e:
                logger.warning(f"IP fallback {ip} failed: {e}")
                continue
        
        return None
    
    async def fetch_all_coins(self, force_refresh: bool = False) -> List[CryptoBubblesCoin]:
        """
        Busca todos os dados do CryptoBubbles.
        
        Args:
            force_refresh: Se True, ignora o cache
            
        Returns:
            Lista de moedas com dados de performance
        """
        # Verificar cache
        if not force_refresh and self._cache and self._cache_time:
            if datetime.now() - self._cache_time < self._cache_duration:
                logger.debug("Returning cached CryptoBubbles data")
                return self._cache
        
        try:
            logger.info("Fetching data from CryptoBubbles API...")
            data = await self._fetch_with_fallback()
            
            if data is None:
                logger.error("All CryptoBubbles fetch attempts failed")
                return self._cache if self._cache else []
            
            if not isinstance(data, list):
                logger.error("CryptoBubbles API returned invalid data format")
                return self._cache if self._cache else []
            
            # Parsear dados
            coins = []
            for item in data:
                coin = CryptoBubblesCoin.from_api_data(item)
                if coin:
                    coins.append(coin)
            
            logger.info(f"Fetched {len(coins)} coins from CryptoBubbles")
            
            # Atualizar cache
            self._cache = coins
            self._cache_time = datetime.now()
            
            return coins
                
        except Exception as e:
            logger.error(f"Error fetching CryptoBubbles data: {e}")
            return self._cache if self._cache else []
    
    async def get_top_volatile_symbols(
        self,
        limit: int = 100,
        exclude_stablecoins: bool = True,
        min_volume: float = 0,
        force_refresh: bool = False
    ) -> List[str]:
        """
        Retorna os símbolos Binance dos top N pares com maior variação em 24h.
        
        A variação é calculada em valor absoluto (tanto alta quanto baixa).
        
        Args:
            limit: Número máximo de símbolos a retornar
            exclude_stablecoins: Excluir stablecoins (USDT, USDC, etc.)
            min_volume: Volume mínimo em USD para filtrar
            force_refresh: Ignorar cache
            
        Returns:
            Lista de símbolos no formato Binance (ex: BTCUSDT)
        """
        coins = await self.fetch_all_coins(force_refresh)
        
        # Filtrar
        filtered_coins = []
        for coin in coins:
            # Pular se não tem símbolo Binance
            if not coin.binance_symbol:
                continue
            
            # Pular stablecoins se configurado
            if exclude_stablecoins and coin.stable:
                continue
            
            # Filtrar por volume mínimo
            if min_volume > 0 and coin.volume < min_volume:
                continue
            
            filtered_coins.append(coin)
        
        # Ordenar por variação absoluta em 24h (maior variação primeiro)
        sorted_coins = sorted(
            filtered_coins,
            key=lambda c: abs(c.performance_day),
            reverse=True
        )
        
        # Extrair símbolos únicos
        symbols = []
        seen = set()
        for coin in sorted_coins[:limit]:
            symbol = coin.binance_symbol
            if symbol and symbol not in seen:
                symbols.append(symbol)
                seen.add(symbol)
        
        logger.info(f"Selected {len(symbols)} top volatile symbols from CryptoBubbles")
        return symbols
    
    async def get_top_gainers(
        self,
        limit: int = 50,
        exclude_stablecoins: bool = True,
        force_refresh: bool = False
    ) -> List[str]:
        """
        Retorna os símbolos dos maiores ganhos em 24h.
        
        Returns:
            Lista de símbolos no formato Binance
        """
        coins = await self.fetch_all_coins(force_refresh)
        
        filtered_coins = [
            c for c in coins 
            if c.binance_symbol and (not exclude_stablecoins or not c.stable)
        ]
        
        # Ordenar por variação positiva (maiores ganhos)
        sorted_coins = sorted(
            filtered_coins,
            key=lambda c: c.performance_day,
            reverse=True
        )
        
        return [c.binance_symbol for c in sorted_coins[:limit] if c.binance_symbol]
    
    async def get_top_losers(
        self,
        limit: int = 50,
        exclude_stablecoins: bool = True,
        force_refresh: bool = False
    ) -> List[str]:
        """
        Retorna os símbolos das maiores quedas em 24h.
        
        Returns:
            Lista de símbolos no formato Binance
        """
        coins = await self.fetch_all_coins(force_refresh)
        
        filtered_coins = [
            c for c in coins 
            if c.binance_symbol and (not exclude_stablecoins or not c.stable)
        ]
        
        # Ordenar por variação negativa (maiores quedas)
        sorted_coins = sorted(
            filtered_coins,
            key=lambda c: c.performance_day
        )
        
        return [c.binance_symbol for c in sorted_coins[:limit] if c.binance_symbol]
    
    async def get_top_volatile_with_details(
        self,
        limit: int = 100,
        exclude_stablecoins: bool = True,
        min_volume: float = 0,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retorna os top N pares com maior variação em 24h, incluindo todos os detalhes.
        
        Returns:
            Lista de dicts com dados completos de cada moeda
        """
        coins = await self.fetch_all_coins(force_refresh)
        
        # Filtrar
        filtered_coins = []
        for coin in coins:
            if not coin.binance_symbol:
                continue
            if exclude_stablecoins and coin.stable:
                continue
            if min_volume > 0 and coin.volume < min_volume:
                continue
            filtered_coins.append(coin)
        
        # Ordenar por variação absoluta em 24h
        sorted_coins = sorted(
            filtered_coins,
            key=lambda c: abs(c.performance_day),
            reverse=True
        )
        
        # Retornar detalhes
        result = []
        seen = set()
        for coin in sorted_coins[:limit]:
            if coin.binance_symbol in seen:
                continue
            seen.add(coin.binance_symbol)
            result.append({
                "symbol": coin.symbol,
                "name": coin.name,
                "binance_symbol": coin.binance_symbol,
                "rank": coin.rank,
                "price": coin.price,
                "volume": coin.volume,
                "marketcap": coin.marketcap,
                "change_1h": coin.performance_hour,
                "change_24h": coin.performance_day,
                "change_7d": coin.performance_week
            })
        
        return result
    
    async def get_coin_details(self, symbol: str) -> Optional[CryptoBubblesCoin]:
        """
        Busca detalhes de uma moeda específica pelo símbolo.
        
        Args:
            symbol: Símbolo (ex: BTC, ETH)
            
        Returns:
            Dados da moeda ou None se não encontrada
        """
        coins = await self.fetch_all_coins()
        
        symbol_upper = symbol.upper()
        for coin in coins:
            if coin.symbol.upper() == symbol_upper:
                return coin
        
        return None
    
    async def get_summary(self) -> Dict[str, Any]:
        """
        Retorna um resumo dos dados disponíveis.
        """
        coins = await self.fetch_all_coins()
        
        if not coins:
            return {
                "status": "no_data",
                "total_coins": 0
            }
        
        # Filtrar moedas com símbolo Binance (excluindo stablecoins)
        tradeable = [c for c in coins if c.binance_symbol and not c.stable]
        
        return {
            "status": "ok",
            "total_coins": len(coins),
            "tradeable_on_binance": len(tradeable),
            "cache_time": self._cache_time.isoformat() if self._cache_time else None,
            "top_5_gainers": [
                {"symbol": c.symbol, "change": c.performance_day}
                for c in sorted(tradeable, key=lambda x: x.performance_day, reverse=True)[:5]
            ],
            "top_5_losers": [
                {"symbol": c.symbol, "change": c.performance_day}
                for c in sorted(tradeable, key=lambda x: x.performance_day)[:5]
            ]
        }


# Instância global do serviço
cryptobubbles_service = CryptoBubblesService()
