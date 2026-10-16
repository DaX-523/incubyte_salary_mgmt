from fastapi import APIRouter, status

from app.api.dependencies import CurrentUserDep, JwtSecretDep, NowDep, UserRepositoryDep
from app.schemas.auth import LoginRequest, ProfileOut, TokenOut
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    body: LoginRequest, users: UserRepositoryDep, secret: JwtSecretDep, now: NowDep
) -> TokenOut:
    """Exchanges an email and password for a token to send as `Authorization: Bearer <token>`."""
    issued = auth_service.login(users, body.email, body.password, secret, now)
    return TokenOut(access_token=issued.token, expires_at=issued.expires_at)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: CurrentUserDep, users: UserRepositoryDep) -> None:
    """Ends all of the user's sessions: every token issued so far stops working."""
    auth_service.logout(users, current_user)


@router.get("/me")
def read_profile(current_user: CurrentUserDep, users: UserRepositoryDep) -> ProfileOut:
    profile = auth_service.get_profile(users, current_user)
    return ProfileOut(name=profile.name, email=profile.email, organization=profile.organization)
