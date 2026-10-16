from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Employee
from app.domain.errors import DuplicateEmailError
from app.repositories.employees import SqlEmployeeRepository
from app.schemas.employees import EmployeeSortField, MonthlyEmployeeQuery, SortOrder
from tests.fakes import ORGANIZATION_ID, make_employee, make_payroll

OCTOBER = date(2026, 10, 1)
JOINED_LAST_YEAR = datetime(2025, 1, 1, 9, 0, tzinfo=UTC)


def add_employee(session: Session, **overrides: Any) -> Employee:
    """Insert an employee who joined last year unless told otherwise."""
    fields = {"created_at": JOINED_LAST_YEAR, "email": f"{overrides.get('name', 'ada')}@x.com"}
    employee = make_employee(**(fields | overrides))
    session.add(employee)
    session.commit()
    return employee


def ids_for(session: Session, **query: Any) -> list[int]:
    result = SqlEmployeeRepository(session, ORGANIZATION_ID).list_for_month(
        MonthlyEmployeeQuery(month=query.pop("month", OCTOBER), **query)
    )
    return [employee.id for employee, _ in result.rows]


def test_add_returns_the_stored_employee_with_its_id_and_timestamps(session: Session) -> None:
    repository = SqlEmployeeRepository(session, ORGANIZATION_ID)

    employee = repository.add(make_employee())

    assert employee.id == 1
    assert employee.created_at is not None
    assert session.scalar(select(func.count()).select_from(Employee)) == 1


def test_add_rejects_a_duplicate_email_and_keeps_the_session_usable(session: Session) -> None:
    repository = SqlEmployeeRepository(session, ORGANIZATION_ID)
    repository.add(make_employee())

    with pytest.raises(DuplicateEmailError):
        repository.add(make_employee())

    assert repository.get(1) is not None


def test_save_rejects_taking_another_employee_email(session: Session) -> None:
    repository = SqlEmployeeRepository(session, ORGANIZATION_ID)
    repository.add(make_employee())
    alan = repository.add(make_employee(email="alan@example.com"))

    alan.email = "ada@example.com"
    with pytest.raises(DuplicateEmailError):
        repository.save(alan)


def test_add_lets_other_constraint_violations_through(session: Session) -> None:
    with pytest.raises(IntegrityError, match="ck_employees_country_iso_alpha2"):
        SqlEmployeeRepository(session, ORGANIZATION_ID).add(make_employee(country="gb"))


def test_save_persists_changes(session: Session) -> None:
    repository = SqlEmployeeRepository(session, ORGANIZATION_ID)
    employee = repository.add(make_employee())

    employee.monthly_salary = Decimal("6100.00")
    repository.save(employee)
    session.expire_all()

    assert session.scalar(select(Employee.monthly_salary)) == Decimal("6100.00")


def test_get_returns_none_for_an_unknown_id(session: Session) -> None:
    assert SqlEmployeeRepository(session, ORGANIZATION_ID).get(404) is None


def test_list_pairs_each_employee_with_only_that_month_payroll(session: Session) -> None:
    paid = add_employee(session, name="paid")
    add_employee(session, name="unpaid")
    session.add_all(
        [
            make_payroll(employee_id=paid.id, month=date(2026, 9, 1)),
            make_payroll(employee_id=paid.id, month=OCTOBER, bonus=Decimal("99.00")),
        ]
    )
    session.commit()

    result = SqlEmployeeRepository(session, ORGANIZATION_ID).list_for_month(
        MonthlyEmployeeQuery(month=OCTOBER)
    )

    names_and_bonuses = [
        (employee.name, payroll and payroll.bonus) for employee, payroll in result.rows
    ]
    assert names_and_bonuses == [("paid", Decimal("99.00")), ("unpaid", None)]
    assert result.total == 2


