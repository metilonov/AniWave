from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.formatting import anime_text, list_text
from app.bot.keyboards import anime_keyboard
from app.services import Services

router = Router(name="anime")


@router.message(Command("anime"))
async def anime_search(message: Message, services: Services) -> None:
    query = (message.text or "").partition(" ")[2].strip()
    if not query:
        await message.answer("Использование: <code>/anime название</code>", parse_mode="HTML")
        return
    await message.bot.send_chat_action(message.chat.id, "typing")
    try:
        results = await services.anilist.search(query, 5)
    except Exception as exc:
        await message.answer(f"AniList временно недоступен: <code>{type(exc).__name__}</code>", parse_mode="HTML")
        return
    if not results:
        await message.answer("Ничего не найдено.")
        return
    anime = results[0]
    subs = await services.repo.list_subscriptions(message.chat.id)
    subscribed = any(x.anilist_id == anime.anilist_id for x in subs)
    text = anime_text(anime)
    kb = anime_keyboard(anime.anilist_id, subscribed)
    if anime.cover_url:
        await message.answer_photo(anime.cover_url, caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("top"))
async def top(message: Message, services: Services) -> None:
    items = await services.anilist.top(10)
    await message.answer(list_text("🏆 Топ AniList", items), parse_mode="HTML")


@router.message(Command("trending"))
async def trending(message: Message, services: Services) -> None:
    items = await services.anilist.trending(10)
    await message.answer(list_text("🔥 Сейчас в тренде", items), parse_mode="HTML")


@router.message(Command("season"))
async def season(message: Message, services: Services) -> None:
    items = await services.anilist.season_now(10)
    await message.answer(list_text("📺 Онгоинги сезона", items), parse_mode="HTML")
