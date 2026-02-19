from __future__ import annotations

from mezon.protobuf.api import api_pb2

from .base import BaseMessageHandler, command
from app.services.gold_price.service import GoldPriceService


class GoldPriceHandler(BaseMessageHandler):
    """Handler for *gold command to get gold prices."""

    def __init__(self, client, gold_price_service: GoldPriceService):
        super().__init__(client)
        self.gold_price_service = gold_price_service

    def _format_price(self, price: float) -> str:
        """Format price to Vietnamese currency format."""
        return f"{price:,.0f}".replace(",", ".")

    @command("*gold")
    async def handle_gold(
        self, message: api_pb2.ChannelMessage, gold_type: str | None = None, location: str | None = None, date: str | None = None
    ) -> None:
        """Get today's gold prices.

        Usage:
            *gold           - all prices
            *gold SJC       - specific type
        """
        try:
            if gold_type:
                # Get specific gold type price
                gold_price = await self.gold_price_service.get_gold_price_by_type(
                    gold_type=gold_type
                )

                if gold_price is None:
                    response = f"❌ Không tìm thấy giá vàng {gold_type}. Vui lòng thử loại khác."
                else:
                    price_date = gold_price.date.strftime("%d/%m/%Y")
                    response = f"💰 Giá vàng {gold_type} ({price_date}):\n"
                    response += f"Mua vào: {self._format_price(gold_price.buy_price)} VNĐ\n"
                    response += f"Bán ra: {self._format_price(gold_price.sell_price)} VNĐ"
            else:
                gold_prices = await self.gold_price_service.get_all_gold_prices()

                if not gold_prices:
                    gold_prices = await self.gold_price_service.get_latest_gold_prices()

                if not gold_prices:
                    response = "❌ Không có dữ liệu giá vàng. Vui lòng thử lại sau."
                else:
                    price_date = gold_prices[0].date.strftime("%d/%m/%Y")
                    location = gold_prices[0].location
                    response = f"💰 Giá vàng {location} ({price_date}):\n\n"

                    for gp in gold_prices:
                        response += f"**{gp.gold_type}:**\n"
                        response += f"  Mua: {self._format_price(gp.buy_price)} VNĐ\n"
                        response += (
                            f"  Bán: {self._format_price(gp.sell_price)} VNĐ\n\n"
                        )

                    response += (
                        "Sử dụng `*gold [loại]` để xem giá cụ thể (VD: *gold SJC)"
                    )

            await self.reply_message(message, response)

        except Exception as e:
            self.logger.error("Error in GoldPriceHandler: %s", e)
            await self.send_message(
                message, "❌ Không thể lấy giá vàng. Vui lòng thử lại sau."
            )
