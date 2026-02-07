"""
Portal Sinais - Signal Engine / Worker
Motor de análise que executa as estratégias em loop assíncrono.
"""
import asyncio
import logging
import os
import json
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timezone
import pandas as pd

from app.core.config import get_settings
from app.services.exchange import exchange_service
from app.services.telegram import telegram_service
from app.services.cryptobubbles import cryptobubbles_service
from app.strategies import (
    BaseStrategy, SignalResult,
    RSIStrategy, MACDStrategy, GCMStrategy,
    ScalpingStrategy, SwingTradeStrategy, DayTradeStrategy, RsiEma50Strategy,
    JFNStrategy
)

logger = logging.getLogger(__name__)

# Caminho para o arquivo de configuração de timeframes por estratégia
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
STRATEGY_TIMEFRAMES_FILE = os.path.join(CONFIG_DIR, "strategy_timeframes.json")

DEFAULT_STRATEGY_TIMEFRAMES = {
    "GCM": ["1h"],
    "RSI": ["1h"],
    "MACD": ["1h"],
    "RSI_EMA50": ["1h"],
    "SCALPING": ["3m", "5m"],
    "SWING_TRADE": ["1d"],
    "DAY_TRADE": ["15m"],
    "JFN": ["1h"]
}


class SignalEngine:
    """
    Motor de análise de sinais.
    
    Executa as estratégias configuradas em loop assíncrono,
    enviando sinais via callback (WebSocket).
    """
    
    # Mapeamento de timeframes para segundos
    TIMEFRAME_SECONDS = {
        "1m": 60,
        "3m": 180,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "1h": 3600,
        "2h": 7200,
        "4h": 14400,
        "6h": 21600,
        "8h": 28800,
        "12h": 43200,
        "1d": 86400,
        "3d": 259200,
        "1w": 604800,
    }
    
    def __init__(self):
        self.settings = get_settings()
        self.strategies: Dict[str, BaseStrategy] = {}
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._signal_callbacks: List[Callable] = []
        self._last_summary_bucket: Optional[int] = None
        
        # Timeframes por estratégia (configurável)
        self.strategy_timeframes: Dict[str, List[str]] = {}
        
        # Cache de sinais enviados: chave = "symbol_timeframe_strategy_direction" -> candle_start_timestamp
        # Evita enviar o mesmo sinal múltiplas vezes dentro da mesma vela
        self._sent_signals_cache: Dict[str, int] = {}
        
        # Inicializar estratégias padrão
        self._init_default_strategies()
    
    def _init_default_strategies(self):
        """Inicializa estratégias com parâmetros do .env"""
        settings = self.settings
        
        self.strategies = {
            "RSI": RSIStrategy(
                period=settings.rsi_period,
                signal_period=settings.rsi_signal,
                overbought=settings.rsi_overbought,
                oversold=settings.rsi_oversold
            ),
            "MACD": MACDStrategy(
                fast_period=settings.macd_fast,
                slow_period=settings.macd_slow,
                signal_period=settings.macd_signal
            ),
            "GCM": GCMStrategy(
                harsi_length=settings.harsi_len,
                harsi_smooth=settings.harsi_smooth
            ),
            "SCALPING": ScalpingStrategy(
                ema_fast=settings.scalping_ema_fast,
                ema_slow=settings.scalping_ema_slow,
                rsi_period=settings.rsi_period
            ),
            "SWING_TRADE": SwingTradeStrategy(
                harsi_len=settings.harsi_len,
                harsi_smooth=settings.harsi_smooth
            ),
            "DAY_TRADE": DayTradeStrategy(
                macd_fast=settings.macd_fast,
                macd_slow=settings.macd_slow,
                macd_signal=settings.macd_signal,
                rsi_period=settings.rsi_period,
                confirm_window=settings.confirm_window
            ),
            "RSI_EMA50": RsiEma50Strategy(
                rsi_period=settings.rsi_period,
                rsi_signal=settings.rsi_signal,
                rsi_overbought=settings.rsi_overbought,
                rsi_oversold=settings.rsi_oversold,
                ema_period=50
            ),
            "JFN": JFNStrategy()
        }
        
        # Configurar Telegram
        if settings.telegram_bot_token and settings.telegram_chat_id:
            telegram_service.configure(
                settings.telegram_bot_token,
                settings.telegram_chat_id
            )
        
        # Carregar timeframes por estratégia do arquivo de configuração
        self._load_strategy_timeframes()
    
    def _load_strategy_timeframes(self):
        """Carrega os timeframes por estratégia do arquivo de configuração"""
        try:
            if os.path.exists(STRATEGY_TIMEFRAMES_FILE):
                with open(STRATEGY_TIMEFRAMES_FILE, 'r') as f:
                    loaded = json.load(f)
                    self.strategy_timeframes = DEFAULT_STRATEGY_TIMEFRAMES.copy()
                    self.strategy_timeframes.update(loaded)
                    logger.info(f"Loaded strategy timeframes from {STRATEGY_TIMEFRAMES_FILE}")
            else:
                self.strategy_timeframes = DEFAULT_STRATEGY_TIMEFRAMES.copy()
                logger.info("Using default strategy timeframes")
        except Exception as e:
            logger.error(f"Error loading strategy timeframes: {e}")
            self.strategy_timeframes = DEFAULT_STRATEGY_TIMEFRAMES.copy()
    
    def update_strategies(self, config: Dict[str, Any]):
        """
        Atualiza parâmetros das estratégias dinamicamente.
        """
        if "strategy_params" in config:
            strategy_params = config.get("strategy_params", {}) or {}
            for strategy_name, params in strategy_params.items():
                if strategy_name not in self.strategies:
                    continue
                current_params = getattr(self.strategies[strategy_name], "params", {}).copy()
                current_params.update(params or {})

                if strategy_name == "RSI":
                    self.strategies[strategy_name] = RSIStrategy(**current_params)
                elif strategy_name == "MACD":
                    self.strategies[strategy_name] = MACDStrategy(**current_params)
                elif strategy_name == "GCM":
                    self.strategies[strategy_name] = GCMStrategy(**current_params)
                elif strategy_name == "SCALPING":
                    self.strategies[strategy_name] = ScalpingStrategy(**current_params)
                elif strategy_name == "SWING_TRADE":
                    self.strategies[strategy_name] = SwingTradeStrategy(**current_params)
                elif strategy_name == "DAY_TRADE":
                    self.strategies[strategy_name] = DayTradeStrategy(**current_params)
                elif strategy_name == "RSI_EMA50":
                    self.strategies[strategy_name] = RsiEma50Strategy(**current_params)
                elif strategy_name == "JFN":
                    self.strategies[strategy_name] = JFNStrategy(**current_params)

        if "rsi_period" in config:
            self.strategies["RSI"] = RSIStrategy(
                period=config.get("rsi_period", 14),
                signal_period=config.get("rsi_signal", 9),
                overbought=config.get("rsi_overbought", 85),
                oversold=config.get("rsi_oversold", 15)
            )
        
        if "macd_fast" in config:
            self.strategies["MACD"] = MACDStrategy(
                fast_period=config.get("macd_fast", 12),
                slow_period=config.get("macd_slow", 26),
                signal_period=config.get("macd_signal", 9)
            )
        
        if "harsi_len" in config:
            self.strategies["GCM"] = GCMStrategy(
                harsi_length=config.get("harsi_len", 10),
                harsi_smooth=config.get("harsi_smooth", 5)
            )
        
        logger.info("Strategies updated with new configuration")

    def get_strategy_params(self) -> Dict[str, Dict[str, Any]]:
        """Retorna parametros atuais de cada estrategia"""
        params: Dict[str, Dict[str, Any]] = {}
        for name, strategy in self.strategies.items():
            params[name] = getattr(strategy, "params", {}).copy()
        return params
    
    def update_strategy_timeframes(self, strategy_timeframes: Dict[str, List[str]]):
        """
        Atualiza os timeframes específicos por estratégia.
        
        Args:
            strategy_timeframes: Dict mapeando estratégia para lista de timeframes
                Ex: {"GCM": ["15m", "1h"], "SCALPING": ["3m", "5m"]}
        """
        self.strategy_timeframes = strategy_timeframes
        logger.info(f"Strategy timeframes updated: {strategy_timeframes}")
    
    def get_timeframes_for_strategy(self, strategy_name: str) -> List[str]:
        """
        Retorna os timeframes configurados para uma estratégia específica.
        Se não configurado, retorna os timeframes padrão do settings.
        """
        if strategy_name in self.strategy_timeframes:
            return self.strategy_timeframes[strategy_name]
        return self.settings.timeframes_list
    
    def add_signal_callback(self, callback: Callable):
        """Adiciona callback para receber sinais"""
        self._signal_callbacks.append(callback)
    
    def remove_signal_callback(self, callback: Callable):
        """Remove callback"""
        if callback in self._signal_callbacks:
            self._signal_callbacks.remove(callback)
    
    def _get_candle_start_timestamp(self, timeframe: str) -> int:
        """
        Calcula o timestamp de início da vela atual baseado no timeframe.
        
        Por exemplo, se for 14:37 e o timeframe for 1h, retorna timestamp de 14:00.
        Se for 14:37 e timeframe for 15m, retorna timestamp de 14:30.
        
        Returns:
            Timestamp em segundos do início da vela atual
        """
        now = datetime.now(timezone.utc)
        current_timestamp = int(now.timestamp())
        
        # Obter duração do timeframe em segundos
        tf_seconds = self.TIMEFRAME_SECONDS.get(timeframe, 3600)  # default 1h
        
        # Calcular o início da vela atual (arredondar para baixo)
        candle_start = (current_timestamp // tf_seconds) * tf_seconds
        
        return candle_start
    
    def _get_signal_cache_key(self, signal: SignalResult) -> str:
        """
        Gera chave única para o cache de sinais.
        
        Formato: symbol_timeframe_strategy_direction
        """
        return f"{signal.symbol}_{signal.timeframe}_{signal.strategy}_{signal.direction}"
    
    def _should_send_signal(self, signal: SignalResult) -> bool:
        """
        Verifica se o sinal deve ser enviado ou se já foi enviado nesta vela.
        
        Um sinal só é enviado uma vez por vela. Se o sinal persistir na próxima
        vela, será enviado novamente.
        
        Returns:
            True se deve enviar, False se já foi enviado nesta vela
        """
        cache_key = self._get_signal_cache_key(signal)
        current_candle_start = self._get_candle_start_timestamp(signal.timeframe)
        
        # Verificar se já enviamos este sinal nesta vela
        if cache_key in self._sent_signals_cache:
            last_sent_candle = self._sent_signals_cache[cache_key]
            if last_sent_candle == current_candle_start:
                logger.debug(f"Signal already sent for this candle: {cache_key}")
                return False
        
        # Atualizar cache com o timestamp da vela atual
        self._sent_signals_cache[cache_key] = current_candle_start
        logger.info(f"New signal will be sent: {cache_key} (candle: {datetime.fromtimestamp(current_candle_start, tz=timezone.utc)})")
        
        # Limpar cache antigo (sinais de velas anteriores que não são mais necessários)
        self._cleanup_signal_cache()
        
        return True
    
    def _cleanup_signal_cache(self):
        """
        Remove entradas antigas do cache de sinais para evitar uso excessivo de memória.
        Remove sinais de velas que passaram há mais de 2 períodos do maior timeframe (1 semana).
        """
        cutoff_time = int(datetime.now(timezone.utc).timestamp()) - (2 * 604800)  # 2 semanas
        
        keys_to_remove = [
            key for key, timestamp in self._sent_signals_cache.items()
            if timestamp < cutoff_time
        ]
        
        for key in keys_to_remove:
            del self._sent_signals_cache[key]
        
        if keys_to_remove:
            logger.debug(f"Cleaned up {len(keys_to_remove)} old signal cache entries")
    
    async def _emit_signal(self, signal: SignalResult):
        """Emite sinal para todos os callbacks registrados e Telegram"""
        # Verificar se deve enviar (evita duplicados na mesma vela)
        if not self._should_send_signal(signal):
            logger.debug("Skipping signal - already sent for this candle")
            return

        # Verificar se ha grupo configurado para a estrategia
        target_chat = telegram_service.get_strategy_group(signal.strategy) or telegram_service.chat_id
        if not target_chat:
            logger.debug(f"Skipping signal - no Telegram group configured for {signal.strategy}")
            return

        # Enviar para callbacks (WebSocket)
        for callback in self._signal_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(signal)
                else:
                    callback(signal)
            except Exception as e:
                logger.error(f"Error in signal callback: {e}")
        
        # Enviar para Telegram
        if telegram_service.is_enabled:
            try:
                await telegram_service.send_signal(
                    signal,
                    include_disclaimer=self.settings.telegram_include_disclaimer
                )
            except Exception as e:
                logger.error(f"Error sending to Telegram: {e}")
    
    async def analyze_symbol(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        active_strategies: List[str] = None
    ) -> List[SignalResult]:
        """
        Analisa um símbolo com as estratégias ativas.
        
        Returns:
            Lista de sinais gerados
        """
        signals = []
        
        if active_strategies is None:
            active_strategies = self.settings.strategies_list
        
        for strategy_name in active_strategies:
            if strategy_name not in self.strategies:
                continue
            
            strategy = self.strategies[strategy_name]
            
            try:
                signal = strategy.analyze(df, symbol, timeframe)
                if signal:
                    signals.append(signal)
                    logger.info(f"Signal generated: {signal.strategy} {signal.direction} for {symbol}")
            except Exception as e:
                logger.error(f"Error analyzing {symbol} with {strategy_name}: {e}")
        
        return signals
    
    async def run_analysis_cycle(
        self,
        symbols: List[str] = None,
        timeframes: List[str] = None,
        active_strategies: List[str] = None
    ) -> List[SignalResult]:
        """
        Executa um ciclo completo de análise.
        
        Se use_cryptobubbles estiver habilitado e symbols não for fornecido,
        busca automaticamente os top N pares com maior variação em 24h.
        
        Returns:
            Lista de todos os sinais gerados no ciclo
        """
        # Determinar símbolos a analisar
        if symbols is None:
            if self.settings.use_cryptobubbles:
                # Buscar símbolos do CryptoBubbles
                symbols = await cryptobubbles_service.get_top_volatile_symbols(
                    limit=self.settings.cryptobubbles_top_limit,
                    exclude_stablecoins=self.settings.cryptobubbles_exclude_stablecoins,
                    min_volume=self.settings.cryptobubbles_min_volume
                )
                logger.info(f"Using {len(symbols)} symbols from CryptoBubbles (top volatile)")
                
                # Fallback para settings se CryptoBubbles falhar
                if not symbols:
                    logger.warning("CryptoBubbles returned no symbols, using fallback from settings")
                    symbols = self.settings.symbols_list
            else:
                symbols = self.settings.symbols_list
        if timeframes is None:
            timeframes = self.settings.timeframes_list
        if active_strategies is None:
            active_strategies = self.settings.strategies_list
        
        all_signals = []
        
        # Coletar todos os timeframes necessários (união de todos os timeframes por estratégia)
        required_timeframes = set(timeframes)
        for strategy in active_strategies:
            strategy_tfs = self.get_timeframes_for_strategy(strategy)
            required_timeframes.update(strategy_tfs)
        
        for timeframe in required_timeframes:
            logger.info(f"Analyzing {len(symbols)} symbols on {timeframe}...")
            
            # Quais estratégias usar neste timeframe
            strategies_for_tf = [
                s for s in active_strategies 
                if timeframe in self.get_timeframes_for_strategy(s)
            ]
            
            if not strategies_for_tf:
                continue
            
            # Buscar dados para todos os símbolos
            data = await exchange_service.fetch_multiple_ohlcv(
                symbols,
                timeframe,
                limit=self.settings.chunk_size
            )
            
            for symbol, df in data.items():
                if df.empty:
                    continue
                
                signals = await self.analyze_symbol(
                    symbol, timeframe, df, strategies_for_tf
                )
                
                for signal in signals:
                    all_signals.append(signal)
                    await self._emit_signal(signal)
        
        logger.info(f"Analysis cycle complete. Generated {len(all_signals)} signals.")
        return all_signals
    
    async def _worker_loop(self):
        """Loop principal do worker"""
        logger.info("Signal Engine worker started")
        
        while self.is_running:
            try:
                await self.run_analysis_cycle()
                await self._maybe_send_summary()
                
                # Aguardar intervalo configurado
                await asyncio.sleep(self.settings.worker_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(10)  # Retry delay
        
        logger.info("Signal Engine worker stopped")

    async def _maybe_send_summary(self):
        """Envia resumo CryptoBubbles 1h a cada 15 minutos"""
        if not telegram_service.is_enabled:
            return

        summary_chat = telegram_service.get_summary_group()
        if not summary_chat:
            return

        now = datetime.now(timezone.utc)
        bucket = int(now.timestamp() // 900)  # 15 minutos
        if self._last_summary_bucket == bucket:
            return

        summary = await cryptobubbles_service.get_summary_1h(
            exclude_stablecoins=self.settings.cryptobubbles_exclude_stablecoins,
            min_volume=self.settings.cryptobubbles_min_volume
        )

        positive_pct = summary.get("positive_pct", 0)
        negative_pct = summary.get("negative_pct", 0)
        positives = summary.get("positives", 0)
        negatives = summary.get("negatives", 0)
        total = summary.get("total", 0)
        top_5 = summary.get("top_5_abs", [])

        bias_up = positive_pct >= negative_pct
        bias_emoji = "🟢" if bias_up else "🔴"
        bias_sign = "+" if bias_up else "-"

        lines = [
            f"📊 RESUMO CRIPTO 1H {bias_emoji} {bias_sign}",
            "",
            f"{positive_pct:.1f}% positivas / {negative_pct:.1f}% negativas",
            "",
            f"Analisadas: {total}",
            f"Positivas: {positives} | Negativas: {negatives}",
            "",
            "TOP 5 (variacao absoluta)",
        ]

        for idx, item in enumerate(top_5, start=1):
            symbol = item.get("symbol", "")
            change = item.get("change", 0)
            sign = "+" if change >= 0 else ""
            lines.append(f"{idx}. {symbol} {sign}{change:.1f}%")

        message = "\n".join(lines)

        try:
            sent = await telegram_service.send_message(
                message,
                chat_id=summary_chat,
                include_disclaimer=True
            )
            if sent:
                self._last_summary_bucket = bucket
        except Exception as e:
            logger.error(f"Error sending summary to Telegram: {e}")
    
    async def start(self):
        """Inicia o worker em background"""
        if self.is_running:
            logger.warning("Worker already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._worker_loop())
        logger.info("Signal Engine started")
    
    async def stop(self):
        """Para o worker"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        await exchange_service.close()
        await cryptobubbles_service.close()
        logger.info("Signal Engine stopped")
    
    @property
    def status(self) -> Dict[str, Any]:
        """Retorna status do engine"""
        return {
            "running": self.is_running,
            "strategies": list(self.strategies.keys()),
            "symbols_count": len(self.settings.symbols_list),
            "timeframes": self.settings.timeframes_list,
            "strategy_timeframes": self.strategy_timeframes,
            "interval_seconds": self.settings.worker_interval_seconds,
            "use_cryptobubbles": self.settings.use_cryptobubbles,
            "cryptobubbles_limit": self.settings.cryptobubbles_top_limit
        }


# Instância global do engine
signal_engine = SignalEngine()
