from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Path, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.domain.errors import NotAuthenticatedError
from app.repositories.employees import EmployeeRepository, SqlEmployeeRepository
from app.repositories.insights import InsightsRepository, SqlInsightsRepository
from app.repositories.payrolls import PayrollRepository, SqlPayrollRepository
from app.repositories.users import SqlUserRepository, UserRepository
from app.schemas.common import MAX_ID
from app.services.auth import CurrentUser, authenticate


class DatabaseNotConfiguredError(Exception):
    """The API was started without DATABASE_URL, so it cannot serve data."""


class AuthNotConfiguredError(Exception):
    """The API was started without JWT_SECRET, so it cannot issue or check login tokens."""


def get_session(request: Request) -> Iterator[Session]:
    session_factory: sessionmaker[Session] | None = request.app.state.session_factory
    if session_factory is None:
        raise DatabaseNotConfiguredError
    with session_factory() as session:
        yield session


def get_now() -> datetime:
    return datetime.now(UTC)


def get_jwt_secret(request: Request) -> str:
    settings: Settings = request.app.state.settings
    if settings.jwt_secret is None:
        raise AuthNotConfiguredError
    return settings.jwt_secret.get_secret_value()


SessionDep = Annotated[Session, Depends(get_session)]
NowDep = Annotated[datetime, Depends(get_now)]
JwtSecretDep = Annotated[str, Depends(get_jwt_secret)]
# auto_error=False: a missing token is reported as our own 401, not FastAPI's 403.
BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))]


def get_user_repository(session: SessionDep) -> UserRepository:
    return SqlUserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_current_user(
    credentials: BearerDep, users: UserRepositoryDep, secret: JwtSecretDep, now: NowDep
) -> CurrentUser:
    """The logged-in user, from the `Authorization: Bearer <token>` header."""
    if credentials is None:
        raise NotAuthenticatedError
    return authenticate(users, credentials.credentials, secret, now)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


# Data repositories only see the logged-in user's organization.
def get_employee_repository(session: SessionDep, user: CurrentUserDep) -> EmployeeRepository:
    return SqlEmployeeRepository(session, user.organization_id)


def get_payroll_repository(session: SessionDep, user: CurrentUserDep) -> PayrollRepository:
    return SqlPayrollRepository(session, user.organization_id)


def get_insights_repository(session: SessionDep, user: CurrentUserDep) -> InsightsRepository:
    return SqlInsightsRepository(session, user.organization_id)


EmployeeRepositoryDep = Annotated[EmployeeRepository, Depends(get_employee_repository)]
PayrollRepositoryDep = Annotated[PayrollRepository, Depends(get_payroll_repository)]
InsightsRepositoryDep = Annotated[InsightsRepository, Depends(get_insights_repository)]
IdPath = Annotated[int, Path(ge=1, le=MAX_ID)]
