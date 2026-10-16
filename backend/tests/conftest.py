from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.main import create_app
from tests.fakes import (
    JWT_SECRET,
    InMemoryEmployeeRepository,
    InMemoryPayrollRepository,
    InMemoryUserRepository,
    StubInsightsRepository,
    make_user,
)


@pytest.fixture
def app() -> FastAPI:
    # Explicit settings: unit tests never read backend/.env or touch a real database.
    return create_app(Settings(_env_file=None, database_url=None, jwt_secret=SecretStr(JWT_SECRET)))


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def employee_repository() -> InMemoryEmployeeRepository:
    return InMemoryEmployeeRepository()


@pytest.fixture
def payroll_repository() -> InMemoryPayrollRepository:
    return InMemoryPayrollRepository()


@pytest.fixture
def insights_repository() -> StubInsightsRepository:
    return StubInsightsRepository()


@pytest.fixture
def user_repository() -> InMemoryUserRepository:
    return InMemoryUserRepository(make_user())
