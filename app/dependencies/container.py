from dependency_injector import containers, providers
from mezon.client import MezonClient
import logging

from app.core.settings.app import app_settings
from app.database.connect import async_session_factory
from app.database.repositories.gold_price import GoldPriceRepository
from app.services.bot.service import MezonBotService
from app.services.bot.handler_manager import HandlerManager
from app.services.bot.handlers import GoldPriceHandler
from app.services.gold_price.service import GoldPriceService


class Container(containers.DeclarativeContainer):
    """Dependency injection container for the application."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.v1.health",
            "app.api.v1.gold_price",
            "app.api.v1.bot",
        ]
    )

    config = providers.Configuration()

    # Database session factory (callable that returns a session)
    db_session_factory = providers.Object(async_session_factory)

    mezon_client = providers.Singleton(
        MezonClient,
        client_id=app_settings.mezon_client_id,
        api_key=app_settings.mezon_api_key,
        enable_logging=True,
        log_level=logging.INFO,
    )

    # Repositories
    gold_price_repository = providers.Singleton(
        GoldPriceRepository,
        session_factory=db_session_factory,
    )

    # Services
    gold_price_service = providers.Singleton(
        GoldPriceService,
        gold_price_repository=gold_price_repository,
    )

    mezon_bot_service = providers.Factory(
        MezonBotService,
        settings=app_settings,
        mezon_client=mezon_client,
        gold_price_service=gold_price_service,
    )

    # Handlers
    gold_price_handler = providers.Singleton(
        GoldPriceHandler,
        client=mezon_client,
        gold_price_service=gold_price_service,
    )

    handler_manager = providers.Singleton(
        HandlerManager,
        handlers=providers.List(
            gold_price_handler,
        ),
        client_id=app_settings.mezon_client_id,
    )
