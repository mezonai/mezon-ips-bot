from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.bot.handler_manager import HandlerManager
from app.services.bot.handlers.base import BaseMessageHandler, command


class DummyHandler(BaseMessageHandler):
    @command("*expert")
    async def handle_expert(self, message) -> None:
        return None

    @command("*program")
    async def handle_program(self, message) -> None:
        return None


@pytest.fixture
def dummy_handler():
    handler = DummyHandler(MagicMock())
    handler.reply_message = AsyncMock()
    return handler


@pytest.fixture
def mention_only_message():
    return SimpleNamespace(
        sender_id="user-1",
        content={"t": "<@bot-123>"},
        mentions=[SimpleNamespace(user_id="bot-123")],
    )


async def test_mention_without_command_shows_available_commands(
    dummy_handler, mention_only_message
):
    manager = HandlerManager([dummy_handler], client_id="bot-123")

    await manager.handle_channel_message(mention_only_message)

    dummy_handler.reply_message.assert_awaited_once()
    reply_text = dummy_handler.reply_message.await_args.args[1]
    assert "Các lệnh hiện có của bot" in reply_text
    assert "`*expert`" in reply_text
    assert "`*program`" in reply_text
