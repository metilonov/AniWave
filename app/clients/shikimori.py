from __future__ import annotations

import httpx


class ShikimoriClient:
    BASE = "https://shikimori.one/api"

    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def search(self, title: str, limit: int = 5) -> list[dict]:
        response = await self.http.get(
            f"{self.BASE}/animes",
            params={"search": title, "limit": limit, "censored": "true"},
        )
        response.raise_for_status()
        return response.json()

    async def by_id(self, anime_id: int) -> dict | None:
        response = await self.http.get(f"{self.BASE}/animes/{anime_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
