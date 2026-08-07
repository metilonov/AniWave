from __future__ import annotations

import html
from datetime import datetime, timezone

from app.schemas import AnimeCard


def short_description(text: str | None, limit: int = 600) -> str:
    if not text:
        return "Описание отсутствует."
    value = " ".join(text.split())
    if len(value) > limit:
        value = value[: limit - 1].rstrip() + "…"
    return html.escape(value)


def anime_text(anime: AnimeCard) -> str:
    lines = [f"🎬 <b>{html.escape(anime.title)}</b>"]
    if anime.title_native and anime.title_native != anime.title:
        lines.append(f"🇯🇵 {html.escape(anime.title_native)}")
    meta: list[str] = []
    if anime.season_year:
        meta.append(str(anime.season_year))
    if anime.format:
        meta.append(anime.format)
    if anime.episodes:
        meta.append(f"{anime.episodes} эп.")
    if meta:
        lines.append("📅 " + " • ".join(meta))
    if anime.score:
        lines.append(f"⭐ AniList: {anime.score / 10:.1f}/10")
    if anime.genres:
        lines.append("🎭 " + ", ".join(html.escape(x) for x in anime.genres[:6]))
    if anime.next_episode and anime.next_airing_at:
        dt = datetime.fromtimestamp(anime.next_airing_at, tz=timezone.utc)
        lines.append(f"⏱ Следующая серия: {anime.next_episode} — {dt:%d.%m.%Y %H:%M} UTC")
    lines.append("")
    lines.append(short_description(anime.description))
    if anime.site_url:
        lines.append(f'\n🔗 <a href="{html.escape(anime.site_url, quote=True)}">AniList</a>')
    return "\n".join(lines)


def list_text(title: str, items: list[AnimeCard]) -> str:
    lines = [f"<b>{html.escape(title)}</b>", ""]
    for i, anime in enumerate(items, 1):
        score = f" — ⭐ {anime.score / 10:.1f}" if anime.score else ""
        lines.append(f"{i}. <b>{html.escape(anime.title)}</b>{score}")
    return "\n".join(lines)


def seconds_to_timestamp(value: float) -> str:
    total = max(0, int(value))
    return f"{total // 60:02d}:{total % 60:02d}"
