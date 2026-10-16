from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PSYCOPG_URL_PREFIX = "postgresql+psycopg://"
PLAIN_POSTGRES_URL_PREFIXES = ("postgresql://", "postgres://")
# HS256 is only as strong as its key: 32 characters is the floor (`openssl rand -hex 32` gives 64).
MIN_JWT_SECRET_LENGTH = 32


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

    # Signs login tokens. Required whenever the API serves data (see create_app).
    jwt_secret: SecretStr | None = None

    @field_validator("jwt_secret")
    @classmethod
    def _long_enough(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None or not value.get_secret_value():
            return None
        if len(value.get_secret_value()) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(f"JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
