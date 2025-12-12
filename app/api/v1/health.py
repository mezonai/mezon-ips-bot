from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.settings.app import app_settings

router = APIRouter()


@router.get(
    path="",
    name="health:check",
)
async def health_check():
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "version": app_settings.version},
    )
