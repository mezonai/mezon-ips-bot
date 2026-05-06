from app.services.llm.service import LLMService
from dependency_injector import containers, providers
from mezon.client import MezonClient
import logging

from app.core.settings.app import app_settings
from app.database.connect import async_session_factory
from app.database.repositories.gold_price import GoldPriceRepository
from app.database.repositories.professional import ProfessionalRepository
from app.services.bot.service import MezonBotService
from app.services.bot.handler_manager import HandlerManager
from app.services.bot.handlers import GoldPriceHandler
from app.services.bot.handlers.llm import LLMHandler
from app.services.bot.handlers.professional import ProfessionalHandler
from app.services.gold_price.service import GoldPriceService
from app.services.professional.service import ProfessionalService


class Container(containers.DeclarativeContainer):
    """Dependency injection container for the application."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.v1.health",
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
        log_level=logging.DEBUG,
    )

    # Repositories
    gold_price_repository = providers.Singleton(
        GoldPriceRepository,
        session_factory=db_session_factory,
    )

    professional_repository = providers.Singleton(
        ProfessionalRepository,
        session_factory=db_session_factory,
    )

    # Services
    gold_price_service = providers.Singleton(
        GoldPriceService,
        gold_price_repository=gold_price_repository,
    )
    llm_service = providers.Singleton(
        LLMService,
    )
    professional_service = providers.Singleton(
        ProfessionalService,
        professional_repository=professional_repository,
    )

    mezon_bot_service = providers.Factory(
        MezonBotService,
        settings=app_settings,
        mezon_client=mezon_client,
        gold_price_service=gold_price_service,
        llm_service=llm_service,
    )

    # Handlers
    gold_price_handler = providers.Singleton(
        GoldPriceHandler,
        client=mezon_client,
        gold_price_service=gold_price_service,
    )

    llm_handler = providers.Singleton(
        LLMHandler,
        client=mezon_client,
        llm_service=llm_service,
    )

    professional_handler = providers.Singleton(
        ProfessionalHandler,
        client=mezon_client,
        professional_service=professional_service,
    )

    handler_manager = providers.Singleton(
        HandlerManager,
        handlers=providers.List(
            gold_price_handler,
            llm_handler,
            professional_handler,
        ),
        client_id=app_settings.mezon_client_id,
        require_mention=app_settings.mezon_bot_require_mention,
    )
