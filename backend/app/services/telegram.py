"""
Portal Alertas - Serviço de Telegram
Envia alertas formatados para grupos do Telegram.
Suporta grupos individuais por estratégia.
"""
import asyncio
import aiohttp
from aiohttp import TCPConnector
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import socket
import json
import os
from pathlib import Path

from app.strategies.base import SignalResult

logger = logging.getLogger(__name__)

# Disclaimer de responsabilidade
DISCLAIMER = """
⚠️ AVISO DE RESPONSABILIDADE ⚠️
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
    Suporta grupos individuais por estratégia.
    """
    
    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token
        self.chat_id = chat_id  # Chat padrão (fallback)
        self.strategy_groups: Dict[str, str] = {}  # Mapeamento estratégia -> chat_id
        self.summary_group: str = ""  # Grupo para resumo CryptoBubbles
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
                    self.strategy_groups = config.get('strategy_groups', {})
                    self.summary_group = config.get('summary_group', '')
                    self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
                    self._enabled = bool(self.bot_token)
                    if self._enabled:
                        logger.info(f"Telegram configuration loaded. Groups: {list(self.strategy_groups.keys())}")
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
                    'chat_id': self.chat_id,
                    'strategy_groups': self.strategy_groups,
                    'summary_group': self.summary_group
                }, f, indent=2)
            logger.info("Telegram configuration saved to file")
        except Exception as e:
            logger.error(f"Could not save Telegram config: {e}")
        
    def configure(self, bot_token: str, chat_id: str = ""):
        """Configura credenciais do Telegram (token e chat padrão opcional)"""
        self.bot_token = bot_token
        if chat_id:
            self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self._enabled = bool(bot_token)
        
        # Salvar configuração em arquivo
        self._save_config()
    
    def configure_strategy_group(self, strategy: str, chat_id: str):
        """Configura grupo específico para uma estratégia"""
        if chat_id:
            self.strategy_groups[strategy.upper()] = chat_id
        else:
            # Remover configuração se chat_id for vazio
            self.strategy_groups.pop(strategy.upper(), None)
        self._save_config()
        logger.info(f"Strategy {strategy} configured with chat_id: {chat_id}")

    def configure_summary_group(self, chat_id: str):
        """Configura grupo para resumo CryptoBubbles"""
        self.summary_group = chat_id or ""
        self._save_config()
        logger.info("Summary group configured")

    def get_summary_group(self) -> str:
        """Retorna o chat_id do grupo de resumo"""
        return self.summary_group
    
    def get_strategy_group(self, strategy: str) -> Optional[str]:
        """Retorna o chat_id configurado para uma estratégia"""
        return self.strategy_groups.get(strategy.upper())
    
    def get_all_strategy_groups(self) -> Dict[str, str]:
        """Retorna todos os grupos configurados por estratégia"""
        return self.strategy_groups.copy()
    
    def remove_strategy_group(self, strategy: str):
        """Remove a configuração de grupo para uma estratégia"""
        self.strategy_groups.pop(strategy.upper(), None)
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

        def _format_price(value: float) -> str:
            if value >= 1:
                return f"{value:.4f}"
            if value >= 0.01:
                return f"{value:.6f}"
            return f"{value:.8f}"

        display_names = {
            "RSI_EMA50": "RSI EMA50",
            "DAY_TRADE": "DAY TRADE",
            "SWING_TRADE": "SWING TRADE",
        }
        display_name = display_names.get(strategy, strategy.replace("_", " "))
        title = f"*{display_name}*"
        lines = [
            title,
            "",
            f"*Ativo: {symbol} 🧩*",
            f"_Sinal: {signal_text} {direction_emoji}_",
            "",
            f"Timeframe: {timeframe} ⏱️",
        ]

        raw = signal.raw_data or {}
        indicator_lines = []
        if strategy == "RSI" and signal.rsi is not None:
            indicator_lines.append(f"RSI: {signal.rsi:.2f}")
        elif strategy == "MACD" and signal.macd is not None and signal.macd_signal is not None:
            indicator_lines.append(f"MACD: {signal.macd:.4f} | Signal: {signal.macd_signal:.4f}")
        elif strategy == "RSI_EMA50":
            if signal.rsi is not None:
                indicator_lines.append(f"RSI: {signal.rsi:.2f}")
            if signal.ema50 is not None:
                indicator_lines.append(f"EMA50: {signal.ema50:.4f}")
        elif strategy == "SCALPING":
            if signal.rsi is not None:
                indicator_lines.append(f"RSI: {signal.rsi:.2f}")
            if signal.ema50 is not None:
                indicator_lines.append(f"EMA50: {signal.ema50:.4f}")

        if indicator_lines:
            lines.extend(["", *indicator_lines])

        if strategy == "JFN" and "assertiveness" in raw:
            lines.extend(["", f"Assertividade: {raw['assertiveness']:.2f}% 🎯"])

        return "\n".join(lines)
    
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
        if not target_chat:
            logger.warning("Telegram chat_id vazio - mensagem nao enviada")
            return False
        
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
        Usa o grupo específico da estratégia se configurado.
        """
        # Usar grupo específico da estratégia se não for passado um chat_id
        if not chat_id:
            chat_id = self.strategy_groups.get(signal.strategy.upper())
        
        # Se não houver grupo específico e não houver chat padrão, não envia
        if not chat_id and not self.chat_id:
            logger.debug(f"No chat configured for strategy {signal.strategy}")
            return False
            
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
