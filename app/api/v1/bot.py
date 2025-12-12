from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from app.dependencies.container import Container
from app.services.bot.service import MezonBotService

router = APIRouter(tags=["bot"])


@router.get("/status")
@inject
async def bot_status(
    bot_service: MezonBotService = Depends(Provide[Container.mezon_bot_service]),
):
    """Example endpoint showing how to inject MezonBotService with the initialized MezonClient."""
    return {
        "status": "connected",
        "client_initialized": bot_service.mezon_client is not None,
    }
