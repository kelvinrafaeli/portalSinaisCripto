"""
Portal Sinais - WebSocket API Routes
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import List, Optional
import json
import asyncio

from app.services.websocket import ws_manager, subscription_manager
from app.services.engine import signal_engine

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket para receber sinais em tempo real.
    
    Mensagens de entrada (JSON):
    - subscribe: {"type": "subscribe", "symbols": [...], "timeframes": [...], "strategies": [...]}
    - unsubscribe: {"type": "unsubscribe"}
    - ping: {"type": "ping"}
    
    Mensagens de saída (JSON):
    - signal: {"type": "signal", "data": {...}}
    - heartbeat: {"type": "heartbeat", "timestamp": "..."}
    - pong: {"type": "pong"}
    """
    await ws_manager.connect(websocket)
    
    # Registrar callback no engine
    async def signal_callback(signal):
        await ws_manager.broadcast_signal(signal)
    
    signal_engine.add_signal_callback(signal_callback)
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # Timeout para heartbeat
                )
                
                message = json.loads(data)
                msg_type = message.get("type", "")
                
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                
                elif msg_type == "subscribe":
                    # Poderia implementar filtros específicos aqui
                    await websocket.send_json({
                        "type": "subscribed",
                        "filters": message
                    })
                
            except asyncio.TimeoutError:
                # Enviar heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "connections": ws_manager.connection_count
                })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
                
    except WebSocketDisconnect:
        pass
    finally:
        signal_engine.remove_signal_callback(signal_callback)
        await ws_manager.disconnect(websocket)


@router.websocket("/ws/signals")
async def signals_websocket(
    websocket: WebSocket,
    symbols: Optional[str] = Query(default=None),
    timeframes: Optional[str] = Query(default=None),
    strategies: Optional[str] = Query(default=None)
):
    """
    WebSocket com filtros via query params.
    
    Exemplo: /ws/signals?symbols=BTCUSDT,ETHUSDT&timeframes=1h,4h&strategies=GCM,RSI
    """
    # Parse query params
    symbol_list = symbols.split(",") if symbols else None
    tf_list = timeframes.split(",") if timeframes else None
    strat_list = strategies.split(",") if strategies else None
    
    await subscription_manager.subscribe(
        websocket, 
        symbols=symbol_list,
        timeframes=tf_list,
        strategies=strat_list
    )
    
    # Registrar callback filtrado
    async def filtered_callback(signal):
        await subscription_manager.broadcast_signal(signal)
    
    signal_engine.add_signal_callback(filtered_callback)
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat"})
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        pass
    finally:
        signal_engine.remove_signal_callback(filtered_callback)
        await subscription_manager.unsubscribe(websocket)
