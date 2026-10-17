"""Organization data needs a logged-in user; only the login, the filter catalog and the health
check are public."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import issue_token
from tests.fakes import JWT_SECRET, NOW

PROTECTED_ENDPOINTS = [
    ("GET", "/api/v1/employees?month=2026-10"),
    ("GET", "/api/v1/employees/export?month=2026-10"),
    ("POST", "/api/v1/employees"),
    ("GET", "/api/v1/employees/1"),
    ("PATCH", "/api/v1/employees/1"),
    ("DELETE", "/api/v1/employees/1"),
    ("GET", "/api/v1/employees/1/payrolls"),
    ("POST", "/api/v1/employees/1/payrolls"),
    ("GET", "/api/v1/payrolls/1"),
    ("PATCH", "/api/v1/payrolls/1"),
    ("GET", "/api/v1/insights/payroll-status?month=2026-10"),
    ("GET", "/api/v1/insights/pay-by-job-title?country=GB"),
    ("GET", "/api/v1/insights/pay-by-country"),
    ("GET", "/api/v1/auth/me"),
    ("POST", "/api/v1/auth/logout"),
]


@pytest.mark.parametrize(("method", "path"), PROTECTED_ENDPOINTS)
def test_protected_endpoints_ask_for_a_login(
    auth_client: TestClient, method: str, path: str
) -> None:
    response = auth_client.request(method, path)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Log in to continue"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    ("authorization", "message"),
    [
        ("Basic aHI6c2VjcmV0", "Log in to continue"),
        ("Bearer not-a-token", "Your session has ended; log in again"),
        (
            f"Bearer {issue_token(1, 1, 'x' * 32, NOW).token}",
            "Your session has ended; log in again",
        ),
        (
            f"Bearer {issue_token(99, 1, JWT_SECRET, NOW).token}",
            "Your session has ended; log in again",
        ),
    ],
    ids=["another-scheme", "garbage-token", "signed-elsewhere", "unknown-user"],
)
def test_protected_endpoints_reject_unusable_credentials(
    auth_client: TestClient, authorization: str, message: str
) -> None:
    response = auth_client.get(
        "/api/v1/employees", params={"month": "2026-10"}, headers={"Authorization": authorization}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": message}


@pytest.mark.parametrize("path", ["/api/v1/filters", "/health"])
def test_reference_data_and_health_need_no_login(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == status.HTTP_200_OK
