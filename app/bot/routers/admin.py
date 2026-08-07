from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services import Services

router = Router(name="admin")


@router.message(Command("providers"))
async def providers(message: Message, services: Services) -> None:
    if not message.from_user or message.from_user.id not in services.settings.admins:
        return
    states = await services.repo.provider_states()
    if not states:
        await message.answer("Состояния провайдеров ещё не созданы.")
        return
    lines = ["🧩 <b>Провайдеры AniWave</b>", ""]
    for s in states:
        icon = "✅" if s.last_error is None and s.last_ok_at else "⚠️"
        init = "ready" if s.initialized else "baseline"
        lines.append(f"{icon} <code>{s.provider}</code> — {init}, seen={s.seen_count}")
        if s.last_error:
            lines.append(f"   ↳ <code>{s.last_error[:180]}</code>")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("scan"))
async def scan(message: Message, services: Services) -> None:
    if not message.from_user or message.from_user.id not in services.settings.admins:
        return
    await message.answer("Запускаю внеочередной цикл мониторинга…")
    await services.monitor.cycle()
    await message.answer("Цикл завершён. /providers покажет состояние источников.")


@router.message(Command("status"))
async def status(message: Message, services: Services) -> None:
    if not message.from_user or message.from_user.id not in services.settings.admins:
        return
    chats = await services.repo.broadcast_chat_ids()
    await message.answer(
        "🌊 <b>AniWave status</b>\n\n"
        f"👑 ADMIN_ID: <code>{services.settings.admin_id}</code>\n"
        f"📢 CHANNEL_ID: <code>{services.settings.channel_id}</code>\n"
        f"💬 Чатов рассылки: <b>{len(chats)}</b>\n"
        f"🔎 Кнопка поиска: <code>{services.settings.anime_search_url}</code>",
        parse_mode="HTML",
    )
