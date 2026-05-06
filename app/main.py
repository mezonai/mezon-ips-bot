import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings.app import app_settings
from app.api.v1 import health_router, bot_router
from app.dependencies.container import Container

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = Container()
    container.wire(modules=container.wiring_config.modules)

    mezon_client = container.mezon_client()
    await mezon_client.login()

    handler_manager = container.handler_manager()
    mezon_client.on_channel_message(handler_manager.handle_channel_message)
    mezon_client.on_message_button_clicked(handler_manager.handle_button_click)

    app.state.container = container
    app.state.mezon_client = mezon_client
    app.state.handler_manager = handler_manager

    yield

    await mezon_client.disconnect()


def create_app() -> FastAPI:
    app = FastAPI(
        title=app_settings.app_name,
        openapi_url=f"{app_settings.api_v1_prefix}/openapi.json"
        if app_settings.app_env == "dev"
        else None,
        lifespan=lifespan,
    )

    app.include_router(health_router, prefix=app_settings.api_v1_prefix)
    app.include_router(bot_router, prefix=app_settings.api_v1_prefix)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()
