from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.repository import Repository


class ChatRegistrationMiddleware(BaseMiddleware):
    """Registers every reachable private/group chat for global release broadcasts.

    Channels are never registered here. The one allowed channel is handled explicitly
    by ReleaseEngine; all other channels are rejected by the access router.
    """

    def __init__(self, repo: Repository, allowed_channel_id: int):
        self.repo = repo
        self.allowed_channel_id = allowed_channel_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        chat = None
        if isinstance(event, Message):
            chat = event.chat
        elif isinstance(event, CallbackQuery) and event.message:
            chat = event.message.chat

        if chat is not None:
            if chat.type in (ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP):
                await self.repo.register_broadcast_chat(chat.id)
            elif chat.type == ChatType.CHANNEL and chat.id != self.allowed_channel_id:
                bot: Bot = data["bot"]
                try:
                    await bot.leave_chat(chat.id)
                finally:
                    return None

        return await handler(event, data)
