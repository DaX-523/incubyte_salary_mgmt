from dataclasses import asdict

from sqlalchemy import Engine, func, insert, select, text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import Employee, Organization, Payroll, User
from app.seed.generator import SeedData

DEMO_ORGANIZATION = "ACME"
DEMO_LOGIN_EMAIL = "hr@acme.example"
DEMO_LOGIN_NAME = "ACME HR"


class SeedAbortedError(Exception):
    """Raised instead of mixing demo data into a database that already has employees."""


def seed_database(
    engine: Engine, data: SeedData, *, demo_password: str, reset: bool = False
) -> None:
    """Insert `data` into the demo organization in a single transaction, and set up the demo login
    with `demo_password`. With `reset`, replace existing employees and payrolls first."""
    with Session(engine) as session, session.begin():
        organization_id = _demo_organization_id(session)
        existing = session.scalar(select(func.count()).select_from(Employee))
        if existing and not reset:
            raise SeedAbortedError(
                f"employees already has {existing} rows; re-run with --reset to replace them"
            )
        if reset:
            session.execute(text("TRUNCATE payrolls, employees RESTART IDENTITY"))

        employee_ids = session.scalars(
            insert(Employee).returning(Employee.id, sort_by_parameter_order=True),
            [
                asdict(employee) | {"organization_id": organization_id}
                for employee in data.employees
            ],
        ).all()
        if data.payrolls:
            session.execute(
                insert(Payroll),
                [
                    {
                        "employee_id": employee_ids[payroll.employee_index],
                        "month": payroll.month,
                        "base": payroll.base,
                        "bonus": payroll.bonus,
                        "esops": payroll.esops,
                        "currency": payroll.currency,
                        "payment_method": payroll.payment_method,
                        "created_at": payroll.paid_at,
                        "updated_at": payroll.paid_at,
                    }
                    for payroll in data.payrolls
                ],
            )
        _set_demo_login(session, organization_id, demo_password)


def reset_demo_login(engine: Engine, password: str) -> None:
    """Create the demo login, or give it a new password, leaving all other data alone."""
    with Session(engine) as session, session.begin():
        _set_demo_login(session, _demo_organization_id(session), password)


def _demo_organization_id(session: Session) -> int:
    existing = session.scalar(select(Organization.id).where(Organization.name == DEMO_ORGANIZATION))
    if existing is not None:
        return existing
    organization = Organization(name=DEMO_ORGANIZATION)
    session.add(organization)
    session.flush()
    return organization.id


def _set_demo_login(session: Session, organization_id: int, password: str) -> None:
    user = session.scalar(select(User).where(User.email == DEMO_LOGIN_EMAIL))
    if user is None:
        session.add(
            User(
                organization_id=organization_id,
                email=DEMO_LOGIN_EMAIL,
                name=DEMO_LOGIN_NAME,
                password_hash=hash_password(password),
            )
        )
        return
    user.password_hash = hash_password(password)
    # A new password ends the sessions that were started with the old one.
    user.session_version += 1
