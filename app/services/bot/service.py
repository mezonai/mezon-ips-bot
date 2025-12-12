from mezon.client import MezonClient
from app.core.settings.app import AppSettings
from app.services.gold_price.service import GoldPriceService

class MezonBotService:
    def __init__(self, settings: AppSettings, mezon_client: MezonClient, gold_price_service: GoldPriceService):
        self.mezon_client = mezon_client
        self.gold_price_service = gold_price_service
    