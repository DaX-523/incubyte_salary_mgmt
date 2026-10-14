from datetime import UTC, datetime
from typing import Any

import pytest
from alembic import command
from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import DataError, IntegrityError

from app.db.migrate import alembic_config, run_migrations

INSERT_EMPLOYEE = text(
    "INSERT INTO employees (name, email, monthly_salary, country, department, job_title) "
    "VALUES (:name, :email, :monthly_salary, :country, :department, :job_title) RETURNING id"
)
INSERT_PAYROLL = text(
    "INSERT INTO payrolls (employee_id, month, base, currency, payment_method) "
    "VALUES (:employee_id, :month, :base, :currency, :payment_method)"
)
VALID_EMPLOYEE = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "monthly_salary": "5000.00",
    "country": "GB",
    "department": "Engineering",
    "job_title": "Software Engineer",
}
VALID_PAYROLL = {
    "month": "2026-10-01",
    "base": "5000.00",
    "currency": "GBP",
    "payment_method": "bank_transfer",
}


def test_migrated_schema_matches_the_models(migrated_engine: Engine, database_url: str) -> None:
    command.check(alembic_config(database_url))  # raises if models and migrations differ


def test_migrations_downgrade_and_upgrade_cleanly(
    migrated_engine: Engine, database_url: str
) -> None:
    command.downgrade(alembic_config(database_url), "base")
    tables_after_downgrade = set(inspect(migrated_engine).get_table_names())
    run_migrations(database_url)
    tables_after_upgrade = set(inspect(migrated_engine).get_table_names())

    assert tables_after_downgrade == {"alembic_version"}
    assert tables_after_upgrade == {"alembic_version", "employees", "payrolls"}


def test_running_migrations_again_is_a_no_op(migrated_engine: Engine, database_url: str) -> None:
    run_migrations(database_url)

    with migrated_engine.connect() as connection:
        version = connection.scalar(text("SELECT version_num FROM alembic_version"))
    assert version == "0002"


def test_accepts_a_valid_employee_and_payroll(engine: Engine) -> None:
    with engine.begin() as connection:
        employee_id = connection.scalar(INSERT_EMPLOYEE, VALID_EMPLOYEE)
        connection.execute(INSERT_PAYROLL, {**VALID_PAYROLL, "employee_id": employee_id})

        payroll = connection.execute(text("SELECT bonus, esops FROM payrolls")).one()
    assert payroll == (0, 0)


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        ({"monthly_salary": "-0.01"}, IntegrityError),
        ({"country": "gb"}, IntegrityError),
        ({"country": "GBR"}, DataError),
        ({"job_title": None}, IntegrityError),
    ],
    ids=["negative-salary", "lowercase-country", "three-letter-country", "missing-job-title"],
)
def test_rejects_invalid_employees(
    engine: Engine, overrides: dict[str, Any], error: type[Exception]
) -> None:
    with pytest.raises(error), engine.begin() as connection:
        connection.execute(INSERT_EMPLOYEE, {**VALID_EMPLOYEE, **overrides})


def test_rejects_duplicate_email(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(INSERT_EMPLOYEE, VALID_EMPLOYEE)

    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(INSERT_EMPLOYEE, VALID_EMPLOYEE)


@pytest.mark.parametrize(
    "overrides",
    [
        {"month": "2026-10-15"},
        {"base": "-1.00"},
        {"currency": "gbp"},
        {"payment_method": "crypto"},
        {"payment_method": "cash"},
        {"payment_method": "cheque"},
        {"employee_id": 999_999},
    ],
    ids=[
        "month-not-first-day",
        "negative-base",
        "lowercase-currency",
        "unknown-method",
        "retired-method-cash",
        "retired-method-cheque",
        "no-employee",
    ],
)
def test_rejects_invalid_payrolls(engine: Engine, overrides: dict[str, Any]) -> None:
    with engine.begin() as connection:
        employee_id = connection.scalar(INSERT_EMPLOYEE, VALID_EMPLOYEE)

    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            INSERT_PAYROLL, {**VALID_PAYROLL, "employee_id": employee_id, **overrides}
        )


def test_rejects_second_payroll_for_the_same_employee_and_month(engine: Engine) -> None:
    with engine.begin() as connection:
        employee_id = connection.scalar(INSERT_EMPLOYEE, VALID_EMPLOYEE)
        connection.execute(INSERT_PAYROLL, {**VALID_PAYROLL, "employee_id": employee_id})

    with pytest.raises(IntegrityError, match="uq_payrolls_employee_id_month"), engine.begin() as c:
        c.execute(INSERT_PAYROLL, {**VALID_PAYROLL, "employee_id": employee_id})


def test_cannot_delete_an_employee_with_payroll_history(engine: Engine) -> None:
    with engine.begin() as connection:
        employee_id = connection.scalar(INSERT_EMPLOYEE, VALID_EMPLOYEE)
        connection.execute(INSERT_PAYROLL, {**VALID_PAYROLL, "employee_id": employee_id})

    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(text("DELETE FROM employees WHERE id = :id"), {"id": employee_id})


def test_upgrade_to_0002_migrates_existing_rows(engine: Engine, database_url: str) -> None:
    config = alembic_config(database_url)
    command.downgrade(config, "0001")
    with engine.begin() as connection:
        employee_id = connection.scalar(
            text(
                "INSERT INTO employees (name, email, monthly_salary, country, department) "
                "VALUES ('Ada Lovelace', 'ada@example.com', 5000, 'GB', 'Engineering') "
                "RETURNING id"
            )
        )
        connection.execute(
            text(
                "INSERT INTO payrolls (employee_id, month, base, currency, payment_method) VALUES "
                "(:id, '2026-08-01', 5000, 'GBP', 'cash'), "
                "(:id, '2026-09-01', 5000, 'GBP', 'cheque'), "
                "(:id, '2026-10-01', 5000, 'GBP', 'digital_wallet')"
            ),
            {"id": employee_id},
        )

    command.upgrade(config, "head")

    with engine.connect() as connection:
        job_title = connection.scalar(text("SELECT job_title FROM employees"))
        payment_methods = connection.scalars(
            text("SELECT payment_method FROM payrolls ORDER BY month")
        ).all()
    assert job_title == "Unassigned"
    assert payment_methods == ["bank_transfer", "bank_transfer", "digital_wallet"]


def test_downgrade_from_0002_recomputes_last_transaction(engine: Engine, database_url: str) -> None:
    with engine.begin() as connection:
        employee_id = connection.scalar(INSERT_EMPLOYEE, VALID_EMPLOYEE)
        connection.execute(
            text(
                "INSERT INTO payrolls (employee_id, month, base, currency, payment_method, "
                "created_at) VALUES "
                "(:id, '2026-09-01', 5000, 'GBP', 'bank_transfer', '2026-09-25T09:00:00Z'), "
                "(:id, '2026-10-01', 5000, 'GBP', 'bank_transfer', '2026-10-14T09:00:00Z')"
            ),
            {"id": employee_id},
        )
    config = alembic_config(database_url)

    command.downgrade(config, "0001")
    with engine.connect() as connection:
        last_transaction_at = connection.scalar(text("SELECT last_transaction_at FROM employees"))
    command.upgrade(config, "head")

    assert last_transaction_at == datetime(2026, 10, 14, 9, 0, tzinfo=UTC)
