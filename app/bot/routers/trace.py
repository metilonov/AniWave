from __future__ import annotations

import io

from aiogram import Router
from aiogram.types import Message

from app.bot.formatting import seconds_to_timestamp
from app.bot.keyboards import anime_keyboard
from app.services import Services

router = Router(name="trace")


@router.message(lambda m: bool(m.photo))
async def trace_photo(message: Message, services: Services) -> None:
    if not message.photo:
        return
    await message.bot.send_chat_action(message.chat.id, "typing")
    buffer = io.BytesIO()
    await message.bot.download(message.photo[-1], destination=buffer)
    image = buffer.getvalue()
    try:
        results = await services.trace.search_bytes(image, "telegram-frame.jpg")
    except Exception as exc:
        await message.answer(f"Не удалось выполнить поиск по кадру: <code>{type(exc).__name__}</code>", parse_mode="HTML")
        return
    if not results:
        await message.answer("trace.moe не нашёл совпадений для этого кадра.")
        return
    best = results[0]
    if best.similarity < services.settings.trace_min_similarity:
        await message.answer(
            f"Совпадение слишком слабое: {best.similarity * 100:.1f}%. Попробуйте оригинальный кадр без рамок и сильных фильтров."
        )
        return
    title = best.title
    if best.anilist_id and title == "Неизвестное аниме":
        anime = await services.anilist.by_id(best.anilist_id)
        if anime:
            title = anime.title
    text = (
        f"🔎 <b>Похоже, найдено</b>\n\n"
        f"🎬 <b>{title}</b>\n"
        f"📺 Серия: <b>{best.episode}</b>\n"
        f"⏱ Таймкод: <b>{seconds_to_timestamp(best.from_seconds)}</b>\n"
        f"🎯 Совпадение: <b>{best.similarity * 100:.1f}%</b>"
    )
    kb = anime_keyboard(best.anilist_id) if best.anilist_id else None
    await message.answer(text, parse_mode="HTML", reply_markup=kb)
