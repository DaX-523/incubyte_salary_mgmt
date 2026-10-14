from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_startup_runs_migrations_when_database_url_is_set() -> None:
    migrated_urls: list[str] = []
    app = create_app(
        Settings(_env_file=None, database_url="postgresql://localhost/salary"),
        migrate=migrated_urls.append,
    )

    with TestClient(app):
        pass

    assert migrated_urls == ["postgresql+psycopg://localhost/salary"]


def test_startup_skips_migrations_without_database_url() -> None:
    migrated_urls: list[str] = []
    app = create_app(Settings(_env_file=None, database_url=None), migrate=migrated_urls.append)

    with TestClient(app):
        pass

    assert migrated_urls == []
