"""Logging in, recognizing a logged-in user on each request, and logging out."""

from dataclasses import dataclass
from datetime import datetime

from app.core.security import IssuedToken, hash_password, issue_token, read_token, verify_password
from app.domain.errors import InvalidCredentialsError, SessionEndedError
from app.repositories.users import UserProfile, UserRepository

# Checked when the email is unknown, so that takes as long as a wrong password and response times
# don't reveal which emails have an account.
_DUMMY_PASSWORD_HASH = hash_password("not anyone's password")


@dataclass(frozen=True)
class CurrentUser:
    user_id: int
    organization_id: int


def login(
    users: UserRepository, email: str, password: str, secret: str, now: datetime
) -> IssuedToken:
    user = users.get_by_email(email)
    if user is None:
        verify_password(password, _DUMMY_PASSWORD_HASH)
        raise InvalidCredentialsError
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    return issue_token(user.id, user.session_version, secret, now)


def authenticate(users: UserRepository, token: str, secret: str, now: datetime) -> CurrentUser:
    """The user a token belongs to, unless it has expired or they have logged out since."""
    claims = read_token(token, secret, now)
    user = users.get(claims.user_id)
    if user is None or user.session_version != claims.session_version:
        raise SessionEndedError
    return CurrentUser(user_id=user.id, organization_id=user.organization_id)


def logout(users: UserRepository, current_user: CurrentUser) -> None:
    """Ends every session of the user: tokens carry the old version, so none of them work now."""
    user = users.get(current_user.user_id)
    if user is None:
        raise SessionEndedError
    user.session_version += 1
    users.save(user)


def get_profile(users: UserRepository, current_user: CurrentUser) -> UserProfile:
    profile = users.get_profile(current_user.user_id)
    if profile is None:
        raise SessionEndedError
    return profile
