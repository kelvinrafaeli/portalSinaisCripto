"""
Portal Sinais - Serviço de Telegram
Envia sinais formatados para grupos do Telegram.
"""
import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.strategies.base import SignalResult

logger = logging.getLogger(__name__)

# Disclaimer de responsabilidade
DISCLAIMER = """
⚠️ *AVISO DE RESPONSABILIDADE*
Isso NÃO é uma recomendação de investimento.
Faça sua própria análise antes de operar.
"""


class TelegramService:
    """
    Serviço para enviar mensagens ao Telegram.
    """
    
    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self._enabled = bool(bot_token and chat_id)
        
    def configure(self, bot_token: str, chat_id: str):
        """Configura credenciais do Telegram"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self._enabled = bool(bot_token and chat_id)
        
    @property
    def is_enabled(self) -> bool:
        return self._enabled
        
    def format_signal_message(self, signal: SignalResult) -> str:
        """
        Formata mensagem do sinal baseado na estratégia.
        """
        strategy = signal.strategy.upper()
        symbol = signal.symbol
        timeframe = signal.timeframe
        direction = signal.direction
        
        # Emoji baseado na direção
        emoji = "🟢" if direction == "LONG" else "🔴"
        direction_text = "virou positivo" if direction == "LONG" else "virou negativo"
        signal_text = "LONG" if direction == "LONG" else "SHORT"
        
        # Header padrão
        header = "🏆 GRUPO CRIPTO JFN - TELEGRAM"
        
        # Formatação específica por estratégia
        if strategy == "GCM":
            return f"""———————————————
{header}

INDICADOR: GCM

MOEDA: {symbol}

TEMPO GRÁFICO: {timeframe.upper()}
CRUZAMENTO:  {emoji}
{direction_text}
———————————————"""

        elif strategy == "RSI":
            return f"""———————————————
{header}

INDICADOR: RSI

MOEDA: {symbol}

TEMPO GRÁFICO: {timeframe.upper()}
CRUZAMENTO:  {emoji}
{direction_text}
———————————————"""

        elif strategy == "MACD":
            return f"""———————————————
{header}

INDICADOR: MACD

MOEDA: {symbol}

TEMPO GRÁFICO: {timeframe.upper()}
CRUZAMENTO:  {emoji}
{direction_text}
———————————————"""

        elif strategy == "RSI_EMA50":
            return f"""———————————————
{header}

INDICADORES: RSI + EMA50 

TEMPO GRÁFICO: {timeframe.upper()}

MOEDA: {symbol}
SINAL:  {signal_text}   {emoji}
———————————————"""

        elif strategy == "SCALPING":
            return f"""———————————————
{header}

TIPO DE OPERAÇÃO: SCALPING

MOEDA: {symbol}
SINAL: {signal_text}   {emoji}
———————————————"""

        elif strategy == "SWING_TRADE" or strategy == "GCM_PRO":
            return f"""———————————————
{header}

TIPO DE OPERAÇÃO: SWING TRADE

MOEDA: {symbol}
SINAL: {signal_text}   {emoji}
———————————————"""

        elif strategy == "DAY_TRADE" or strategy == "COMBO":
            return f"""———————————————
{header}

TIPO DE OPERAÇÃO: DAY TRADE

MOEDA: {symbol}
SINAL: {signal_text}   {emoji}
———————————————"""

        else:
            # Formato genérico
            return f"""———————————————
{header}

INDICADOR: {strategy}

MOEDA: {symbol}

TEMPO GRÁFICO: {timeframe.upper()}
SINAL: {signal_text}   {emoji}
———————————————"""
    
    async def send_message(
        self, 
        text: str, 
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown",
        include_disclaimer: bool = True
    ) -> bool:
        """
        Envia mensagem para o Telegram.
        """
        if not self._enabled:
            logger.warning("Telegram não configurado - mensagem não enviada")
            return False
            
        target_chat = chat_id or self.chat_id
        
        # Adicionar disclaimer se solicitado
        full_text = text
        if include_disclaimer:
            full_text = f"{text}\n{DISCLAIMER}"
        
        payload = {
            "chat_id": target_chat,
            "text": full_text,
            "parse_mode": parse_mode
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/sendMessage",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Mensagem enviada ao Telegram: {target_chat}")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Erro ao enviar ao Telegram: {error}")
                        return False
        except Exception as e:
            logger.error(f"Exceção ao enviar ao Telegram: {e}")
            return False
    
    async def send_signal(
        self, 
        signal: SignalResult,
        chat_id: Optional[str] = None,
        include_disclaimer: bool = True
    ) -> bool:
        """
        Formata e envia sinal para o Telegram.
        """
        message = self.format_signal_message(signal)
        return await self.send_message(
            message, 
            chat_id=chat_id,
            include_disclaimer=include_disclaimer
        )
        

# Instância global do serviço
telegram_service = TelegramService()


def get_telegram_service() -> TelegramService:
    """Retorna instância do serviço Telegram"""
    return telegram_service
