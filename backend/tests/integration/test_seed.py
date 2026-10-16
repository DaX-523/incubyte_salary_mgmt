from datetime import date

import pytest
from sqlalchemy import Engine, func, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import verify_password
from app.db.models import Employee, Organization, Payroll, User
from app.seed.__main__ import main
from app.seed.generator import SeedData, generate_seed_data, recent_months
from app.seed.writer import SeedAbortedError, reset_demo_login, seed_database

TODAY = date(2026, 10, 14)
PASSWORD = "first-demo-password"
NEW_PASSWORD = "second-demo-password"


def small_dataset(seed: int = 3) -> SeedData:
    return generate_seed_data(
        employee_count=20, months=recent_months(TODAY, 3), today=TODAY, seed=seed
    )


def row_counts(engine: Engine) -> tuple[int | None, int | None]:
    with engine.connect() as connection:
        employees = connection.scalar(select(func.count()).select_from(Employee))
        payrolls = connection.scalar(select(func.count()).select_from(Payroll))
    return employees, payrolls


def demo_login(engine: Engine) -> User:
    with Session(engine) as session:
        return session.scalars(select(User).where(User.email == "hr@acme.example")).one()


def employee_organizations(engine: Engine) -> set[str]:
    with engine.connect() as connection:
        return set(
            connection.scalars(
                select(Organization.name).join(
                    Employee, Employee.organization_id == Organization.id
                )
            )
        )


def test_seed_inserts_all_employees_and_payrolls(engine: Engine) -> None:
    data = small_dataset()

    seed_database(engine, data, demo_password=PASSWORD)

    assert row_counts(engine) == (len(data.employees), len(data.payrolls))


def test_seed_links_payrolls_to_the_right_employee(engine: Engine) -> None:
    data = small_dataset()
    first_employee = data.employees[0]
    expected_months = sorted(p.month for p in data.payrolls if p.employee_index == 0)

    seed_database(engine, data, demo_password=PASSWORD)

    with engine.connect() as connection:
        months = connection.scalars(
            select(Payroll.month)
            .join(Employee, Employee.id == Payroll.employee_id)
            .where(Employee.email == first_employee.email)
            .order_by(Payroll.month)
        ).all()
    assert months == expected_months


def test_seed_refuses_to_mix_into_existing_data(engine: Engine) -> None:
    seed_database(engine, small_dataset(), demo_password=PASSWORD)

    with pytest.raises(SeedAbortedError, match="--reset"):
        seed_database(engine, small_dataset(seed=4), demo_password=PASSWORD)


def test_seed_with_reset_replaces_existing_data(engine: Engine) -> None:
    seed_database(engine, small_dataset(), demo_password=PASSWORD)
    replacement = small_dataset(seed=4)

    seed_database(engine, replacement, demo_password=PASSWORD, reset=True)

    with engine.connect() as connection:
        emails = set(connection.scalars(text("SELECT email FROM employees")))
    assert emails == {employee.email for employee in replacement.employees}


def test_seed_puts_every_employee_in_acme(engine: Engine) -> None:
    seed_database(engine, small_dataset(), demo_password=PASSWORD)

    assert employee_organizations(engine) == {"ACME"}


def test_seed_creates_an_acme_demo_login_with_the_given_password(engine: Engine) -> None:
    seed_database(engine, small_dataset(), demo_password=PASSWORD)

    user = demo_login(engine)
    with Session(engine) as session:
        organization = session.get_one(Organization, user.organization_id)
    assert organization.name == "ACME"
    assert verify_password(PASSWORD, user.password_hash)


def test_reseeding_gives_the_demo_login_a_new_password_and_ends_its_sessions(
    engine: Engine,
) -> None:
    seed_database(engine, small_dataset(), demo_password=PASSWORD)

    seed_database(engine, small_dataset(seed=4), demo_password=NEW_PASSWORD, reset=True)

    user = demo_login(engine)
    assert verify_password(NEW_PASSWORD, user.password_hash)
    assert not verify_password(PASSWORD, user.password_hash)
    assert user.session_version == 2


def test_reset_demo_login_leaves_employees_alone(engine: Engine) -> None:
    seed_database(engine, small_dataset(), demo_password=PASSWORD)
    counts_before = row_counts(engine)

    reset_demo_login(engine, NEW_PASSWORD)

    assert row_counts(engine) == counts_before
    assert verify_password(NEW_PASSWORD, demo_login(engine).password_hash)


def test_reset_demo_login_works_on_an_empty_database(engine: Engine) -> None:
    reset_demo_login(engine, PASSWORD)

    assert verify_password(PASSWORD, demo_login(engine).password_hash)


def test_cli_migrates_and_seeds(
    engine: Engine, database_url: str, capsys: pytest.CaptureFixture[str]
) -> None:
    settings = Settings(_env_file=None, database_url=database_url)

    exit_code = main(
        ["--employees", "5", "--months", "2"],
        settings=settings,
        today=TODAY,
        new_password=lambda: PASSWORD,
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert row_counts(engine)[0] == 5
    assert "Seeded 5 employees" in output
    assert f"Demo login: hr@acme.example / {PASSWORD}" in output


def test_cli_can_reset_only_the_demo_login(
    engine: Engine, database_url: str, capsys: pytest.CaptureFixture[str]
) -> None:
    settings = Settings(_env_file=None, database_url=database_url)
    main(["--employees", "5"], settings=settings, today=TODAY, new_password=lambda: PASSWORD)

    exit_code = main(["--demo-login-only"], settings=settings, new_password=lambda: NEW_PASSWORD)

    assert exit_code == 0
    assert row_counts(engine)[0] == 5
    assert verify_password(NEW_PASSWORD, demo_login(engine).password_hash)
    assert f"Demo login: hr@acme.example / {NEW_PASSWORD}" in capsys.readouterr().out


def test_cli_fails_without_reset_when_data_exists(
    engine: Engine, database_url: str, capsys: pytest.CaptureFixture[str]
) -> None:
    settings = Settings(_env_file=None, database_url=database_url)
    main(["--employees", "5"], settings=settings, today=TODAY, new_password=lambda: PASSWORD)

    exit_code = main(
        ["--employees", "5"], settings=settings, today=TODAY, new_password=lambda: PASSWORD
    )

    assert exit_code == 1
    assert "Seed aborted" in capsys.readouterr().err
