"""Integration tests run against a real Postgres named by TEST_DATABASE_URL.

They are skipped when it is unset. The database is reset to an empty schema per session,
so never point TEST_DATABASE_URL at a database whose data you need.
"""

import os
from collections.abc import Iterator

import pytest
from alembic import command
from sqlalchemy import Engine, create_engine, text

from app.core.config import normalize_database_url
from app.db.migrate import alembic_config, run_migrations


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    return normalize_database_url(url)


@pytest.fixture(scope="session")
def migrated_engine(database_url: str) -> Iterator[Engine]:
    command.downgrade(alembic_config(database_url), "base")
    run_migrations(database_url)
    engine = create_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def engine(migrated_engine: Engine) -> Iterator[Engine]:
    yield migrated_engine
    with migrated_engine.begin() as connection:
        connection.execute(text("TRUNCATE payrolls, employees RESTART IDENTITY"))
