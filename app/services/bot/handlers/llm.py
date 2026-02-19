from __future__ import annotations

from mezon.protobuf.api import api_pb2

from .base import BaseMessageHandler, command
from app.services.llm.service import LLMService


class LLMHandler(BaseMessageHandler):
    """Handle !hello and !ai via @command registration."""

    def __init__(self, client, llm_service: LLMService):
        super().__init__(client)
        self.llm_service = llm_service

    @command("!hello")
    async def handle_hello(self, message: api_pb2.ChannelMessage) -> None:
        """Handle !hello command."""
        await self.reply_message(message, "Hi there!")

    @command("!ai")
    async def handle_ai(self, message: api_pb2.ChannelMessage, prompt: str) -> None:
        try:
            response = await self.llm_service.generate_response(prompt)
            await self.reply_message(message, response)
        except Exception as e:
            self.logger.error("Error in LLM handler: %s", e)
            await self.reply_message(
                message, "❌ Không thể xử lý. Vui lòng thử lại sau."
            )

    @command("*ai")
    async def handle_ai_default(self, message: api_pb2.ChannelMessage, prompt: str) -> None:
        if not prompt:
            await self.send_ephemeral(message, "Vui lòng nhập prompt. Ví dụ: `!ai Hello`")
            return
        try:
            response = await self.llm_service.generate_response(prompt)
            await self.reply_message(message, response)
        except Exception as e:
            self.logger.error("Error in LLM handler: %s", e)
            await self.reply_message(message, "❌ Không thể xử lý. Vui lòng thử lại sau.")
