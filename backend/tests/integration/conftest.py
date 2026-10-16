"""Integration tests run against a real Postgres named by TEST_DATABASE_URL.

They are skipped when it is unset. The database is reset to an empty schema per session,
so never point TEST_DATABASE_URL at a database whose data you need.
"""

import os
from collections.abc import Callable, Iterator

import pytest
from alembic import command
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.core.config import Settings, normalize_database_url
from app.db.migrate import alembic_config, run_migrations
from app.main import create_app
from tests.fakes import JWT_SECRET, ORGANIZATION_ID, ORGANIZATION_NAME, USER_PASSWORD, make_user

LogIn = Callable[..., dict[str, str]]


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
    """Every test starts with one organization, ORGANIZATION_ID, that `make_employee` uses."""
    with migrated_engine.begin() as connection:
        organization_id = connection.scalar(
            text("INSERT INTO organizations (name) VALUES (:name) RETURNING id"),
            {"name": ORGANIZATION_NAME},
        )
    assert organization_id == ORGANIZATION_ID
    yield migrated_engine
    with migrated_engine.begin() as connection:
        connection.execute(
            text("TRUNCATE payrolls, employees, users, organizations RESTART IDENTITY")
        )


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


@pytest.fixture
def anonymous_client(engine: Engine, database_url: str) -> Iterator[TestClient]:
    """The real app on the test database, with no one logged in."""
    settings = Settings(_env_file=None, database_url=database_url, jwt_secret=SecretStr(JWT_SECRET))
    # The session fixture already migrated the database.
    app = create_app(settings, migrate=lambda _: None)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def log_in(anonymous_client: TestClient, engine: Engine) -> LogIn:
    """Adds an HR user to an organization and returns the headers of their logged-in session."""

    def log_in_as(
        organization_id: int = ORGANIZATION_ID, email: str = "hr@acme.example"
    ) -> dict[str, str]:
        with Session(engine) as session:
            session.add(make_user(id=None, organization_id=organization_id, email=email))
            session.commit()
        response = anonymous_client.post(
            "/api/v1/auth/login", json={"email": email, "password": USER_PASSWORD}
        )
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return log_in_as


@pytest.fixture
def db_client(anonymous_client: TestClient, log_in: LogIn) -> TestClient:
    """Logged in as an HR user of the test organization, through the real login endpoint."""
    anonymous_client.headers.update(log_in())
    return anonymous_client
