import unittest
from unittest.mock import patch

from app.providers.anicli import AnicliProvider


class FakeSource:
    def __init__(self, title):
        self.title = title


class FakeEpisode:
    def __init__(self, ordinal, title):
        self.ordinal = ordinal
        self.title = title

    @property
    def num(self):
        return str(self.ordinal)

    async def a_get_sources(self):
        return [FakeSource("AniLiberty / Kodik"), FakeSource("Dream Cast / Kodik")]


class FakeAnime:
    title = "Dandadan Season 2"

    async def a_get_episodes(self):
        return [FakeEpisode(1, "Episode 1"), FakeEpisode(2, "Episode 2")]


class FakeOngoing:
    title = "Dandadan Season 2"
    url = "https://example.invalid/dandadan"

    async def a_get_anime(self):
        return FakeAnime()


class FakeExtractor:
    async def a_ongoing(self):
        return [FakeOngoing()]


class FakeModule:
    Extractor = FakeExtractor


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_multi_dub_metadata_only(self):
        provider = AnicliProvider("animego", latest_per_title=1)
        with patch("app.providers.anicli.importlib.import_module", return_value=FakeModule):
            items = await provider.fetch()
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].episode, 2.0)
        self.assertEqual(items[0].source_url, "https://example.invalid/dandadan")
        self.assertIn("AniLiberty", items[0].dub_team)


if __name__ == "__main__":
    unittest.main()