def test_list_leaves_out_employees_who_joined_after_the_month(session: Session) -> None:
    add_employee(
        session,
        name="joined-on-the-last-moment",
        created_at=datetime(2026, 10, 31, 23, 59, tzinfo=UTC),
    )
    add_employee(session, name="joined-next-month", created_at=datetime(2026, 11, 1, tzinfo=UTC))

    assert ids_for(session) == [1]


def test_list_keeps_people_who_left_only_in_months_they_were_paid_for(session: Session) -> None:
    left = add_employee(session, name="left", is_active=False)
    session.add(make_payroll(employee_id=left.id, month=date(2026, 9, 1)))
    session.commit()

    assert ids_for(session, month=date(2026, 9, 1)) == [left.id]
    assert ids_for(session, month=OCTOBER) == []


@pytest.mark.parametrize(
    ("query", "expected_names"),
    [
        ({"country": "IN"}, ["Ada Byron", "Alan Turing"]),
        ({"job_title": "Accountant"}, ["Ada Byron"]),
        ({"name": "ADA"}, ["Ada Byron", "Ada Lovelace"]),
        ({"name": "love"}, ["Ada Lovelace"]),
        ({"name": "%"}, ["100% Grace"]),
        ({"name": "_"}, []),
        ({"email": "TURING@"}, ["Alan Turing"]),
        ({"country": "IN", "job_title": "Accountant", "name": "byron"}, ["Ada Byron"]),
    ],
    ids=[
        "by-country",
        "by-job-title",
        "name-ignores-case",
        "name-matches-a-substring",
        "percent-sign-is-literal",
        "underscore-is-literal",
        "email-ignores-case-and-matches-a-part",
        "filters-combine",
    ],
)
def test_list_filters(session: Session, query: dict[str, Any], expected_names: list[str]) -> None:
    add_employee(session, name="Ada Lovelace", country="GB")
    add_employee(session, name="Alan Turing", country="IN")
    add_employee(
        session, name="Ada Byron", country="IN", job_title="Accountant", department="Finance"
    )
    add_employee(session, name="100% Grace", country="US")

    result = SqlEmployeeRepository(session, ORGANIZATION_ID).list_for_month(
        MonthlyEmployeeQuery(month=OCTOBER, **query)
    )

    assert [employee.name for employee, _ in result.rows] == expected_names


@pytest.mark.parametrize(
    ("sort_by", "sort_order", "expected"),
    [
        (EmployeeSortField.MONTHLY_SALARY, SortOrder.DESC, [2, 1, 3, 4]),
        (EmployeeSortField.MONTHLY_SALARY, SortOrder.ASC, [3, 4, 1, 2]),
        (EmployeeSortField.NAME, SortOrder.ASC, [4, 3, 2, 1]),
    ],
    ids=["salary-high-to-low", "salary-low-to-high", "name"],
)
def test_list_sorts_and_breaks_ties_by_id(
    session: Session, sort_by: EmployeeSortField, sort_order: SortOrder, expected: list[int]
) -> None:
    add_employee(session, name="dee", monthly_salary=Decimal("5000.00"))
    add_employee(session, name="cat", monthly_salary=Decimal("9000.00"))
    add_employee(session, name="bob", monthly_salary=Decimal("3000.00"))
    add_employee(session, name="amy", monthly_salary=Decimal("3000.00"))

    ids = ids_for(session, country="GB", sort_by=sort_by, sort_order=sort_order)

    assert ids == expected


def test_list_pages_through_all_matches(session: Session) -> None:
    for number in range(1, 6):
        add_employee(session, name=f"employee-{number}")
    repository = SqlEmployeeRepository(session, ORGANIZATION_ID)

    pages = [
        repository.list_for_month(MonthlyEmployeeQuery(month=OCTOBER, page=page, page_size=2))
        for page in (1, 2, 3, 4)
    ]

    assert [[employee.id for employee, _ in page.rows] for page in pages] == [
        [1, 2],
        [3, 4],
        [5],
        [],
    ]
    assert {page.total for page in pages} == {5}
