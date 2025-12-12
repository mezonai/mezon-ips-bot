from fastapi import APIRouter

from app.api.v1 import (
    health,
    bot,
)

health_router = APIRouter()
health_router.include_router(health.router, prefix="/health", tags=["health"])

bot_router = APIRouter()
bot_router.include_router(bot.router, prefix="/bot", tags=["bot"])
