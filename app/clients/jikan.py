from __future__ import annotations

import httpx


class JikanClient:
    BASE = "https://api.jikan.moe/v4"

    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def search(self, title: str, limit: int = 5) -> list[dict]:
        response = await self.http.get(f"{self.BASE}/anime", params={"q": title, "limit": limit, "sfw": "true"})
        response.raise_for_status()
        return response.json().get("data", [])

    async def schedules(self, limit: int = 25) -> list[dict]:
        response = await self.http.get(f"{self.BASE}/schedules", params={"limit": limit, "sfw": "true"})
        response.raise_for_status()
        return response.json().get("data", [])
