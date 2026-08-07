from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import RawRelease


class ReleaseProvider(ABC):
    name: str

    @abstractmethod
    async def fetch(self) -> list[RawRelease]:
        raise NotImplementedError
