import base64
import json
from datetime import datetime, timedelta

import jwt
import pytest

from app.core.security import (
    TokenClaims,
    hash_password,
    issue_token,
    read_token,
    verify_password,
)
from app.domain.errors import SessionEndedError
from tests.fakes import JWT_SECRET, NOW

EIGHT_HOURS_LATER = NOW + timedelta(hours=8)
OTHER_SECRET = "another-secret-that-is-at-least-32-chars"
VALID_TOKEN = issue_token(7, 3, JWT_SECRET, NOW).token


def with_payload(token: str, payload: dict[str, object]) -> str:
    """The token with its claims swapped for `payload`, keeping the original signature."""
    header, _, signature = token.split(".")
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{encoded}.{signature}"


def test_a_password_hash_is_an_argon2_hash_not_the_password() -> None:
    password_hash = hash_password("correct horse")

    assert password_hash.startswith("$argon2id$")
    assert "correct horse" not in password_hash


def test_the_right_password_verifies() -> None:
    assert verify_password("correct horse", hash_password("correct horse"))


def test_a_wrong_password_does_not_verify() -> None:
    assert not verify_password("correct horsE", hash_password("correct horse"))


def test_the_same_password_hashes_differently_each_time() -> None:
    assert hash_password("correct horse") != hash_password("correct horse")


def test_a_token_carries_the_user_and_session_version() -> None:
    assert read_token(VALID_TOKEN, JWT_SECRET, NOW) == TokenClaims(user_id=7, session_version=3)


def test_a_token_expires_eight_hours_after_it_is_issued() -> None:
    assert issue_token(7, 3, JWT_SECRET, NOW).expires_at == EIGHT_HOURS_LATER


def test_a_token_is_accepted_until_just_before_it_expires() -> None:
    claims = read_token(VALID_TOKEN, JWT_SECRET, EIGHT_HOURS_LATER - timedelta(seconds=1))

    assert claims.user_id == 7


@pytest.mark.parametrize(
    ("token", "now"),
    [
        (VALID_TOKEN, EIGHT_HOURS_LATER),
        (VALID_TOKEN, NOW + timedelta(days=30)),
        (issue_token(7, 3, OTHER_SECRET, NOW).token, NOW),
        (with_payload(VALID_TOKEN, {"sub": "1", "ver": 3, "iat": 0, "exp": 9_999_999_999}), NOW),
        (jwt.encode({"sub": "7", "iat": NOW, "exp": EIGHT_HOURS_LATER}, JWT_SECRET), NOW),
        (jwt.encode({"ver": 3, "iat": NOW, "exp": EIGHT_HOURS_LATER}, JWT_SECRET), NOW),
        (jwt.encode({"sub": "7", "ver": 3, "iat": NOW}, JWT_SECRET), NOW),
        (
            jwt.encode({"sub": "7", "ver": 3, "iat": NOW, "exp": EIGHT_HOURS_LATER}, None, "none"),
            NOW,
        ),
        ("not-a-token", NOW),
    ],
    ids=[
        "at-expiry",
        "long-expired",
        "signed-with-another-secret",
        "claims-tampered-with",
        "no-session-version",
        "no-user",
        "no-expiry",
        "unsigned",
        "not-a-jwt",
    ],
)
def test_a_token_is_rejected(token: str, now: datetime) -> None:
    with pytest.raises(SessionEndedError, match="log in again"):
        read_token(token, JWT_SECRET, now)
