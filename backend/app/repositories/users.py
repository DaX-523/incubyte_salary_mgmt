from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Organization, User


@dataclass(frozen=True)
class UserProfile:
    name: str
    email: str
    organization: str


class UserRepository(Protocol):
    def get(self, user_id: int) -> User | None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def save(self, user: User) -> User: ...

    def get_profile(self, user_id: int) -> UserProfile | None: ...


class SqlUserRepository:
    """Not limited to one organization: logging in has to find the user before it knows theirs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: int) -> User | None:
        return self._session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self._session.scalar(select(User).where(User.email == email))

    def save(self, user: User) -> User:
        self._session.commit()
        self._session.refresh(user)
        return user

    def get_profile(self, user_id: int) -> UserProfile | None:
        row = self._session.execute(
            select(User.name, User.email, Organization.name)
            .join(Organization, Organization.id == User.organization_id)
            .where(User.id == user_id)
        ).one_or_none()
        if row is None:
            return None
        name, email, organization = row
        return UserProfile(name=name, email=email, organization=organization)
