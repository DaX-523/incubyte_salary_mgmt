from datetime import timedelta

import pytest

from app.core.security import TokenClaims, read_token
from app.domain.errors import InvalidCredentialsError, SessionEndedError
from app.repositories.users import UserProfile
from app.services.auth import CurrentUser, authenticate, get_profile, login, logout
from tests.fakes import (
    JWT_SECRET,
    NOW,
    ORGANIZATION_ID,
    ORGANIZATION_NAME,
    USER_PASSWORD,
    InMemoryUserRepository,
)

EMAIL = "hr@acme.example"
LOGGED_IN = CurrentUser(user_id=1, organization_id=ORGANIZATION_ID)


def log_in(users: InMemoryUserRepository) -> str:
    return login(users, EMAIL, USER_PASSWORD, JWT_SECRET, NOW).token


def test_login_issues_a_token_for_the_user_and_their_session_version(
    user_repository: InMemoryUserRepository,
) -> None:
    token = log_in(user_repository)

    assert read_token(token, JWT_SECRET, NOW) == TokenClaims(user_id=1, session_version=1)


def test_login_issues_a_token_that_expires_eight_hours_later(
    user_repository: InMemoryUserRepository,
) -> None:
    issued = login(user_repository, EMAIL, USER_PASSWORD, JWT_SECRET, NOW)

    assert issued.expires_at == NOW + timedelta(hours=8)


@pytest.mark.parametrize(
    ("email", "password"),
    [
        (EMAIL, "wrong password"),
        (EMAIL, ""),
        ("nobody@acme.example", USER_PASSWORD),
    ],
    ids=["wrong-password", "empty-password", "unknown-email"],
)
def test_login_rejects_bad_credentials_without_saying_which_part_is_wrong(
    user_repository: InMemoryUserRepository, email: str, password: str
) -> None:
    with pytest.raises(InvalidCredentialsError, match=r"^Email or password is incorrect$"):
        login(user_repository, email, password, JWT_SECRET, NOW)


def test_authenticate_returns_the_user_and_their_organization(
    user_repository: InMemoryUserRepository,
) -> None:
    token = log_in(user_repository)

    assert authenticate(user_repository, token, JWT_SECRET, NOW) == LOGGED_IN


def test_authenticate_rejects_a_token_from_before_the_user_logged_out(
    user_repository: InMemoryUserRepository,
) -> None:
    token = log_in(user_repository)
    logout(user_repository, LOGGED_IN)

    with pytest.raises(SessionEndedError):
        authenticate(user_repository, token, JWT_SECRET, NOW)


def test_authenticate_rejects_the_token_of_a_user_who_no_longer_exists(
    user_repository: InMemoryUserRepository,
) -> None:
    token = log_in(user_repository)
    user_repository.users.clear()

    with pytest.raises(SessionEndedError):
        authenticate(user_repository, token, JWT_SECRET, NOW)


def test_authenticate_rejects_an_expired_token(user_repository: InMemoryUserRepository) -> None:
    token = log_in(user_repository)

    with pytest.raises(SessionEndedError):
        authenticate(user_repository, token, JWT_SECRET, NOW + timedelta(hours=8))


def test_logout_bumps_the_session_version_and_saves_it(
    user_repository: InMemoryUserRepository,
) -> None:
    logout(user_repository, LOGGED_IN)

    assert user_repository.users[1].session_version == 2
    assert user_repository.save_count == 1


def test_a_new_login_after_logout_works(user_repository: InMemoryUserRepository) -> None:
    logout(user_repository, LOGGED_IN)

    token = log_in(user_repository)

    assert authenticate(user_repository, token, JWT_SECRET, NOW) == LOGGED_IN


def test_logout_of_a_user_who_no_longer_exists_is_rejected() -> None:
    with pytest.raises(SessionEndedError):
        logout(InMemoryUserRepository(), LOGGED_IN)


def test_get_profile_returns_the_name_email_and_organization(
    user_repository: InMemoryUserRepository,
) -> None:
    assert get_profile(user_repository, LOGGED_IN) == UserProfile(
        name="ACME HR", email=EMAIL, organization=ORGANIZATION_NAME
    )


def test_get_profile_of_a_user_who_no_longer_exists_is_rejected() -> None:
    with pytest.raises(SessionEndedError):
        get_profile(InMemoryUserRepository(), LOGGED_IN)
