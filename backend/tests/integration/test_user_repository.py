from sqlalchemy.orm import Session

from app.db.models import User
from app.repositories.users import SqlUserRepository, UserProfile
from tests.fakes import ORGANIZATION_NAME, make_user


def add_user(session: Session) -> User:
    user = make_user(id=None)
    session.add(user)
    session.commit()
    return user


def test_get_by_email_finds_the_user(session: Session) -> None:
    user = add_user(session)

    assert SqlUserRepository(session).get_by_email("hr@acme.example") is user


def test_get_by_email_returns_none_for_an_unknown_email(session: Session) -> None:
    add_user(session)

    assert SqlUserRepository(session).get_by_email("nobody@acme.example") is None


def test_save_persists_a_new_session_version(session: Session) -> None:
    user = add_user(session)
    user.session_version += 1

    SqlUserRepository(session).save(user)

    session.expire_all()  # the next read comes from the database
    stored = SqlUserRepository(session).get(user.id)
    assert stored is not None
    assert stored.session_version == 2


def test_get_profile_includes_the_organization_name(session: Session) -> None:
    user = add_user(session)

    profile = SqlUserRepository(session).get_profile(user.id)

    assert profile == UserProfile(
        name="ACME HR", email="hr@acme.example", organization=ORGANIZATION_NAME
    )


def test_get_profile_returns_none_for_an_unknown_user(session: Session) -> None:
    assert SqlUserRepository(session).get_profile(999) is None
