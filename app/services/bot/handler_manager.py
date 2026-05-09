from __future__ import annotations

import json
import logging
import re

from mezon.protobuf.api import api_pb2
from mezon.protobuf.rtapi import realtime_pb2

from .handlers.base import BaseMessageHandler, CommandInfo, parse_args
from .handlers.expert import ExpertHandler
from .handlers.program import ProgramHandler


COMMAND_PREFIXS = "*!/@"


class HandlerManager:
    """Manages and routes messages to handlers. O(1) lookup via command -> (handler, info)."""

    def __init__(
        self,
        handlers: list[BaseMessageHandler],
        client_id: str,
        require_mention: bool = False,
    ) -> None:
        self.client_id = client_id
        self.require_mention = require_mention
        self.logger = logging.getLogger(__name__)
        self._command_map: dict[str, tuple[BaseMessageHandler, CommandInfo]] = {}
        for handler in handlers:
            for cmd, info in handler.get_command_handlers().items():
                if cmd in self._command_map:
                    self.logger.warning("Duplicate command %r, first handler wins", cmd)
                    continue
                self._command_map[cmd] = (handler, info)

        self._alias_map: dict[str, str] = {}
        for cmd in self._command_map:
            alias = cmd.lstrip(COMMAND_PREFIXS)
            if alias and alias != cmd:
                self._alias_map[alias] = cmd

    def _is_bot_mentioned(self, message: api_pb2.ChannelMessage) -> bool:
        """
        Check if the bot is among the message mentions.
        """
        mentions = message.mentions

        if not mentions:
            return False

        for mention in mentions:
            mention_id = mention.user_id
            if str(mention_id) == str(self.client_id):
                return True

        return False

    def _strip_mention(self, content: str) -> str:
        """Remove mention tokens from the beginning of message text.

        Mezon formats:  <@user_id>  or  @username
        Also strips leading whitespace after the mention.
        """
        content = re.sub(r"^(<@[^>]+>\s*)+", "", content)
        content = re.sub(r"^(@\S+\s*)+", "", content)
        return content.strip()

    async def handle_channel_message(self, message: api_pb2.ChannelMessage) -> None:
        """Route message to the registered handler for the command."""
        if message.sender_id == self.client_id:
            return

        try:
            message_content = message.content
            content: str = message_content.get("t", "").strip()
            if not content:
                return

            is_mentioned = self._is_bot_mentioned(message)
            if is_mentioned:
                content = self._strip_mention(content)
                if not content:
                    return
            elif self.require_mention:
                self.logger.debug(
                    "Skipping message – bot not mentioned and require_mention=True: %r",
                    content,
                )
                return

            cmd = content.split(maxsplit=1)[0]
            entry = self._command_map.get(cmd)
            parse_cmd = cmd

            if not entry and is_mentioned:
                aliased_cmd = self._alias_map.get(cmd)
                if aliased_cmd:
                    entry = self._command_map.get(aliased_cmd)
                    parse_cmd = cmd

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
                result = parse_args(content, parse_cmd, info.args)
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

    async def handle_button_click(
        self, event: realtime_pb2.MessageButtonClicked
    ) -> None:
        """Route button click events to the appropriate handler."""
        try:
            # Try each handler that supports button clicks
            for handler in self._command_map.values():
                h = handler[0]
                if (isinstance(h, (ExpertHandler, ProgramHandler)) and
                    hasattr(h, "handle_button_click")):
                    await h.handle_button_click(event)
                    # Continue to next handler - they will return early if not handling
        except Exception as e:
            self.logger.error("Error handling button click: %s", e, exc_info=True)
