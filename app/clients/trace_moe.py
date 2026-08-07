from __future__ import annotations

import httpx

from app.schemas import TraceResult


class TraceMoeClient:
    BASE = "https://api.trace.moe/search"

    def __init__(self, http: httpx.AsyncClient, api_key: str | None = None):
        self.http = http
        self.api_key = api_key

    async def search_bytes(self, image: bytes, filename: str = "frame.jpg") -> list[TraceResult]:
        headers = {"x-trace-key": self.api_key} if self.api_key else None
        response = await self.http.post(
            self.BASE,
            params={"anilistInfo": "1", "cutBorders": "1"},
            files={"image": (filename, image, "application/octet-stream")},
            headers=headers,
        )
        response.raise_for_status()
        payload = response.json()
        results: list[TraceResult] = []
        for item in payload.get("result", []):
            anilist = item.get("anilist")
            anilist_id: int | None = None
            title = "Неизвестное аниме"
            if isinstance(anilist, dict):
                anilist_id = anilist.get("id")
                titles = anilist.get("title") or {}
                title = titles.get("english") or titles.get("romaji") or titles.get("native") or title
            elif isinstance(anilist, int):
                anilist_id = anilist
            results.append(
                TraceResult(
                    anilist_id=anilist_id,
                    title=title,
                    episode=str(item.get("episode") or "?"),
                    from_seconds=float(item.get("from") or 0),
                    to_seconds=float(item.get("to") or 0),
                    similarity=float(item.get("similarity") or 0),
                    preview_image=item.get("image"),
                    preview_video=item.get("video"),
                )
            )
        return results
