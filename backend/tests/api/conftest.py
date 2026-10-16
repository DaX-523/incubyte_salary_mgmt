from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_user,
    get_employee_repository,
    get_insights_repository,
    get_now,
    get_payroll_repository,
    get_user_repository,
)
from app.services.auth import CurrentUser
from tests.fakes import (
    NOW,
    ORGANIZATION_ID,
    InMemoryEmployeeRepository,
    InMemoryPayrollRepository,
    InMemoryUserRepository,
    StubInsightsRepository,
)

LOGGED_IN_USER = CurrentUser(user_id=1, organization_id=ORGANIZATION_ID)


@pytest.fixture
def api_client(
    app: FastAPI,
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
    insights_repository: StubInsightsRepository,
) -> Iterator[TestClient]:
    """A logged-in client whose endpoints read and write the in-memory repositories."""
    app.dependency_overrides[get_current_user] = lambda: LOGGED_IN_USER
    app.dependency_overrides[get_employee_repository] = lambda: employee_repository
    app.dependency_overrides[get_payroll_repository] = lambda: payroll_repository
    app.dependency_overrides[get_insights_repository] = lambda: insights_repository
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_client(app: FastAPI, user_repository: InMemoryUserRepository) -> Iterator[TestClient]:
    """A client with no one logged in, whose login checks the in-memory users at a fixed time."""
    app.dependency_overrides[get_user_repository] = lambda: user_repository
    app.dependency_overrides[get_now] = lambda: NOW
    with TestClient(app) as test_client:
        yield test_client
