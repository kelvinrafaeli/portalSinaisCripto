"""
Portal Sinais - Telegram API Routes
Configuração e teste de integração Telegram.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.telegram import telegram_service

router = APIRouter(prefix="/telegram", tags=["Telegram"])


class TelegramConfig(BaseModel):
    """Configuração do Telegram"""
    bot_token: str
    chat_id: str


class TestMessage(BaseModel):
    """Mensagem de teste"""
    message: str = "🚀 Portal Sinais - Teste de conexão!"
    include_disclaimer: bool = True


@router.get("/status")
async def get_telegram_status():
    """Retorna status da integração Telegram"""
    return {
        "enabled": telegram_service.is_enabled,
        "configured": bool(telegram_service.bot_token and telegram_service.chat_id)
    }


@router.post("/configure")
async def configure_telegram(config: TelegramConfig):
    """
    Configura credenciais do Telegram.
    
    - **bot_token**: Token do bot (obtido do @BotFather)
    - **chat_id**: ID do chat/grupo (pode ser negativo para grupos)
    """
    telegram_service.configure(config.bot_token, config.chat_id)
    
    return {
        "status": "configured",
        "enabled": telegram_service.is_enabled
    }


@router.post("/test")
async def test_telegram(test: TestMessage = None):
    """
    Envia mensagem de teste para o Telegram.
    
    Útil para verificar se a configuração está correta.
    """
    if not telegram_service.is_enabled:
        raise HTTPException(
            status_code=400,
            detail="Telegram não está configurado. Use /api/v1/telegram/configure primeiro."
        )
    
    message = test.message if test else "🚀 Portal Sinais - Teste de conexão!"
    include_disclaimer = test.include_disclaimer if test else True
    
    success = await telegram_service.send_message(
        message,
        include_disclaimer=include_disclaimer
    )
    
    if success:
        return {"status": "sent", "message": message}
    else:
        raise HTTPException(
            status_code=500,
            detail="Falha ao enviar mensagem. Verifique o token e chat_id."
        )


@router.post("/disable")
async def disable_telegram():
    """Desativa temporariamente o envio para Telegram"""
    telegram_service._enabled = False
    return {"status": "disabled"}


@router.post("/enable")
async def enable_telegram():
    """Reativa o envio para Telegram (se configurado)"""
    if telegram_service.bot_token and telegram_service.chat_id:
        telegram_service._enabled = True
        return {"status": "enabled"}
    else:
        raise HTTPException(
            status_code=400,
            detail="Telegram não está configurado."
        )
