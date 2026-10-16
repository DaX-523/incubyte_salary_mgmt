import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.main import create_app
from tests.fakes import JWT_SECRET


def test_startup_runs_migrations_when_database_url_is_set() -> None:
    migrated_urls: list[str] = []
    app = create_app(
        Settings(
            _env_file=None,
            database_url="postgresql://localhost/salary",
            jwt_secret=SecretStr(JWT_SECRET),
        ),
        migrate=migrated_urls.append,
    )

    with TestClient(app):
        pass

    assert migrated_urls == ["postgresql+psycopg://localhost/salary"]


def test_startup_fails_without_a_jwt_secret_when_serving_data() -> None:
    migrated_urls: list[str] = []
    app = create_app(
        Settings(_env_file=None, database_url="postgresql://localhost/salary", jwt_secret=None),
        migrate=migrated_urls.append,
    )

    with pytest.raises(RuntimeError, match="Set JWT_SECRET"), TestClient(app):
        pass

    assert migrated_urls == []


def test_startup_skips_migrations_without_database_url() -> None:
    migrated_urls: list[str] = []
    app = create_app(Settings(_env_file=None, database_url=None), migrate=migrated_urls.append)

    with TestClient(app):
        pass

    assert migrated_urls == []
