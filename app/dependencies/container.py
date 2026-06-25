from dependency_injector import containers, providers
from mezon.client import MezonClient
import logging

from app.core.settings.app import app_settings
from app.database.connect import async_session_factory
from app.database.repositories.expert import ExpertRepository
from app.database.repositories.contract import ContractRepository
from app.database.repositories.program import ProgramRepository
from app.services.bot.service import MezonBotService
from app.services.bot.handler_manager import HandlerManager
from app.services.bot.handlers.expert import ExpertHandler
from app.services.bot.handlers.program import ProgramHandler
from app.services.expert.service import ExpertService
from app.services.contract.service import ContractService
from app.services.program.service import ProgramService
from app.services.word_export import WordExportService
from app.services.smb_upload import SMBUploadService


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
    expert_repository = providers.Singleton(
        ExpertRepository,
        session_factory=db_session_factory,
    )

    contract_repository = providers.Singleton(
        ContractRepository,
        session_factory=db_session_factory,
    )

    program_repository = providers.Singleton(
        ProgramRepository,
        session_factory=db_session_factory,
    )

    # Services
    expert_service = providers.Singleton(
        ExpertService,
        expert_repository=expert_repository,
    )
    program_service = providers.Singleton(
        ProgramService,
        program_repository=program_repository,
    )
    contract_service = providers.Singleton(
        ContractService,
        contract_repository=contract_repository,
        program_repository=program_repository,
    )
    word_export_service = providers.Singleton(
        WordExportService,
    )

    smb_upload_service = providers.Singleton(
        SMBUploadService,
        share_path=app_settings.smb_share_path,
        public_url_base=app_settings.smb_public_url_base,
    )

    mezon_bot_service = providers.Factory(
        MezonBotService,
        settings=app_settings,
        mezon_client=mezon_client,
    )

    # Handlers
    expert_handler = providers.Singleton(
        ExpertHandler,
        client=mezon_client,
        expert_service=expert_service,
        contract_service=contract_service,
        program_service=program_service,
        word_export_service=word_export_service,
        smb_upload_service=smb_upload_service,
    )

    program_handler = providers.Singleton(
        ProgramHandler,
        client=mezon_client,
        program_service=program_service,
        contract_service=contract_service,
    )

    handler_manager = providers.Singleton(
        HandlerManager,
        handlers=providers.List(
            expert_handler,
            program_handler,
        ),
        client_id=app_settings.mezon_client_id,
        require_mention=app_settings.mezon_bot_require_mention,
    )
