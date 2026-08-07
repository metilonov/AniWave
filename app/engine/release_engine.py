from __future__ import annotations

import hashlib
import html
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.bot.keyboards import release_search_keyboard
from app.engine.matcher import AnimeMatcher
from app.engine.normalizer import canonical_dub_team, display_episode, normalize_title
from app.repository import Repository
from app.schemas import CanonicalRelease, RawRelease

log = logging.getLogger(__name__)


class ReleaseEngine:
    def __init__(
        self,
        repo: Repository,
        matcher: AnimeMatcher,
        bot: Bot,
        channel_id: int,
        anime_search_url: str,
    ):
        self.repo = repo
        self.matcher = matcher
        self.bot = bot
        self.channel_id = channel_id
        self.anime_search_url = anime_search_url

    @staticmethod
    def _fingerprint(anilist_id: int | None, title: str, episode: float | None, dub_team: str | None) -> str:
        canonical = "|".join(
            [
                str(anilist_id or normalize_title(title)),
                str(episode if episode is not None else "?"),
                canonical_dub_team(dub_team),
            ]
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    async def canonicalize(self, raw: RawRelease) -> CanonicalRelease:
        match = await self.matcher.match(raw.title_raw)
        anime = match.anime
        anime_title = anime.title if anime else raw.title_raw
        anilist_id = anime.anilist_id if anime else None
        fingerprint = self._fingerprint(anilist_id, anime_title, raw.episode, raw.dub_team)
        return CanonicalRelease(
            fingerprint=fingerprint,
            provider=raw.provider,
            provider_release_id=raw.provider_release_id,
            title_raw=raw.title_raw,
            title_normalized=normalize_title(raw.title_raw),
            anilist_id=anilist_id,
            anime_title=anime_title,
            episode=raw.episode,
            dub_team=raw.dub_team,
            source_url=raw.source_url,
            confidence=match.confidence,
            published_at=raw.published_at,
            cover_url=anime.cover_url if anime else None,
        )

    def format_release(self, release: CanonicalRelease) -> str:
        """Single publication format used in the main channel and every broadcast chat."""
        title = html.escape(release.anime_title)
        episode = html.escape(display_episode(release.episode))
        dub = html.escape(release.dub_team or release.provider)
        anilist = str(release.anilist_id) if release.anilist_id else "—"
        lines = [
            "🌊 Новая серия",
            f"🎬 {title}",
            f"📺 Серия: {episode}",
            f"🎙 Озвучка/источник: {dub}",
            f"🆔 AniList: {anilist}",
        ]
        if release.source_url:
            safe_url = html.escape(release.source_url, quote=True)
            lines.append(f'🔗 <a href="{safe_url}">Источник релиза</a>')
        else:
            lines.append("🔗 Источник релиза")
        return "\n".join(lines)

    async def _send(self, chat_id: int, release: CanonicalRelease) -> bool:
        text = self.format_release(release)
        keyboard = release_search_keyboard(self.anime_search_url)
        try:
            if release.cover_url:
                await self.bot.send_photo(
                    chat_id,
                    release.cover_url,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            else:
                await self.bot.send_message(
                    chat_id,
                    text,
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                    reply_markup=keyboard,
                )
            return True
        except TelegramForbiddenError as exc:
            log.warning("Cannot publish release to %s (forbidden): %s", chat_id, exc)
            await self.repo.disable_broadcast_chat(chat_id)
        except TelegramBadRequest as exc:
            log.warning("Cannot publish release to %s: %s", chat_id, exc)
        return False

    async def publish(self, release: CanonicalRelease) -> None:
        # Exactly one channel is published to directly. Every other registered target
        # is a private chat, group or supergroup and receives the same release broadcast.
        targets: set[int] = {self.channel_id}
        targets.update(await self.repo.broadcast_chat_ids())
        targets.discard(0)

        for chat_id in targets:
            await self._send(chat_id, release)
        await self.repo.mark_published(release.fingerprint)
