# AniWave source status

Checked/assembled: 2026-08-07.

## Automatic release providers included

These are loaded through `anicli-api` and can be enabled/disabled in `.env`:

| Provider key | Role | Notes |
|---|---|---|
| `anilibria` | AniLiberty/AniLibria releases | API-backed in anicli-api |
| `animevost` | AnimeVost releases | API-backed in anicli-api |
| `sameband` | StudioBand/SameBand releases | HTML-backed adapter |
| `animego` | AnimeGo aggregator | Region restrictions may apply |
| `yummy_anime` | YummyAnime aggregator | API-backed adapter |
| `anilib_me` | AnimeLib aggregator | Can return 403 under heavy usage |

A provider failure is isolated: it is recorded in `provider_states` and does not stop Telegram polling or other providers.

## Generic RSS/Atom release providers

`config/feeds.json` lets you connect additional legal/public RSS or Atom feeds without writing Python code. Set `enabled: true` and provide a feed URL. This is the recommended path for dubbing teams that publish a stable public feed.

## Metadata/search services included

- AniList GraphQL — canonical metadata and IDs.
- Jikan v4 — MyAnimeList-derived fallback and MAL ID resolution.
- Shikimori REST — Russian-oriented metadata client (available to future handlers/services).
- trace.moe — search anime/episode/timestamp by screenshot.

## Deliberately NOT included

AniWave does not proxy, redistribute, or download anime video streams. The release layer records metadata and source links only. Player extractors in third-party projects are not used by this code.

## Adding a new provider

Implement `app.providers.base.ReleaseProvider` and return `RawRelease` items from `fetch()`. Then register the provider in `build_services()`.
