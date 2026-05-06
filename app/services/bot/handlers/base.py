from __future__ import annotations

import logging
import types
from dataclasses import dataclass
from inspect import Parameter, signature
from typing import Any, Callable, Union, get_args, get_origin, get_type_hints

from mezon.client import MezonClient
from mezon.models import InteractiveMessageProps, MessageActionRow
from mezon.protobuf.api import api_pb2
from mezon import ChannelMessageContent

_COMMAND_ATTR = "_mezon_commands"


@dataclass(frozen=True)
class ArgInfo:
    name: str
    type: type
    required: bool
    default: Any


@dataclass(frozen=True)
class CommandInfo:
    method_name: str
    args: tuple[ArgInfo, ...]


def _base_type(ann: Any) -> type:
    """Unwrap Optional / Union to get the concrete type (e.g. str | None -> str)."""
    if isinstance(ann, type):
        return ann
    union_args: tuple[type, ...] | None = None
    if isinstance(ann, types.UnionType):
        union_args = ann.__args__
    elif get_origin(ann) is Union:
        union_args = get_args(ann)
    if union_args:
        for a in union_args:
            if a is not type(None):
                return a
    return str


def _build_args(fn: Callable) -> tuple[ArgInfo, ...]:
    """Introspect handler method signature to build argument metadata.

    Skips ``self`` and ``message`` (the first two parameters).
    The last ``str`` parameter automatically consumes all remaining tokens;
    ``int`` / ``float`` parameters always consume exactly one token each.
    """
    sig = signature(fn)
    params = list(sig.parameters.values())[2:]
    if not params:
        return ()

    try:
        hints = get_type_hints(fn)
    except Exception:
        hints = {}

    result: list[ArgInfo] = []
    for param in params:
        ann = hints.get(param.name, param.annotation)
        if ann is Parameter.empty:
            ann = str

        base = _base_type(ann)
        required = param.default is Parameter.empty
        default = None if required else param.default

        result.append(
            ArgInfo(
                name=param.name,
                type=base,
                required=required,
                default=default,
            )
        )

    return tuple(result)


def command(*cmds: str) -> Callable:
    """Register a method as the handler for one or more commands.

    Example::

        class MyHandler(BaseMessageHandler):
            @command("!ai", "!ask")
            async def handle_ai(self, message, prompt: str):
                ...
    """
    if not cmds:
        raise ValueError("@command requires at least one command string")

    def decorator(fn: Callable) -> Callable:
        setattr(fn, _COMMAND_ATTR, cmds)
        return fn

    return decorator


def parse_args(
    raw_content: str, cmd: str, args: tuple[ArgInfo, ...]
) -> dict[str, Any] | str:
    """Parse raw message content into keyword arguments.

    Returns a dict of kwargs on success, or an error message string on failure.
    """
    rest = (
        raw_content[len(cmd) :].strip()
        if raw_content.startswith(cmd)
        else raw_content.strip()
    )
    tokens = rest.split() if rest else []
    kwargs: dict[str, Any] = {}
    token_idx = 0
    last_idx = len(args) - 1

    for i, arg in enumerate(args):
        is_last_str = i == last_idx and arg.type is str

        if is_last_str:
            value = " ".join(tokens[token_idx:]) if token_idx < len(tokens) else ""
            token_idx = len(tokens)
            if not value:
                if arg.required:
                    return f"Missing required argument: `{arg.name}`"
                value = arg.default
        elif token_idx < len(tokens):
            raw = tokens[token_idx]
            token_idx += 1
            try:
                value = arg.type(raw)
            except (ValueError, TypeError):
                return (
                    f"Invalid value for `{arg.name}`: "
                    f"expected {arg.type.__name__}, got `{raw}`"
                )
        else:
            if arg.required:
                return f"Missing required argument: `{arg.name}`"
            value = arg.default

        kwargs[arg.name] = value

    return kwargs


class BaseMessageHandler:
    """Base class for all message handlers.

    Subclass and decorate methods with ``@command``.  Arguments declared in the
    method signature (after ``self`` and ``message``) are automatically parsed
    from the message content.
    """

    _command_map: dict[str, CommandInfo] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        mapping: dict[str, CommandInfo] = {}
        for klass in reversed(cls.__mro__):
            if klass is BaseMessageHandler:
                continue
            for name, method in vars(klass).items():
                registered = getattr(method, _COMMAND_ATTR, None)
                if registered is not None:
                    args = _build_args(method)
                    info = CommandInfo(method_name=name, args=args)
                    for cmd_str in registered:
                        mapping[cmd_str] = info
        cls._command_map = mapping

    def __init__(self, client: MezonClient) -> None:
        self.client = client
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_command_handlers(self) -> dict[str, CommandInfo]:
        """Command -> CommandInfo mapping, built from @command decorators."""
        return dict(self._command_map)

    async def send_ephemeral(
        self, message: api_pb2.ChannelMessage, response_text: str
    ) -> bool:
        """Send an ephemeral message (only visible to the sender). Returns True on success."""
        try:
            channel = await self.client.channels.fetch(message.channel_id)
            await channel.send_ephemeral(
                receiver_ids=[message.sender_id],
                content=ChannelMessageContent(text=response_text),
            )
            return True
        except Exception as e:
            self.logger.error("Failed to send ephemeral message: %s", e)
            return False

    async def send_message(
        self,
        message: api_pb2.ChannelMessage,
        response_text: str,
        embeds: list[InteractiveMessageProps] | None = None,
        components: list[MessageActionRow] | None = None,
    ) -> bool:
        """Send a message to the channel. Returns True on success."""
        try:
            channel = await self.client.channels.fetch(message.channel_id)
            await channel.send(
                content=ChannelMessageContent(
                    text=response_text, embed=embeds, components=components
                )
            )
            return True
        except Exception as e:
            self.logger.error("Failed to send message: %s", e)
            return False

    async def reply_message(
        self,
        message: api_pb2.ChannelMessage,
        response_text: str,
        embeds: list[InteractiveMessageProps] | None = None,
        components: list[MessageActionRow] | None = None,
    ) -> bool:
        """Reply to a message. Returns True on success."""
        try:
            channel = await self.client.channels.fetch(message.channel_id)
            reply_msg = await channel.messages.fetch(message.message_id)
            await reply_msg.reply(
                content=ChannelMessageContent(
                    text=response_text, embed=embeds, components=components
                )
            )
            return True
        except Exception as e:
            self.logger.error("Failed to reply to message: %s", e)
            return False

    async def edit_message(
        self,
        channel_id: int,
        message_id: int,
        response_text: str,
        embeds: list[InteractiveMessageProps] | None = None,
        components: list[MessageActionRow] | None = None,
    ) -> bool:
        """Edit an existing message (e.g. update form after submission)."""
        try:
            channel = await self.client.channels.fetch(channel_id)
            msg = await channel.messages.fetch(message_id)
            await msg.update(
                content=ChannelMessageContent(
                    text=response_text, embed=embeds, components=components
                )
            )
            return True
        except Exception as e:
            self.logger.error("Failed to edit message: %s", e)
            return False
