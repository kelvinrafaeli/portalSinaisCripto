"""
Portal Sinais - Serviço de Telegram
Envia sinais formatados para grupos do Telegram.
"""
import asyncio
import aiohttp
from aiohttp import TCPConnector
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import socket
import json
import os
from pathlib import Path

from app.strategies.base import SignalResult

logger = logging.getLogger(__name__)

# Disclaimer de responsabilidade
DISCLAIMER = """
⚠️ *AVISO DE RESPONSABILIDADE*
Isso NÃO é uma recomendação de investimento.
Faça sua própria análise antes de operar.
"""

# IP fixo do Telegram API (para bypass de DNS)
TELEGRAM_API_IPS = ["149.154.167.220", "149.154.166.110"]

# Arquivo de configuração
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
CONFIG_FILE = CONFIG_DIR / "telegram_config.json"


class TelegramService:
    """
    Serviço para enviar mensagens ao Telegram.
    """
    
    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self._enabled = bool(bot_token and chat_id)
        
        # Tentar carregar configuração salva
        self._load_config()
        
    def _load_config(self):
        """Carrega configuração do arquivo"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.bot_token = config.get('bot_token', '')
                    self.chat_id = config.get('chat_id', '')
                    self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
                    self._enabled = bool(self.bot_token and self.chat_id)
                    if self._enabled:
                        logger.info("Telegram configuration loaded from file")
        except Exception as e:
            logger.warning(f"Could not load Telegram config: {e}")
    
    def _save_config(self):
        """Salva configuração em arquivo"""
        try:
            # Criar diretório se não existir
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    'bot_token': self.bot_token,
                    'chat_id': self.chat_id
                }, f, indent=2)
            logger.info("Telegram configuration saved to file")
        except Exception as e:
            logger.error(f"Could not save Telegram config: {e}")
        
    def configure(self, bot_token: str, chat_id: str):
        """Configura credenciais do Telegram"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self._enabled = bool(bot_token and chat_id)
        
        # Salvar configuração em arquivo
        self._save_config()
        
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
        direction_emoji = "⬆️" if direction == "LONG" else "⬇️"
        signal_text = "LONG" if direction == "LONG" else "SHORT"
        
        # Formatação específica por estratégia
        if strategy == "RSI":
            # Valor do RSI
            rsi_value = f"{signal.rsi:.2f}" if signal.rsi else "N/A"
            return f"""🚨 INDICADOR RSI 🚨

Ativo: {symbol}
RSI: {rsi_value}
Tempo gráfico: {timeframe}"""

        elif strategy == "MACD":
            return f"""🔀 CRUZAMENTO MACD 🔀

{symbol}
MACD CRUZOU {direction_emoji}
Tempo gráfico: {timeframe}"""

        elif strategy == "RSI_EMA50":
            # Valor do RSI
            rsi_value = f"{signal.rsi:.2f}" if signal.rsi else "N/A"
            return f"""📊 RSI + EMA50 📊

Ativo: {symbol}
RSI: {rsi_value}
MACD CRUZOU {direction_emoji}
Tempo gráfico: {timeframe}"""

        elif strategy == "GCM":
            return f"""🏆 INDICADOR GCM 🏆

Ativo: {symbol}
Sinal: {signal_text} {direction_emoji}
Tempo gráfico: {timeframe}"""

        elif strategy == "SCALPING":
            return f"""⚡ SCALPING ⚡

Ativo: {symbol}
Sinal: {signal_text} {direction_emoji}
Tempo gráfico: {timeframe}"""

        elif strategy == "SWING_TRADE" or strategy == "GCM_PRO":
            return f"""📈 SWING TRADE 📈

Ativo: {symbol}
Sinal: {signal_text} {direction_emoji}
Tempo gráfico: {timeframe}"""

        elif strategy == "DAY_TRADE" or strategy == "COMBO":
            return f"""💹 DAY TRADE 💹

Ativo: {symbol}
Sinal: {signal_text} {direction_emoji}
Tempo gráfico: {timeframe}"""

        else:
            # Formato genérico
            return f"""📢 {strategy} 📢

Ativo: {symbol}
Sinal: {signal_text} {direction_emoji}
Tempo gráfico: {timeframe}"""
    
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
        
        # Tentar primeiro com DNS normal, depois com IP direto
        urls_to_try = [
            f"{self.base_url}/sendMessage",
        ]
        
        # Adicionar URLs com IP direto como fallback
        for ip in TELEGRAM_API_IPS:
            urls_to_try.append(f"https://{ip}/bot{self.bot_token}/sendMessage")
        
        last_error = None
        for url in urls_to_try:
            try:
                # Usar connector com SSL flexível para IP direto
                connector = TCPConnector(ssl=False) if url.startswith("https://149") else None
                
                async with aiohttp.ClientSession(connector=connector) as session:
                    headers = {"Host": "api.telegram.org"} if url.startswith("https://149") else {}
                    async with session.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as response:
                        if response.status == 200:
                            logger.info(f"Mensagem enviada ao Telegram: {target_chat}")
                            return True
                        else:
                            error = await response.text()
                            logger.error(f"Erro ao enviar ao Telegram: {error}")
                            last_error = error
            except Exception as e:
                logger.warning(f"Falha ao enviar via {url[:50]}...: {e}")
                last_error = str(e)
                continue
        
        logger.error(f"Todas as tentativas falharam. Último erro: {last_error}")
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
