from __future__ import annotations

import json
import logging

from mezon.protobuf.api import api_pb2

from .handlers.base import BaseMessageHandler, CommandInfo, parse_args


class HandlerManager:
    """Manages and routes messages to handlers. O(1) lookup via command -> (handler, info)."""

    def __init__(self, handlers: list[BaseMessageHandler], client_id: str) -> None:
        self.client_id = client_id
        self.logger = logging.getLogger(__name__)
        self._command_map: dict[str, tuple[BaseMessageHandler, CommandInfo]] = {}
        for handler in handlers:
            for cmd, info in handler.get_command_handlers().items():
                if cmd in self._command_map:
                    self.logger.warning("Duplicate command %r, first handler wins", cmd)
                    continue
                self._command_map[cmd] = (handler, info)

    async def handle_channel_message(self, message: api_pb2.ChannelMessage) -> None:
        """Route message to the registered handler for the command."""
        if message.sender_id == self.client_id:
            return

        try:
            message_content = message.content
            content: str = message_content.get("t", "").strip()
            if not content:
                return

            cmd = content.split(maxsplit=1)[0]
            entry = self._command_map.get(cmd)
            if not entry:
                return

            handler, info = entry
            self.logger.info(
                "Routing to %s.%s for command: %s",
                handler.__class__.__name__,
                info.method_name,
                cmd,
            )
            method = getattr(handler, info.method_name)

            if info.args:
                result = parse_args(content, cmd, info.args)
                if isinstance(result, str):
                    await handler.reply_message(message, f"❌ {result}")
                    return
                await method(message, **result)
            else:
                await method(message)

        except json.JSONDecodeError:
            self.logger.error("Failed to parse message content: %s", message.content)
        except Exception as e:
            self.logger.error("Error handling message: %s", e, exc_info=True)
