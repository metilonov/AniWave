from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def anime_keyboard(anilist_id: int, subscribed: bool = False) -> InlineKeyboardMarkup:
    action = "unsub" if subscribed else "sub"
    label = "🔕 Отписаться" if subscribed else "🔔 Подписаться"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"{action}:{anilist_id}")],
            [InlineKeyboardButton(text="🌐 AniList", url=f"https://anilist.co/anime/{anilist_id}")],
        ]
    )


def release_search_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Найти аниме", url=url)]]
    )
