from datetime import date
from decimal import Decimal

import pytest

from app.db.models import PaymentMethod
from app.domain.errors import (
    DuplicatePayrollError,
    EmployeeNotFoundError,
    InactiveEmployeeError,
    PayrollNotFoundError,
)
from app.schemas.payrolls import PayrollCreate, PayrollUpdate
from app.services.payrolls import create_payroll, get_payroll, update_payroll
from tests.fakes import (
    InMemoryEmployeeRepository,
    InMemoryPayrollRepository,
    make_employee,
    make_payroll,
)

OCTOBER_PAY = PayrollCreate(
    month=date(2026, 10, 1),
    base=Decimal("90000.00"),
    payment_method=PaymentMethod.DIGITAL_WALLET,
)


def test_create_payroll_pays_in_the_employee_country_currency(
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    employee = employee_repository.add(make_employee(country="IN"))

    payroll = create_payroll(employee_repository, payroll_repository, employee.id, OCTOBER_PAY)

    assert payroll.currency == "INR"
    assert payroll.employee_id == employee.id
    assert payroll_repository.get(payroll.id) is payroll


def test_create_payroll_defaults_bonus_and_esops_to_zero(
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    employee = employee_repository.add(make_employee())

    payroll = create_payroll(employee_repository, payroll_repository, employee.id, OCTOBER_PAY)

    assert (payroll.bonus, payroll.esops) == (Decimal("0.00"), Decimal("0.00"))


def test_create_payroll_raises_when_the_employee_does_not_exist(
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    with pytest.raises(EmployeeNotFoundError):
        create_payroll(employee_repository, payroll_repository, 42, OCTOBER_PAY)


def test_create_payroll_rejects_an_inactive_employee(
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    employee = employee_repository.add(make_employee(is_active=False))

    with pytest.raises(InactiveEmployeeError, match="inactive"):
        create_payroll(employee_repository, payroll_repository, employee.id, OCTOBER_PAY)

    assert payroll_repository.payrolls == {}


def test_create_payroll_rejects_a_second_payroll_for_the_same_month(
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    employee = employee_repository.add(make_employee())
    create_payroll(employee_repository, payroll_repository, employee.id, OCTOBER_PAY)

    with pytest.raises(DuplicatePayrollError, match="already has a payroll for 2026-10"):
        create_payroll(employee_repository, payroll_repository, employee.id, OCTOBER_PAY)


def test_get_payroll_raises_when_the_payroll_does_not_exist(
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    with pytest.raises(PayrollNotFoundError, match="Payroll 7 not found"):
        get_payroll(payroll_repository, 7)


def test_update_payroll_changes_only_the_fields_sent(
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    payroll = payroll_repository.add(make_payroll())

    update_payroll(payroll_repository, payroll.id, PayrollUpdate(bonus=Decimal("250.00")))

    assert (payroll.base, payroll.bonus) == (Decimal("5000.00"), Decimal("250.00"))
    assert payroll_repository.save_count == 1


def test_update_payroll_raises_when_the_payroll_does_not_exist(
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    with pytest.raises(PayrollNotFoundError):
        update_payroll(payroll_repository, 7, PayrollUpdate(bonus=Decimal("1.00")))
