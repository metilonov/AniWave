from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class AnimeCard:
    anilist_id: int
    mal_id: int | None
    title: str
    title_english: str | None = None
    title_native: str | None = None
    episodes: int | None = None
    format: str | None = None
    status: str | None = None
    season: str | None = None
    season_year: int | None = None
    score: float | None = None
    genres: list[str] = field(default_factory=list)
    cover_url: str | None = None
    site_url: str | None = None
    description: str | None = None
    next_episode: int | None = None
    next_airing_at: int | None = None


@dataclass(slots=True)
class RawRelease:
    provider: str
    provider_release_id: str
    title_raw: str
    episode: float | None
    dub_team: str | None
    source_url: str | None = None
    published_at: datetime | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalRelease:
    fingerprint: str
    provider: str
    provider_release_id: str
    title_raw: str
    title_normalized: str
    anilist_id: int | None
    anime_title: str
    episode: float | None
    dub_team: str | None
    source_url: str | None
    confidence: float
    detected_at: datetime = field(default_factory=utcnow)
    published_at: datetime | None = None
    cover_url: str | None = None


@dataclass(slots=True)
class TraceResult:
    anilist_id: int | None
    title: str
    episode: str
    from_seconds: float
    to_seconds: float
    similarity: float
    preview_image: str | None = None
    preview_video: str | None = None
