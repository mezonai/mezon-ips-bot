import json
import logging
from typing import List
from mezon.protobuf.api import api_pb2

from .handlers.base import BaseMessageHandler


class HandlerManager:
    """Manages and routes messages to appropriate handlers."""

    def __init__(self, handlers: List[BaseMessageHandler], client_id: str):
        self.handlers = handlers
        self.client_id = client_id
        self.logger = logging.getLogger(__name__)

    async def handle_channel_message(self, message: api_pb2.ChannelMessage):
        """
        Main entry point for handling incoming channel messages.
        Routes messages to appropriate handlers.
        """
        if message.sender_id == self.client_id:
            return

        try:
            message_content = json.loads(message.content)
            content = message_content.get("t", "").strip()

            if not content:
                return


            for handler in self.handlers:
                if handler.should_handle(content):
                    self.logger.info(
                        f"Routing to {handler.__class__.__name__} for command: {handler.get_command()}"
                    )

                    response = await handler.handle(message, content)

        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse message content: {message.content}")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}", exc_info=True)
