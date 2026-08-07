from __future__ import annotations

import asyncio
import logging

from app.engine.release_engine import ReleaseEngine
from app.providers.base import ReleaseProvider
from app.repository import Repository

log = logging.getLogger(__name__)


class ReleaseMonitor:
    def __init__(
        self,
        providers: list[ReleaseProvider],
        engine: ReleaseEngine,
        repo: Repository,
        interval_seconds: int = 180,
    ):
        self.providers = providers
        self.engine = engine
        self.repo = repo
        self.interval_seconds = max(60, interval_seconds)
        self._stop = asyncio.Event()

    async def run_provider(self, provider: ReleaseProvider) -> None:
        state = await self.repo.get_provider_state(provider.name)
        try:
            raw_releases = await provider.fetch()
            new_count = 0
            for raw in raw_releases:
                release = await self.engine.canonicalize(raw)
                if await self.repo.has_release(release.fingerprint):
                    continue
                await self.repo.save_release(release)
                new_count += 1
                # First successful scan is a baseline: save current items, do not spam historical releases.
                if state.initialized and release.confidence >= 0.55:
                    await self.engine.publish(release)
            await self.repo.set_provider_state(
                provider.name,
                initialized=True,
                ok=True,
                seen_delta=new_count,
            )
            log.info("Provider %s OK: %s items, %s new", provider.name, len(raw_releases), new_count)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.exception("Provider %s failed", provider.name)
            await self.repo.set_provider_state(provider.name, ok=False, error=str(exc))

    async def cycle(self) -> None:
        if not self.providers:
            return
        # Concurrency is intentionally limited by provider count; each provider failure is isolated.
        await asyncio.gather(*(self.run_provider(p) for p in self.providers), return_exceptions=True)

    async def run_forever(self) -> None:
        while not self._stop.is_set():
            await self.cycle()
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.interval_seconds)
            except asyncio.TimeoutError:
                pass

    def stop(self) -> None:
        self._stop.set()
