from decimal import Decimal

import pytest

from app.domain.errors import DuplicateEmailError, EmployeeNotFoundError
from app.schemas.employees import EmployeeCreate, EmployeeUpdate
from app.services.employees import (
    create_employee,
    deactivate_employee,
    get_employee,
    update_employee,
)
from tests.fakes import InMemoryEmployeeRepository, make_employee

NEW_EMPLOYEE = EmployeeCreate(
    name="Grace Hopper",
    email="grace@example.com",
    monthly_salary=Decimal("7000.00"),
    country="US",
    job_title="Legal Counsel",
)


def test_create_employee_derives_the_department_from_the_job_title(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    employee = create_employee(employee_repository, NEW_EMPLOYEE)

    assert employee.department == "Legal"


def test_create_employee_stores_an_active_employee(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    employee = create_employee(employee_repository, NEW_EMPLOYEE)

    assert employee_repository.get(employee.id) is employee
    assert employee.is_active is True


def test_create_employee_rejects_a_taken_email(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    employee_repository.add(make_employee(email="grace@example.com"))

    with pytest.raises(DuplicateEmailError, match=r"grace@example\.com"):
        create_employee(employee_repository, NEW_EMPLOYEE)


def test_get_employee_raises_when_the_employee_does_not_exist(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    with pytest.raises(EmployeeNotFoundError, match="Employee 42 not found"):
        get_employee(employee_repository, 42)


def test_update_employee_changes_only_the_fields_sent(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    employee = employee_repository.add(make_employee())

    update_employee(
        employee_repository, employee.id, EmployeeUpdate(monthly_salary=Decimal("5500.00"))
    )

    assert employee.monthly_salary == Decimal("5500.00")
    assert (employee.name, employee.job_title) == ("Ada Lovelace", "Software Engineer")
    assert employee_repository.save_count == 1


def test_update_employee_moves_a_new_job_title_to_its_department(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    employee = employee_repository.add(make_employee())

    update_employee(employee_repository, employee.id, EmployeeUpdate(job_title="Sales Manager"))

    assert (employee.job_title, employee.department) == ("Sales Manager", "Sales")


def test_update_employee_raises_when_the_employee_does_not_exist(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    with pytest.raises(EmployeeNotFoundError):
        update_employee(employee_repository, 42, EmployeeUpdate(name="Ada King"))


def test_deactivate_employee_marks_the_employee_inactive(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    employee = employee_repository.add(make_employee())

    deactivate_employee(employee_repository, employee.id)

    assert employee.is_active is False
    assert employee_repository.get(employee.id) is employee


def test_deactivating_an_inactive_employee_changes_nothing(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    employee = employee_repository.add(make_employee(is_active=False))

    deactivate_employee(employee_repository, employee.id)

    assert employee.is_active is False
    assert employee_repository.save_count == 0


def test_deactivate_employee_raises_when_the_employee_does_not_exist(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    with pytest.raises(EmployeeNotFoundError):
        deactivate_employee(employee_repository, 42)
