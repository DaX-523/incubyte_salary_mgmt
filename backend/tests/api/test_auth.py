from datetime import timedelta
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.dependencies import get_user_repository
from app.core.config import Settings
from app.core.security import issue_token
from app.main import create_app
from tests.fakes import (
    JWT_SECRET,
    NOW,
    ORGANIZATION_NAME,
    USER_PASSWORD,
    InMemoryUserRepository,
)

CREDENTIALS = {"email": "hr@acme.example", "password": USER_PASSWORD}


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def log_in(client: TestClient) -> dict[str, str]:
    return bearer(client.post("/api/v1/auth/login", json=CREDENTIALS).json()["access_token"])


def test_login_returns_a_bearer_token_that_expires_in_eight_hours(auth_client: TestClient) -> None:
    response = auth_client.post("/api/v1/auth/login", json=CREDENTIALS)

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] == issue_token(1, 1, JWT_SECRET, NOW).token
    assert body["expires_at"] == "2026-10-16T17:00:00Z"


def test_login_ignores_the_case_of_the_email(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/v1/auth/login", json={**CREDENTIALS, "email": "HR@Acme.Example"}
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "credentials",
    [
        {**CREDENTIALS, "password": "wrong password"},
        {**CREDENTIALS, "email": "nobody@acme.example"},
    ],
    ids=["wrong-password", "unknown-email"],
)
def test_login_rejects_bad_credentials_with_one_message(
    auth_client: TestClient, credentials: dict[str, str]
) -> None:
    response = auth_client.post("/api/v1/auth/login", json=credentials)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Email or password is incorrect"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({**CREDENTIALS, "email": "not-an-email"}, "valid email address"),
        ({**CREDENTIALS, "password": ""}, "at least 1 character"),
        ({**CREDENTIALS, "password": "x" * 257}, "at most 256 characters"),
        ({"email": "hr@acme.example"}, "Field required"),
        ({**CREDENTIALS, "organization_id": 2}, "Extra inputs are not permitted"),
    ],
    ids=["invalid-email", "empty-password", "password-too-long", "no-password", "extra-field"],
)
def test_login_validates_the_request(
    auth_client: TestClient, body: dict[str, Any], message: str
) -> None:
    response = auth_client.post("/api/v1/auth/login", json=body)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert message in response.text


def test_login_reports_missing_configuration_without_a_jwt_secret(
    user_repository: InMemoryUserRepository,
) -> None:
    app = create_app(Settings(_env_file=None, database_url=None, jwt_secret=None))
    app.dependency_overrides[get_user_repository] = lambda: user_repository

    with TestClient(app) as client:
        response = client.post("/api/v1/auth/login", json=CREDENTIALS)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Login is not configured; set JWT_SECRET"}


def test_me_returns_the_logged_in_user_and_their_organization(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/auth/me", headers=log_in(auth_client))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "name": "ACME HR",
        "email": "hr@acme.example",
        "organization": ORGANIZATION_NAME,
    }


def test_logout_ends_the_session(auth_client: TestClient) -> None:
    headers = log_in(auth_client)

    logout = auth_client.post("/api/v1/auth/logout", headers=headers)
    after_logout = auth_client.get("/api/v1/auth/me", headers=headers)

    assert logout.status_code == status.HTTP_204_NO_CONTENT
    assert after_logout.status_code == status.HTTP_401_UNAUTHORIZED
    assert after_logout.json() == {"detail": "Your session has ended; log in again"}


def test_logout_ends_every_session_of_the_user(auth_client: TestClient) -> None:
    first_device = log_in(auth_client)
    second_device = log_in(auth_client)

    auth_client.post("/api/v1/auth/logout", headers=first_device)

    response = auth_client.get("/api/v1/auth/me", headers=second_device)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_a_token_stops_working_once_it_expires(auth_client: TestClient) -> None:
    expired = issue_token(1, 1, JWT_SECRET, NOW - timedelta(hours=8)).token

    response = auth_client.get("/api/v1/auth/me", headers=bearer(expired))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
