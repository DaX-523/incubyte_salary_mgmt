from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Employee, Payroll
from app.domain.errors import DuplicatePayrollError
from app.repositories.insights import JobTitlePayRow, PaidCount, SqlInsightsRepository
from app.repositories.payrolls import SqlPayrollRepository
from app.repositories.population import MonthFilter
from tests.fakes import ORGANIZATION_ID, make_employee, make_payroll

OCTOBER = date(2026, 10, 1)
JOINED_LAST_YEAR = datetime(2025, 1, 1, 9, 0, tzinfo=UTC)


def add_employee(session: Session, name: str, **overrides: Any) -> Employee:
    fields = {"name": name, "email": f"{name}@example.com", "created_at": JOINED_LAST_YEAR}
    employee = make_employee(**(fields | overrides))
    session.add(employee)
    session.commit()
    return employee


def pay(session: Session, employee: Employee, month: date = OCTOBER) -> None:
    session.add(make_payroll(employee_id=employee.id, month=month))
    session.commit()


def test_payroll_add_returns_the_stored_payroll(session: Session) -> None:
    employee = add_employee(session, "ada")

    payroll = SqlPayrollRepository(session, ORGANIZATION_ID).add(
        make_payroll(employee_id=employee.id)
    )

    assert payroll.id == 1
    assert payroll.created_at is not None


def test_payroll_add_rejects_a_second_payroll_for_the_month(session: Session) -> None:
    employee = add_employee(session, "ada")
    repository = SqlPayrollRepository(session, ORGANIZATION_ID)
    repository.add(make_payroll(employee_id=employee.id))

    with pytest.raises(DuplicatePayrollError, match="already has a payroll for 2026-10"):
        repository.add(make_payroll(employee_id=employee.id))

    assert repository.get(1) is not None


def test_payroll_add_lets_other_constraint_violations_through(session: Session) -> None:
    with pytest.raises(IntegrityError, match="fk_payrolls_employee_id_employees"):
        SqlPayrollRepository(session, ORGANIZATION_ID).add(make_payroll(employee_id=404))


def test_payroll_save_persists_changes(session: Session) -> None:
    employee = add_employee(session, "ada")
    repository = SqlPayrollRepository(session, ORGANIZATION_ID)
    payroll = repository.add(make_payroll(employee_id=employee.id))

    payroll.bonus = Decimal("300.00")
    repository.save(payroll)
    session.expire_all()

    assert session.scalar(select(Payroll.bonus)) == Decimal("300.00")


def test_payroll_get_returns_none_for_an_unknown_id(session: Session) -> None:
    assert SqlPayrollRepository(session, ORGANIZATION_ID).get(404) is None


def test_count_paid_uses_the_same_population_as_the_monthly_list(session: Session) -> None:
    paid = add_employee(session, "paid")
    add_employee(session, "unpaid")
    left_after_pay = add_employee(session, "left-after-pay", is_active=False)
    add_employee(session, "left-before", is_active=False)
    add_employee(session, "joins-later", created_at=datetime(2026, 11, 2, tzinfo=UTC))
    pay(session, paid)
    pay(session, left_after_pay)

    counts = SqlInsightsRepository(session, ORGANIZATION_ID).count_paid(MonthFilter(OCTOBER))

    assert counts == PaidCount(total=3, paid=2)


@pytest.mark.parametrize(
    ("month_filter", "expected"),
    [
        (MonthFilter(OCTOBER, country="IN"), PaidCount(total=1, paid=0)),
        (MonthFilter(OCTOBER, job_title="Accountant"), PaidCount(total=1, paid=1)),
        (MonthFilter(date(2026, 9, 1)), PaidCount(total=2, paid=0)),
    ],
    ids=["by-country", "by-job-title", "another-month"],
)
def test_count_paid_applies_the_filters(
    session: Session, month_filter: MonthFilter, expected: PaidCount
) -> None:
    accountant = add_employee(session, "ada", job_title="Accountant", department="Finance")
    add_employee(session, "alan", country="IN")
    pay(session, accountant)

    assert SqlInsightsRepository(session, ORGANIZATION_ID).count_paid(month_filter) == expected


def test_count_paid_is_zero_when_nobody_is_on_the_books(session: Session) -> None:
    assert SqlInsightsRepository(session, ORGANIZATION_ID).count_paid(
        MonthFilter(OCTOBER)
    ) == PaidCount(0, 0)


def test_pay_by_job_title_reports_ranges_for_active_employees_in_one_country(
    session: Session,
) -> None:
    add_employee(session, "a", monthly_salary=Decimal("5000.00"))
    add_employee(session, "b", monthly_salary=Decimal("6200.00"))
    add_employee(session, "c", monthly_salary=Decimal("9900.00"), is_active=False)
    add_employee(session, "d", monthly_salary=Decimal("99000.00"), country="IN")
    add_employee(
        session,
        "e",
        monthly_salary=Decimal("4100.00"),
        job_title="Accountant",
        department="Finance",
    )

    rows = SqlInsightsRepository(session, ORGANIZATION_ID).pay_by_job_title("GB")

    assert rows == [
        JobTitlePayRow(
            "Software Engineer", "Engineering", 2, Decimal("5000.00"), Decimal("6200.00")
        ),
        JobTitlePayRow("Accountant", "Finance", 1, Decimal("4100.00"), Decimal("4100.00")),
    ]


def test_pay_by_job_title_is_empty_for_a_country_without_employees(session: Session) -> None:
    add_employee(session, "ada")

    assert SqlInsightsRepository(session, ORGANIZATION_ID).pay_by_job_title("JP") == []
