import unittest

from app.engine.normalizer import display_episode, normalize_title


class NormalizerTests(unittest.TestCase):
    def test_release_noise_removed(self):
        value = normalize_title("[AniLiberty] Dandadan Season 2 — Episode 06 (1080p)")
        self.assertEqual(value, "dandadan season 2")

    def test_russian_season(self):
        value = normalize_title("Магическая битва ТВ-3 серия 4")
        self.assertEqual(value, "магическая битва season 3")

    def test_episode_display(self):
        self.assertEqual(display_episode(4.0), "4")
        self.assertEqual(display_episode(4.5), "4.5")
        self.assertEqual(display_episode(None), "?")


if __name__ == "__main__":
    unittest.main()
