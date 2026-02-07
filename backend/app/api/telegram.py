"""
Portal Alertas - Telegram API Routes
Configuração e teste de integração Telegram.
Suporta grupos individuais por estratégia.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict

from app.services.telegram import telegram_service

router = APIRouter(prefix="/telegram", tags=["Telegram"])


class TelegramConfig(BaseModel):
    """Configuração do Telegram"""
    bot_token: str
    chat_id: str = ""  # Chat padrão (opcional)


class StrategyGroupConfig(BaseModel):
    """Configuração de grupo por estratégia"""
    strategy: str
    chat_id: str


class SummaryGroupConfig(BaseModel):
    """Configuração de grupo para resumo"""
    chat_id: str


class TestMessage(BaseModel):
    """Mensagem de teste"""
    message: str = "🚀 Portal Alertas - Teste de conexão!"
    include_disclaimer: bool = True
    strategy: Optional[str] = None  # Testar grupo específico de estratégia


@router.get("/status")
async def get_telegram_status():
    """Retorna status da integração Telegram"""
    # Mascarar token e chat_id para segurança
    masked_token = ""
    masked_chat = ""
    
    if telegram_service.bot_token:
        token = telegram_service.bot_token
        if len(token) > 10:
            masked_token = token[:5] + "..." + token[-4:]
        else:
            masked_token = "****"
            
    if telegram_service.chat_id:
        chat = telegram_service.chat_id
        if len(chat) > 6:
            masked_chat = chat[:4] + "..." + chat[-3:]
        else:
            masked_chat = chat
    
    # Mascarar grupos de estratégias
    masked_groups = {}
    for strategy, chat_id in telegram_service.get_all_strategy_groups().items():
        if len(chat_id) > 6:
            masked_groups[strategy] = chat_id[:4] + "..." + chat_id[-3:]
        else:
            masked_groups[strategy] = chat_id

    summary_group = telegram_service.get_summary_group()
    if summary_group:
        if len(summary_group) > 6:
            masked_summary = summary_group[:4] + "..." + summary_group[-3:]
        else:
            masked_summary = summary_group
    else:
        masked_summary = ""
    
    return {
        "enabled": telegram_service.is_enabled,
        "configured": bool(telegram_service.bot_token),
        "masked_token": masked_token,
        "masked_chat_id": masked_chat,
        "strategy_groups": masked_groups,
        "masked_summary_group": masked_summary
    }


@router.post("/configure")
async def configure_telegram(config: TelegramConfig):
    """
    Configura credenciais do Telegram.
    
    - **bot_token**: Token do bot (obtido do @BotFather)
    - **chat_id**: ID do chat/grupo padrão (opcional, pode ser negativo para grupos)
    """
    telegram_service.configure(config.bot_token, config.chat_id)
    
    return {
        "status": "configured",
        "enabled": telegram_service.is_enabled
    }


@router.post("/strategy-group")
async def configure_strategy_group(config: StrategyGroupConfig):
    """
    Configura grupo específico para uma estratégia.
    
    - **strategy**: Nome da estratégia (ex: GCM, RSI, MACD)
    - **chat_id**: ID do grupo/chat para essa estratégia
    """
    telegram_service.configure_strategy_group(config.strategy, config.chat_id)
    
    return {
        "status": "configured",
        "strategy": config.strategy.upper(),
        "chat_id": config.chat_id[:4] + "..." if len(config.chat_id) > 4 else config.chat_id
    }


@router.delete("/strategy-group/{strategy}")
async def remove_strategy_group(strategy: str):
    """Remove a configuração de grupo para uma estratégia"""
    telegram_service.remove_strategy_group(strategy)
    
    return {
        "status": "removed",
        "strategy": strategy.upper()
    }


@router.post("/summary-group")
async def configure_summary_group(config: SummaryGroupConfig):
    """Configura grupo para envio do resumo CryptoBubbles"""
    telegram_service.configure_summary_group(config.chat_id)

    return {
        "status": "configured",
        "summary_group": config.chat_id[:4] + "..." if len(config.chat_id) > 4 else config.chat_id
    }


@router.get("/strategy-groups")
async def get_strategy_groups():
    """Retorna todos os grupos configurados por estratégia"""
    groups = telegram_service.get_all_strategy_groups()
    
    # Mascarar chat_ids
    masked_groups = {}
    for strategy, chat_id in groups.items():
        if len(chat_id) > 6:
            masked_groups[strategy] = chat_id[:4] + "..." + chat_id[-3:]
        else:
            masked_groups[strategy] = chat_id
    
    return {
        "groups": masked_groups,
        "count": len(groups)
    }


@router.post("/test")
async def test_telegram(test: TestMessage = None):
    """
    Envia mensagem de teste para o Telegram.
    
    Útil para verificar se a configuração está correta.
    Se strategy for fornecida, testa o grupo dessa estratégia.
    """
    if not telegram_service.is_enabled:
        raise HTTPException(
            status_code=400,
            detail="Telegram não está configurado. Use /api/v1/telegram/configure primeiro."
        )
    
    message = test.message if test else "🚀 Portal Alertas - Teste de conexão!"
    include_disclaimer = test.include_disclaimer if test else True
    
    # Determinar chat_id baseado na estratégia ou usar o padrão
    chat_id = None
    if test and test.strategy:
        chat_id = telegram_service.get_strategy_group(test.strategy)
        if not chat_id:
            raise HTTPException(
                status_code=400,
                detail=f"Nenhum grupo configurado para a estratégia {test.strategy}"
            )
    elif not telegram_service.chat_id:
        raise HTTPException(
            status_code=400,
            detail="Nenhum grupo padrao configurado. Configure um grupo por estrategia antes de testar."
        )
    
    try:
        success = await telegram_service.send_message(
            message,
            chat_id=chat_id,
            include_disclaimer=include_disclaimer
        )
        
        if success:
            return {"status": "sent", "message": message, "strategy": test.strategy if test else None}
        else:
            raise HTTPException(
                status_code=500,
                detail="Falha ao enviar mensagem. Verifique o token e chat_id."
            )
    except Exception as e:
        error_msg = str(e)
        if "DNS" in error_msg or "connect" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail="Erro de conexão: não foi possível conectar ao Telegram. Verifique sua conexão de internet/DNS."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao enviar: {error_msg}"
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
