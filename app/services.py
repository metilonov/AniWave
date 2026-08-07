from __future__ import annotations

from dataclasses import dataclass

import httpx
from aiogram import Bot

from app.clients.anilist import AniListClient
from app.clients.jikan import JikanClient
from app.clients.shikimori import ShikimoriClient
from app.clients.trace_moe import TraceMoeClient
from app.config import Settings
from app.database import Database
from app.engine.matcher import AnimeMatcher
from app.engine.monitor import ReleaseMonitor
from app.engine.release_engine import ReleaseEngine
from app.providers.anicli import AnicliProvider
from app.providers.rss import load_rss_providers
from app.repository import Repository


@dataclass(slots=True)
class Services:
    settings: Settings
    http: httpx.AsyncClient
    db: Database
    repo: Repository
    anilist: AniListClient
    jikan: JikanClient
    shikimori: ShikimoriClient
    trace: TraceMoeClient
    matcher: AnimeMatcher
    release_engine: ReleaseEngine
    monitor: ReleaseMonitor


async def build_services(settings: Settings, bot: Bot) -> Services:
    http = httpx.AsyncClient(
        timeout=settings.http_timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": settings.user_agent, "Accept": "application/json, text/plain, */*"},
    )
    db = Database(settings.database_url)
    await db.init()
    repo = Repository(db.sessions)
    anilist = AniListClient(http)
    jikan = JikanClient(http)
    shikimori = ShikimoriClient(http)
    trace = TraceMoeClient(http, settings.trace_moe_key)
    matcher = AnimeMatcher(anilist, jikan)
    release_engine = ReleaseEngine(repo, matcher, bot, settings.channel_id, settings.anime_search_url)

    providers = [AnicliProvider(name) for name in settings.provider_names]
    providers.extend(load_rss_providers(http, settings.rss_path))
    monitor = ReleaseMonitor(providers, release_engine, repo, settings.monitor_interval_seconds)
    return Services(
        settings=settings,
        http=http,
        db=db,
        repo=repo,
        anilist=anilist,
        jikan=jikan,
        shikimori=shikimori,
        trace=trace,
        matcher=matcher,
        release_engine=release_engine,
        monitor=monitor,
    )


async def close_services(services: Services) -> None:
    services.monitor.stop()
    await services.http.aclose()
    await services.db.close()
