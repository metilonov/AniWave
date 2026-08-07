from __future__ import annotations

import re
from typing import Any

import httpx

from app.schemas import AnimeCard


API_URL = "https://graphql.anilist.co"

MEDIA_FIELDS = """
    id
    idMal
    title { romaji english native }
    episodes
    format
    status
    season
    seasonYear
    averageScore
    genres
    coverImage { large extraLarge }
    siteUrl
    description(asHtml: false)
    nextAiringEpisode { episode airingAt }
"""


class AniListClient:
    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def _query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self.http.post(API_URL, json={"query": query, "variables": variables or {}})
        response.raise_for_status()
        data = response.json()
        if data.get("errors"):
            raise RuntimeError(f"AniList error: {data['errors']}")
        return data["data"]

    @staticmethod
    def _card(data: dict[str, Any]) -> AnimeCard:
        title = data.get("title") or {}
        next_airing = data.get("nextAiringEpisode") or {}
        description = data.get("description")
        if description:
            description = re.sub(r"<[^>]+>", "", description)
        return AnimeCard(
            anilist_id=data["id"],
            mal_id=data.get("idMal"),
            title=title.get("english") or title.get("romaji") or title.get("native") or str(data["id"]),
            title_english=title.get("english"),
            title_native=title.get("native"),
            episodes=data.get("episodes"),
            format=data.get("format"),
            status=data.get("status"),
            season=data.get("season"),
            season_year=data.get("seasonYear"),
            score=data.get("averageScore"),
            genres=data.get("genres") or [],
            cover_url=(data.get("coverImage") or {}).get("extraLarge") or (data.get("coverImage") or {}).get("large"),
            site_url=data.get("siteUrl"),
            description=description,
            next_episode=next_airing.get("episode"),
            next_airing_at=next_airing.get("airingAt"),
        )

    async def search(self, text: str, per_page: int = 5) -> list[AnimeCard]:
        query = f"""
        query ($search: String, $perPage: Int) {{
          Page(page: 1, perPage: $perPage) {{
            media(search: $search, type: ANIME, sort: SEARCH_MATCH) {{ {MEDIA_FIELDS} }}
          }}
        }}
        """
        data = await self._query(query, {"search": text, "perPage": per_page})
        return [self._card(x) for x in data["Page"]["media"]]

    async def by_id(self, anilist_id: int) -> AnimeCard | None:
        query = f"query ($id: Int) {{ Media(id: $id, type: ANIME) {{ {MEDIA_FIELDS} }} }}"
        data = await self._query(query, {"id": anilist_id})
        media = data.get("Media")
        return self._card(media) if media else None

    async def by_mal_id(self, mal_id: int) -> AnimeCard | None:
        query = f"query ($idMal: Int) {{ Media(idMal: $idMal, type: ANIME) {{ {MEDIA_FIELDS} }} }}"
        data = await self._query(query, {"idMal": mal_id})
        media = data.get("Media")
        return self._card(media) if media else None

    async def top(self, per_page: int = 10) -> list[AnimeCard]:
        query = f"""
        query ($perPage: Int) {{
          Page(page: 1, perPage: $perPage) {{
            media(type: ANIME, sort: SCORE_DESC, isAdult: false) {{ {MEDIA_FIELDS} }}
          }}
        }}
        """
        data = await self._query(query, {"perPage": per_page})
        return [self._card(x) for x in data["Page"]["media"]]

    async def trending(self, per_page: int = 10) -> list[AnimeCard]:
        query = f"""
        query ($perPage: Int) {{
          Page(page: 1, perPage: $perPage) {{
            media(type: ANIME, sort: TRENDING_DESC, isAdult: false) {{ {MEDIA_FIELDS} }}
          }}
        }}
        """
        data = await self._query(query, {"perPage": per_page})
        return [self._card(x) for x in data["Page"]["media"]]

    async def season_now(self, per_page: int = 10) -> list[AnimeCard]:
        query = f"""
        query ($perPage: Int) {{
          Page(page: 1, perPage: $perPage) {{
            media(type: ANIME, status: RELEASING, sort: TRENDING_DESC, isAdult: false) {{ {MEDIA_FIELDS} }}
          }}
        }}
        """
        data = await self._query(query, {"perPage": per_page})
        return [self._card(x) for x in data["Page"]["media"]]
