from __future__ import annotations

import asyncio
from dataclasses import dataclass

from rapidfuzz.fuzz import ratio

from app.clients.anilist import AniListClient
from app.clients.jikan import JikanClient
from app.engine.normalizer import normalize_title
from app.schemas import AnimeCard


@dataclass(slots=True)
class Match:
    anime: AnimeCard | None
    confidence: float


class AnimeMatcher:
    def __init__(self, anilist: AniListClient, jikan: JikanClient):
        self.anilist = anilist
        self.jikan = jikan
        self._cache: dict[str, Match] = {}
        self._lock = asyncio.Lock()

    async def match(self, raw_title: str) -> Match:
        key = normalize_title(raw_title)
        if not key:
            return Match(None, 0.0)
        if key in self._cache:
            return self._cache[key]

        async with self._lock:
            if key in self._cache:
                return self._cache[key]
            match = await self._match_uncached(raw_title, key)
            if len(self._cache) > 5000:
                self._cache.clear()
            self._cache[key] = match
            return match

    async def _match_uncached(self, raw_title: str, normalized: str) -> Match:
        try:
            candidates = await self.anilist.search(raw_title, 5)
        except Exception:
            candidates = []

        best: AnimeCard | None = None
        best_score = 0.0
        for anime in candidates:
            variants = [anime.title, anime.title_english or "", anime.title_native or ""]
            score = max(ratio(normalized, normalize_title(v)) for v in variants if v)
            if score > best_score:
                best_score = score
                best = anime

        if best is not None and best_score >= 58:
            return Match(best, min(0.99, best_score / 100.0))

        # MAL/Jikan fallback -> resolve back to AniList by MAL id.
        try:
            jikan_results = await self.jikan.search(raw_title, 3)
            for item in jikan_results:
                mal_id = item.get("mal_id")
                if not mal_id:
                    continue
                anime = await self.anilist.by_mal_id(int(mal_id))
                if anime:
                    score = ratio(normalized, normalize_title(anime.title)) / 100.0
                    if score >= 0.55:
                        return Match(anime, min(0.94, score))
        except Exception:
            pass

        return Match(best, best_score / 100.0 if best else 0.0)
