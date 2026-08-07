import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import anime_keyboard
from app.services import Services

router = Router(name="subscriptions")


@router.callback_query(F.data.startswith("sub:"))
async def subscribe(callback: CallbackQuery, services: Services) -> None:
    anilist_id = int(callback.data.split(":", 1)[1])
    anime = await services.anilist.by_id(anilist_id)
    if not anime:
        await callback.answer("Тайтл не найден", show_alert=True)
        return
    created = await services.repo.add_subscription(callback.message.chat.id, anilist_id, anime.title)
    await callback.answer("Подписка создана" if created else "Уже подписаны")
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=anime_keyboard(anilist_id, True))


@router.callback_query(F.data.startswith("unsub:"))
async def unsubscribe(callback: CallbackQuery, services: Services) -> None:
    anilist_id = int(callback.data.split(":", 1)[1])
    removed = await services.repo.remove_subscription(callback.message.chat.id, anilist_id)
    await callback.answer("Подписка удалена" if removed else "Подписка уже отсутствует")
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=anime_keyboard(anilist_id, False))


@router.message(Command("subs"))
async def list_subs(message: Message, services: Services) -> None:
    items = await services.repo.list_subscriptions(message.chat.id)
    if not items:
        await message.answer("У этого чата пока нет подписок. Используйте /anime и кнопку «Подписаться».")
        return
    lines = ["🔔 <b>Подписки этого чата</b>", ""]
    for item in items:
        lines.append(f"• {html.escape(item.anime_title)} — <code>{item.anilist_id}</code>")
    lines.append("\nОткрыть тайтл: <code>/anime название</code>")
    await message.answer("\n".join(lines), parse_mode="HTML")
