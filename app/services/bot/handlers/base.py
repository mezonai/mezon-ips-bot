from abc import ABC, abstractmethod
from typing import Optional
import logging

from mezon.client import MezonClient
from mezon.models import InteractiveMessageProps, MessageActionRow
from mezon.protobuf.api import api_pb2
from mezon import ChannelMessageContent


class BaseMessageHandler(ABC):
    """Base class for all message handlers."""

    def __init__(self, client: MezonClient):
        self.client = client
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_command(self) -> str:
        """Return the command this handler responds to (e.g., '!hello')."""
        pass

    @abstractmethod
    async def handle(
        self, message: api_pb2.ChannelMessage, content: str
    ) -> Optional[str]:
        """
        Handle the message and return a response.

        Args:
            message: The channel message object
            content: The text content of the message

        Returns:
            Optional[str]: Response text to send, or None if no response
        """
        pass

    def should_handle(self, content: str) -> bool:
        """Check if this handler should process the message."""
        command = self.get_command()
        return content.startswith(command)

    async def send_ephemeral(
        self, message: api_pb2.ChannelMessage, response_text: str
    ) -> None:
        """Send an ephemeral message (only visible to the sender)."""
        try:
            channel = await self.client.channels.fetch(message.channel_id)
            await channel.send_ephemeral(
                receiver_id=message.sender_id,
                content=ChannelMessageContent(text=response_text),
            )
        except Exception as e:
            self.logger.error(f"Error sending ephemeral message: {e}")

    async def send_message(
        self, message: api_pb2.ChannelMessage, response_text: str = None, embeds: list[InteractiveMessageProps] = None, components: list[MessageActionRow] = None
    ) -> None:
        """Send a message to the channel."""
        try:
            channel = await self.client.channels.fetch(message.channel_id)
            await channel.send(content=ChannelMessageContent(text=response_text, embed=embeds, components=components))
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")

    async def reply_message(self, message: api_pb2.ChannelMessage, response_text: str = None, embeds: list[InteractiveMessageProps] = None, components: list[MessageActionRow] = None) -> None:
        """Reply to a message."""
        try:
            channel = await self.client.channels.fetch(message.channel_id)
            reply_message = await channel.messages.fetch(message.message_id)
            await reply_message.reply(content=ChannelMessageContent(text=response_text, embed=embeds, components=components))
        except Exception as e:
            self.logger.error(f"Error replying to message: {e}")