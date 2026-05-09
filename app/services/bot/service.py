from mezon.client import MezonClient
from app.core.settings.app import AppSettings


class MezonBotService:
    def __init__(
        self,
        settings: AppSettings,
        mezon_client: MezonClient,
    ):
        self.mezon_client = mezon_client
