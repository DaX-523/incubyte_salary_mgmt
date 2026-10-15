from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_employee_repository,
    get_insights_repository,
    get_payroll_repository,
)
from tests.fakes import (
    InMemoryEmployeeRepository,
    InMemoryPayrollRepository,
    StubInsightsRepository,
)


@pytest.fixture
def api_client(
    app: FastAPI,
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
    insights_repository: StubInsightsRepository,
) -> Iterator[TestClient]:
    """A client whose endpoints read and write the in-memory repositories."""
    app.dependency_overrides[get_employee_repository] = lambda: employee_repository
    app.dependency_overrides[get_payroll_repository] = lambda: payroll_repository
    app.dependency_overrides[get_insights_repository] = lambda: insights_repository
    with TestClient(app) as test_client:
        yield test_client
