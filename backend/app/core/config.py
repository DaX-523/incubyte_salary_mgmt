from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PSYCOPG_URL_PREFIX = "postgresql+psycopg://"
PLAIN_POSTGRES_URL_PREFIXES = ("postgresql://", "postgres://")


def normalize_database_url(url: str) -> str:
    """Point plain Postgres URLs at the psycopg 3 driver, which is the one installed."""
    for prefix in PLAIN_POSTGRES_URL_PREFIXES:
        if url.startswith(prefix):
            return PSYCOPG_URL_PREFIX + url.removeprefix(prefix)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # When set, pending migrations are applied on startup.
    database_url: str | None = None

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, value: str | None) -> str | None:
        if not value:
            return None
        return normalize_database_url(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()
