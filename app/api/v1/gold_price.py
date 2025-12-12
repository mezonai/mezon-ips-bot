from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.settings.app import app_settings

router = APIRouter()


@router.get(
    path="",
    name="gold_price:get",
)
async def get_gold_price():
    return JSONResponse(
        status_code=200,
        content={"status": "ok"},
    )
