from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models import ChatSettings, ProviderState, ReleaseRecord, Subscription, TelegramUser
from app.schemas import CanonicalRelease


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Repository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]):
        self.sessions = sessions

    async def upsert_user(self, user_id: int, username: str | None, first_name: str | None) -> None:
        async with self.sessions() as session:
            user = await session.get(TelegramUser, user_id)
            if user is None:
                user = TelegramUser(id=user_id, username=username, first_name=first_name)
                session.add(user)
            else:
                user.username = username
                user.first_name = first_name
            await session.commit()


    async def register_broadcast_chat(self, chat_id: int) -> None:
        """Register/enable a private chat, group or supergroup for global release broadcasts."""
        async with self.sessions() as session:
            chat = await session.get(ChatSettings, chat_id)
            if chat is None:
                chat = ChatSettings(chat_id=chat_id, releases_enabled=True, news_enabled=True)
                session.add(chat)
            else:
                chat.releases_enabled = True
            await session.commit()

    async def disable_broadcast_chat(self, chat_id: int) -> None:
        async with self.sessions() as session:
            chat = await session.get(ChatSettings, chat_id)
            if chat is not None:
                chat.releases_enabled = False
                await session.commit()

    async def broadcast_chat_ids(self) -> list[int]:
        async with self.sessions() as session:
            result = await session.scalars(
                select(ChatSettings.chat_id).where(ChatSettings.releases_enabled.is_(True))
            )
            return list(dict.fromkeys(result))

    async def add_subscription(self, chat_id: int, anilist_id: int, title: str) -> bool:
        async with self.sessions() as session:
            existing = await session.scalar(
                select(Subscription).where(
                    Subscription.target_chat_id == chat_id,
                    Subscription.anilist_id == anilist_id,
                )
            )
            if existing:
                return False
            session.add(Subscription(target_chat_id=chat_id, anilist_id=anilist_id, anime_title=title))
            await session.commit()
            return True

    async def remove_subscription(self, chat_id: int, anilist_id: int) -> bool:
        async with self.sessions() as session:
            existing = await session.scalar(
                select(Subscription).where(
                    Subscription.target_chat_id == chat_id,
                    Subscription.anilist_id == anilist_id,
                )
            )
            if not existing:
                return False
            await session.delete(existing)
            await session.commit()
            return True

    async def list_subscriptions(self, chat_id: int) -> list[Subscription]:
        async with self.sessions() as session:
            result = await session.scalars(
                select(Subscription)
                .where(Subscription.target_chat_id == chat_id)
                .order_by(Subscription.anime_title)
            )
            return list(result)

    async def subscriber_chat_ids(self, anilist_id: int) -> list[int]:
        async with self.sessions() as session:
            result = await session.scalars(
                select(Subscription.target_chat_id).where(Subscription.anilist_id == anilist_id)
            )
            return list(dict.fromkeys(result))

    async def has_release(self, fingerprint: str) -> bool:
        async with self.sessions() as session:
            return await session.get(ReleaseRecord, fingerprint) is not None

    async def save_release(self, release: CanonicalRelease) -> None:
        async with self.sessions() as session:
            if await session.get(ReleaseRecord, release.fingerprint):
                return
            session.add(
                ReleaseRecord(
                    fingerprint=release.fingerprint,
                    provider=release.provider,
                    provider_release_id=release.provider_release_id,
                    title_raw=release.title_raw,
                    title_normalized=release.title_normalized,
                    anilist_id=release.anilist_id,
                    anime_title=release.anime_title,
                    episode=release.episode,
                    dub_team=release.dub_team,
                    source_url=release.source_url,
                    confidence=release.confidence,
                    detected_at=release.detected_at,
                    published_at=release.published_at,
                )
            )
            await session.commit()

    async def mark_published(self, fingerprint: str) -> None:
        async with self.sessions() as session:
            obj = await session.get(ReleaseRecord, fingerprint)
            if obj:
                obj.published_at = now_utc()
                await session.commit()

    async def get_provider_state(self, provider: str) -> ProviderState:
        async with self.sessions() as session:
            state = await session.get(ProviderState, provider)
            if state is None:
                state = ProviderState(provider=provider, initialized=False, seen_count=0)
                session.add(state)
                await session.commit()
                await session.refresh(state)
            return state

    async def set_provider_state(
        self,
        provider: str,
        *,
        initialized: bool | None = None,
        ok: bool | None = None,
        error: str | None = None,
        seen_delta: int = 0,
    ) -> None:
        async with self.sessions() as session:
            state = await session.get(ProviderState, provider)
            if state is None:
                state = ProviderState(provider=provider, initialized=False, seen_count=0)
                session.add(state)
            state.last_run_at = now_utc()
            if initialized is not None:
                state.initialized = initialized
            if ok is True:
                state.last_ok_at = now_utc()
                state.last_error = None
            elif ok is False:
                state.last_error = (error or "unknown error")[:4000]
            state.seen_count = (state.seen_count or 0) + seen_delta
            await session.commit()

    async def provider_states(self) -> list[ProviderState]:
        async with self.sessions() as session:
            result = await session.scalars(select(ProviderState).order_by(ProviderState.provider))
            return list(result)
