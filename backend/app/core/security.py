"""Password hashing and login tokens: plain functions, with the secret and the clock passed in."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.domain.errors import SessionEndedError

# A working day: long enough not to interrupt work, short enough that a leaked token soon expires.
TOKEN_LIFETIME = timedelta(hours=8)
TOKEN_ALGORITHM = "HS256"
REQUIRED_CLAIMS = ["sub", "ver", "iat", "exp"]

# Argon2id with pwdlib's recommended settings: deliberately slow, with a random salt per password.
_password_hasher = PasswordHash.recommended()


@dataclass(frozen=True)
class IssuedToken:
    token: str
    expires_at: datetime


@dataclass(frozen=True)
class TokenClaims:
    user_id: int
    session_version: int


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hasher.verify(password, password_hash)


def issue_token(user_id: int, session_version: int, secret: str, now: datetime) -> IssuedToken:
    expires_at = now + TOKEN_LIFETIME
    claims = {"sub": str(user_id), "ver": session_version, "iat": now, "exp": expires_at}
    return IssuedToken(jwt.encode(claims, secret, algorithm=TOKEN_ALGORITHM), expires_at)


def read_token(token: str, secret: str, now: datetime) -> TokenClaims:
    """The token's claims, if it was signed with `secret` and has not expired by `now`."""
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[TOKEN_ALGORITHM],
            # Expiry is checked below against the injected clock instead of the system clock.
            options={"require": REQUIRED_CLAIMS, "verify_exp": False, "verify_iat": False},
        )
    except jwt.InvalidTokenError as error:
        raise SessionEndedError from error
    if datetime.fromtimestamp(claims["exp"], UTC) <= now:
        raise SessionEndedError
    return TokenClaims(user_id=int(claims["sub"]), session_version=claims["ver"])
