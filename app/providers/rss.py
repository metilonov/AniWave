from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import feedparser
import httpx

from app.providers.base import ReleaseProvider
from app.schemas import RawRelease


EPISODE_RE = re.compile(r"(?:сер(?:ия|ии)|episode|ep\.?|e)\s*[-:#№]?\s*(\d+(?:\.\d+)?)", re.I)


class RSSReleaseProvider(ReleaseProvider):
    def __init__(self, http: httpx.AsyncClient, name: str, url: str, dub_team: str | None = None):
        self.http = http
        self.name = f"rss:{name}"
        self.url = url
        self.dub_team = dub_team

    async def fetch(self) -> list[RawRelease]:
        response = await self.http.get(self.url)
        response.raise_for_status()
        feed = feedparser.loads(response.content)
        releases: list[RawRelease] = []
        for entry in feed.entries[:50]:
            title = str(entry.get("title") or "").strip()
            if not title:
                continue
            match = EPISODE_RE.search(title)
            episode = float(match.group(1)) if match else None
            link = entry.get("link")
            entry_id = entry.get("id") or link or title
            published_at = None
            if entry.get("published_parsed"):
                published_at = datetime(*entry.published_parsed[:6])
            releases.append(
                RawRelease(
                    provider=self.name,
                    provider_release_id=str(entry_id),
                    title_raw=title,
                    episode=episode,
                    dub_team=self.dub_team,
                    source_url=link,
                    published_at=published_at,
                )
            )
        return releases


def load_rss_providers(http: httpx.AsyncClient, path: Path) -> list[RSSReleaseProvider]:
    if not path.exists():
        return []
    items = json.loads(path.read_text("utf-8"))
    providers: list[RSSReleaseProvider] = []
    for item in items:
        if not item.get("enabled") or item.get("kind", "release") != "release":
            continue
        providers.append(
            RSSReleaseProvider(
                http=http,
                name=item["name"],
                url=item["url"],
                dub_team=item.get("dub_team"),
            )
        )
    return providers
