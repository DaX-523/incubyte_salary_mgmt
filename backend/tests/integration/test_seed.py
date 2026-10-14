from datetime import date

import pytest
from sqlalchemy import Engine, func, select, text

from app.core.config import Settings
from app.db.models import Employee, Payroll
from app.seed.__main__ import main
from app.seed.generator import SeedData, generate_seed_data, recent_months
from app.seed.writer import SeedAbortedError, seed_database

TODAY = date(2026, 10, 14)


def small_dataset(seed: int = 3) -> SeedData:
    return generate_seed_data(
        employee_count=20, months=recent_months(TODAY, 3), today=TODAY, seed=seed
    )


def row_counts(engine: Engine) -> tuple[int | None, int | None]:
    with engine.connect() as connection:
        employees = connection.scalar(select(func.count()).select_from(Employee))
        payrolls = connection.scalar(select(func.count()).select_from(Payroll))
    return employees, payrolls


def test_seed_inserts_all_employees_and_payrolls(engine: Engine) -> None:
    data = small_dataset()

    seed_database(engine, data)

    assert row_counts(engine) == (len(data.employees), len(data.payrolls))


def test_seed_links_payrolls_to_the_right_employee(engine: Engine) -> None:
    data = small_dataset()
    first_employee = data.employees[0]
    expected_months = sorted(p.month for p in data.payrolls if p.employee_index == 0)

    seed_database(engine, data)

    with engine.connect() as connection:
        months = connection.scalars(
            select(Payroll.month)
            .join(Employee, Employee.id == Payroll.employee_id)
            .where(Employee.email == first_employee.email)
            .order_by(Payroll.month)
        ).all()
    assert months == expected_months


def test_seed_refuses_to_mix_into_existing_data(engine: Engine) -> None:
    seed_database(engine, small_dataset())

    with pytest.raises(SeedAbortedError, match="--reset"):
        seed_database(engine, small_dataset(seed=4))


def test_seed_with_reset_replaces_existing_data(engine: Engine) -> None:
    seed_database(engine, small_dataset())
    replacement = small_dataset(seed=4)

    seed_database(engine, replacement, reset=True)

    with engine.connect() as connection:
        emails = set(connection.scalars(text("SELECT email FROM employees")))
    assert emails == {employee.email for employee in replacement.employees}


def test_cli_migrates_and_seeds(
    engine: Engine, database_url: str, capsys: pytest.CaptureFixture[str]
) -> None:
    settings = Settings(_env_file=None, database_url=database_url)

    exit_code = main(["--employees", "5", "--months", "2"], settings=settings, today=TODAY)

    assert exit_code == 0
    assert row_counts(engine)[0] == 5
    assert "Seeded 5 employees" in capsys.readouterr().out


def test_cli_fails_without_reset_when_data_exists(
    engine: Engine, database_url: str, capsys: pytest.CaptureFixture[str]
) -> None:
    settings = Settings(_env_file=None, database_url=database_url)
    main(["--employees", "5"], settings=settings, today=TODAY)

    exit_code = main(["--employees", "5"], settings=settings, today=TODAY)

    assert exit_code == 1
    assert "Seed aborted" in capsys.readouterr().err
