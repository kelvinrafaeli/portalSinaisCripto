"""
Portal Sinais - WebSocket Manager
Gerencia conexões WebSocket para streaming de sinais em tempo real.
"""
import asyncio
import json
import logging
from typing import List, Set, Dict, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from app.strategies.base import SignalResult

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Gerencia conexões WebSocket para broadcast de sinais.
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Aceita nova conexão WebSocket"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove conexão WebSocket"""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Envia mensagem para todas as conexões ativas.
        """
        if not self.active_connections:
            return
        
        json_message = json.dumps(message, default=str)
        
        dead_connections = set()
        
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(json_message)
                except Exception as e:
                    logger.warning(f"Failed to send message: {e}")
                    dead_connections.add(connection)
        
        # Remover conexões mortas
        for conn in dead_connections:
            await self.disconnect(conn)
    
    async def broadcast_signal(self, signal: SignalResult):
        """
        Envia sinal para todos os clientes conectados.
        """
        message = {
            "type": "signal",
            "data": signal.to_dict()
        }
        await self.broadcast(message)
    
    async def send_heartbeat(self):
        """Envia heartbeat para manter conexões vivas"""
        message = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)
    
    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


class SignalSubscriptionManager:
    """
    Gerencia assinaturas de sinais por filtros.
    Permite que clientes recebam apenas sinais específicos.
    """
    
    def __init__(self):
        self.subscriptions: Dict[WebSocket, Dict[str, Any]] = {}
        self._connection_manager = ConnectionManager()
    
    async def subscribe(
        self, 
        websocket: WebSocket,
        symbols: List[str] = None,
        timeframes: List[str] = None,
        strategies: List[str] = None
    ):
        """
        Inscreve cliente com filtros específicos.
        """
        await self._connection_manager.connect(websocket)
        
        self.subscriptions[websocket] = {
            "symbols": set(symbols) if symbols else None,
            "timeframes": set(timeframes) if timeframes else None,
            "strategies": set(strategies) if strategies else None
        }
    
    async def unsubscribe(self, websocket: WebSocket):
        """Remove inscrição do cliente"""
        await self._connection_manager.disconnect(websocket)
        self.subscriptions.pop(websocket, None)
    
    def _matches_filter(
        self, 
        signal: SignalResult,
        filters: Dict[str, Any]
    ) -> bool:
        """Verifica se o sinal corresponde aos filtros"""
        if filters.get("symbols") and signal.symbol not in filters["symbols"]:
            return False
        if filters.get("timeframes") and signal.timeframe not in filters["timeframes"]:
            return False
        if filters.get("strategies") and signal.strategy not in filters["strategies"]:
            return False
        return True
    
    async def broadcast_signal(self, signal: SignalResult):
        """
        Envia sinal apenas para clientes que correspondem aos filtros.
        """
        message = {
            "type": "signal",
            "data": signal.to_dict()
        }
        json_message = json.dumps(message, default=str)
        
        dead_connections = set()
        
        for websocket, filters in self.subscriptions.items():
            if not self._matches_filter(signal, filters):
                continue
            
            try:
                await websocket.send_text(json_message)
            except Exception as e:
                logger.warning(f"Failed to send signal: {e}")
                dead_connections.add(websocket)
        
        for conn in dead_connections:
            await self.unsubscribe(conn)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Envia para todos sem filtros"""
        await self._connection_manager.broadcast(message)


# Instâncias globais
ws_manager = ConnectionManager()
subscription_manager = SignalSubscriptionManager()
