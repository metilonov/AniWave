from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str | None = Field(default=None, alias="BOT_USERNAME")
    database_url: str = Field(default="sqlite+aiosqlite:///./data/aniwave.db", alias="DATABASE_URL")

    # Access / publishing. Strings are intentional so an empty value in .env is accepted
    # and can be diagnosed with a clear startup error instead of a Pydantic traceback.
    channel_id_raw: str = Field(default="", alias="CHANNEL_ID")
    admin_id_raw: str = Field(default="", alias="ADMIN_ID")
    legacy_admin_ids: str = Field(default="", alias="ADMIN_IDS")
    anime_search_url: str = Field(default="", alias="ANIME_SEARCH_URL")

    monitor_interval_seconds: int = Field(default=180, alias="MONITOR_INTERVAL_SECONDS")
    anicli_providers: str = Field(
        default="anilibria,animevost,sameband,animego,yummy_anime,anilib_me",
        alias="ANICLI_PROVIDERS",
    )
    rss_config_path: str = Field(default="config/feeds.json", alias="RSS_CONFIG_PATH")
    trace_moe_key: str | None = Field(default=None, alias="TRACE_MOE_KEY")
    trace_min_similarity: float = Field(default=0.82, alias="TRACE_MIN_SIMILARITY")
    http_timeout_seconds: float = Field(default=25.0, alias="HTTP_TIMEOUT_SECONDS")
    user_agent: str = Field(default="AniWave/1.1", alias="USER_AGENT")
    health_enabled: bool = Field(default=False, alias="HEALTH_ENABLED")
    health_host: str = Field(default="0.0.0.0", alias="HEALTH_HOST")
    health_port: int = Field(default=8080, alias="HEALTH_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def channel_id(self) -> int | None:
        value = self.channel_id_raw.strip()
        return int(value) if value else None

    @property
    def admin_id(self) -> int | None:
        value = self.admin_id_raw.strip()
        return int(value) if value else None

    @property
    def admins(self) -> set[int]:
        result: set[int] = set()
        if self.admin_id is not None:
            result.add(self.admin_id)
        # Backward compatibility with older AniWave archives.
        for value in self.legacy_admin_ids.split(","):
            value = value.strip()
            if value:
                result.add(int(value))
        return result

    @property
    def provider_names(self) -> list[str]:
        return [x.strip() for x in self.anicli_providers.split(",") if x.strip()]

    @property
    def rss_path(self) -> Path:
        return Path(self.rss_config_path)

    def validate_runtime(self) -> None:
        missing: list[str] = []
        if not self.bot_token.strip():
            missing.append("BOT_TOKEN")
        if self.admin_id is None:
            missing.append("ADMIN_ID")
        if self.channel_id is None:
            missing.append("CHANNEL_ID")
        if not self.anime_search_url.strip():
            missing.append("ANIME_SEARCH_URL")
        if missing:
            raise RuntimeError("Заполните обязательные переменные .env: " + ", ".join(missing))
        if not self.anime_search_url.startswith(("http://", "https://")):
            raise RuntimeError("ANIME_SEARCH_URL должен начинаться с http:// или https://")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
