from __future__ import annotations

import logging

from aiogram import Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import ChatMemberUpdated, Message

from app.services import Services

router = Router(name="access")
log = logging.getLogger(__name__)

_ACTIVE_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.RESTRICTED,
}
_INACTIVE_STATUSES = {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}


@router.my_chat_member()
async def enforce_membership(event: ChatMemberUpdated, services: Services) -> None:
    chat = event.chat
    status = event.new_chat_member.status

    if chat.type == ChatType.CHANNEL:
        if chat.id != services.settings.channel_id and status in _ACTIVE_STATUSES:
            log.info("Leaving unauthorized channel %s (%s)", chat.id, chat.title)
            await event.bot.leave_chat(chat.id)
        return

    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        if status in _ACTIVE_STATUSES:
            await services.repo.register_broadcast_chat(chat.id)
        elif status in _INACTIVE_STATUSES:
            await services.repo.disable_broadcast_chat(chat.id)


@router.channel_post()
async def reject_foreign_channel_posts(message: Message, services: Services) -> None:
    if message.chat.id != services.settings.channel_id:
        log.info("Received post from unauthorized channel %s; leaving", message.chat.id)
        await message.bot.leave_chat(message.chat.id)
