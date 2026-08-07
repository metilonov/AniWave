from __future__ import annotations

import importlib
import logging
from typing import Any

from app.providers.base import ReleaseProvider
from app.schemas import RawRelease

log = logging.getLogger(__name__)

DUB_TEAM_MAP = {
    "anilibria": "AniLiberty",
    "animevost": "AnimeVost",
    "sameband": "StudioBand",
    "animego": "AnimeGo",
    "yummy_anime": "YummyAnime",
    "anilib_me": "AnimeLib",
}
MULTI_DUB_SOURCES = {"animego", "yummy_anime", "anilib_me"}


def _safe_value(obj: Any, *names: str) -> Any:
    for name in names:
        try:
            value = getattr(obj, name, None)
        except Exception:
            continue
        if value is not None and not callable(value):
            return value
    return None


def _obj_text(obj: Any) -> str:
    value = _safe_value(obj, "title", "name", "label", "ru_title", "russian")
    if isinstance(value, str) and value.strip():
        return value.strip()
    try:
        return str(obj).strip()
    except Exception:
        return repr(obj)


def _episode_number(obj: Any) -> float | None:
    # anicli-api BaseEpisode exposes `ordinal` and backwards-compatible `num`.
    value = _safe_value(obj, "ordinal", "number", "num", "episode", "episode_number", "index")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            pass
    return None


def _url(obj: Any) -> str | None:
    value = _safe_value(obj, "url", "href", "link", "web_url")
    return str(value) if value else None


class AnicliProvider(ReleaseProvider):
    """Metadata-only adapter around anicli-api.

    It intentionally never calls `a_get_videos()`. For multi-dub aggregators it may call
    `a_get_sources()` only to identify dubbing/source labels; public anime page URLs are
    retained as the outgoing source link rather than direct player URLs.
    """

    def __init__(self, source_name: str, latest_per_title: int = 2):
        self.source_name = source_name
        self.name = f"anicli:{source_name}"
        self.latest_per_title = latest_per_title

    async def fetch(self) -> list[RawRelease]:
        module = importlib.import_module(f"anicli_api.source.{self.source_name}")
        extractor_cls = getattr(module, "Extractor")
        extractor = extractor_cls()
        ongoing = await extractor.a_ongoing()
        releases: list[RawRelease] = []

        for item in ongoing:
            try:
                anime = await item.a_get_anime()
                title = _safe_value(anime, "title") or _safe_value(item, "title") or _obj_text(item)
                anime_page = _url(item)
                episodes = await anime.a_get_episodes()
                parsed = [(ep, _episode_number(ep)) for ep in episodes]
                parsed.sort(key=lambda pair: pair[1] if pair[1] is not None else -1, reverse=True)

                for ep, number in parsed[: self.latest_per_title]:
                    if self.source_name in MULTI_DUB_SOURCES:
                        try:
                            sources = await ep.a_get_sources()
                        except Exception as exc:
                            log.debug("%s source labels failed for %s ep %s: %s", self.name, title, number, exc)
                            sources = []
                        if sources:
                            seen_labels: set[str] = set()
                            for source in sources:
                                label = _safe_value(source, "title") or _obj_text(source)
                                label = str(label).strip()
                                if not label or label in seen_labels:
                                    continue
                                seen_labels.add(label)
                                release_id = f"{anime_page or title}|{number}|{label}"
                                releases.append(
                                    RawRelease(
                                        provider=self.name,
                                        provider_release_id=release_id,
                                        title_raw=str(title),
                                        episode=number,
                                        dub_team=label,
                                        source_url=anime_page,
                                        payload={"episode_title": _obj_text(ep), "source_label": label},
                                    )
                                )
                            continue

                    release_id = f"{anime_page or title}|{number}|{self.source_name}"
                    releases.append(
                        RawRelease(
                            provider=self.name,
                            provider_release_id=release_id,
                            title_raw=str(title),
                            episode=number,
                            dub_team=DUB_TEAM_MAP.get(self.source_name, self.source_name),
                            source_url=anime_page,
                            payload={"episode_title": _obj_text(ep)},
                        )
                    )
            except Exception as exc:
                log.warning("%s title failed: %s", self.name, exc)
        return releases
