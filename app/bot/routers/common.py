from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.services import Services

router = Router(name="common")


@router.message(CommandStart())
async def start(message: Message, services: Services) -> None:
    if message.from_user:
        await services.repo.upsert_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
        )
    await message.answer(
        "🌊 <b>AniWave</b>\n\n"
        "Мониторинг аниме-релизов, база тайтлов и поиск аниме по кадру.\n\n"
        "<b>Команды:</b>\n"
        "/anime название — найти аниме\n"
        "/top — топ AniList\n"
        "/trending — тренды\n"
        "/season — онгоинги сезона\n"
        "/subs — мои подписки\n"
        "/help — помощь\n\n"
        "Также можно просто отправить скриншот из аниме — я попробую определить тайтл, серию и таймкод.\n\nКоманды работают также в группах и супергруппах.",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "<b>AniWave — помощь</b>\n\n"
        "1) <code>/anime Frieren</code> — карточка аниме.\n"
        "2) Нажмите «Подписаться» — новые найденные релизы этого тайтла будут приходить в текущий чат.\n"
        "3) Отправьте фото/скриншот — поиск через trace.moe.\n"
        "4) <code>/subs</code> — управление подписками.\n\n"
        "Монитор релизов работает в фоне. Первый запуск каждого источника создаёт базовую точку и не рассылает старые серии.",
        parse_mode="HTML",
    )
