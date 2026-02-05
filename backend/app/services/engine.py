"""
Portal Sinais - Signal Engine / Worker
Motor de análise que executa as estratégias em loop assíncrono.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import pandas as pd

from app.core.config import get_settings
from app.services.exchange import exchange_service
from app.services.telegram import telegram_service
from app.strategies import (
    BaseStrategy, SignalResult,
    RSIStrategy, MACDStrategy, GCMStrategy, ComboStrategy,
    ScalpingStrategy, SwingTradeStrategy, DayTradeStrategy, RsiEma50Strategy
)

logger = logging.getLogger(__name__)


class SignalEngine:
    """
    Motor de análise de sinais.
    
    Executa as estratégias configuradas em loop assíncrono,
    enviando sinais via callback (WebSocket).
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.strategies: Dict[str, BaseStrategy] = {}
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._signal_callbacks: List[Callable] = []
        
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
            "COMBO": ComboStrategy(
                rsi_period=settings.rsi_period,
                rsi_signal=settings.rsi_signal,
                macd_fast=settings.macd_fast,
                macd_slow=settings.macd_slow,
                macd_signal=settings.macd_signal,
                confirm_window=settings.confirm_window,
                require_ema50=settings.combo_require_ema50
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
                rsi_signal=settings.rsi_signal
            )
        }
        
        # Configurar Telegram
        if settings.telegram_bot_token and settings.telegram_chat_id:
            telegram_service.configure(
                settings.telegram_bot_token,
                settings.telegram_chat_id
            )
    
    def update_strategies(self, config: Dict[str, Any]):
        """
        Atualiza parâmetros das estratégias dinamicamente.
        """
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
    
    def add_signal_callback(self, callback: Callable):
        """Adiciona callback para receber sinais"""
        self._signal_callbacks.append(callback)
    
    def remove_signal_callback(self, callback: Callable):
        """Remove callback"""
        if callback in self._signal_callbacks:
            self._signal_callbacks.remove(callback)
    
    async def _emit_signal(self, signal: SignalResult):
        """Emite sinal para todos os callbacks registrados e Telegram"""
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
        
        Returns:
            Lista de todos os sinais gerados no ciclo
        """
        if symbols is None:
            symbols = self.settings.symbols_list
        if timeframes is None:
            timeframes = self.settings.timeframes_list
        if active_strategies is None:
            active_strategies = self.settings.strategies_list
        
        all_signals = []
        
        for timeframe in timeframes:
            logger.info(f"Analyzing {len(symbols)} symbols on {timeframe}...")
            
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
                    symbol, timeframe, df, active_strategies
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
                
                # Aguardar intervalo configurado
                await asyncio.sleep(self.settings.worker_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(10)  # Retry delay
        
        logger.info("Signal Engine worker stopped")
    
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
        logger.info("Signal Engine stopped")
    
    @property
    def status(self) -> Dict[str, Any]:
        """Retorna status do engine"""
        return {
            "running": self.is_running,
            "strategies": list(self.strategies.keys()),
            "symbols_count": len(self.settings.symbols_list),
            "timeframes": self.settings.timeframes_list,
            "interval_seconds": self.settings.worker_interval_seconds
        }


# Instância global do engine
signal_engine = SignalEngine()
