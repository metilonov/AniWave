from __future__ import annotations

import re
import unicodedata

NOISE_PATTERNS = [
    r"\[[^\]]+\]",
    r"\([^)]*(?:озвуч|dub|sub|1080|720|480|web|bd|tv)[^)]*\)",
    r"\b(?:1080p|720p|480p|web[- ]?dl|webrip|bdrip|bluray|tv)\b",
    r"\b(?:серия|episode|ep\.?|эпизод)\s*[-:#№]?\s*\d+(?:\.\d+)?\b",
]


def normalize_title(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = text.replace("ё", "е").replace("Ё", "Е")
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.I)
    text = re.sub(r"\b(?:s|season)\s*0?(\d+)\b", r" season \1 ", text, flags=re.I)
    text = re.sub(r"\b(?:тв|сезон)\s*[- ]?0?(\d+)\b", r" season \1 ", text, flags=re.I)
    text = re.sub(r"[^0-9A-Za-zА-Яа-я一-龯ぁ-ゔァ-ヴー々〆〤\s]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


DUB_ALIASES = {
    "anilibria": "aniliberty",
    "aniliberty": "aniliberty",
    "animevost": "animevost",
    "sameband": "studioband",
    "studioband": "studioband",
    "dreamerscast": "dreamcast",
    "dream cast": "dreamcast",
    "anistar": "anistar",
    "anidub": "anidub",
    "shiza": "shiza",
    "kazoku": "kazoku",
    "fumodub": "fumodub",
    "youkai": "youkai",
}


def canonical_dub_team(value: str | None) -> str:
    normalized = normalize_title(value or "unknown")
    for needle, canonical in DUB_ALIASES.items():
        if needle in normalized:
            return canonical
    return normalized or "unknown"


def display_episode(number: float | None) -> str:
    if number is None:
        return "?"
    return str(int(number)) if number.is_integer() else str(number)
