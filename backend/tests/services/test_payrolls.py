from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.db.models import PaymentMethod
from app.domain.errors import (
    DuplicatePayrollError,
    EmployeeNotFoundError,
    InactiveEmployeeError,
    PayrollBeforeJoiningError,
    PayrollNotFoundError,
)
from app.schemas.payrolls import PayrollCreate, PayrollUpdate
from app.services.payrolls import (
    create_payroll,
    get_payroll,
    list_employee_payrolls,
    update_payroll,
)
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
UTC_MINUS_4 = timezone(timedelta(hours=-4))


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


@pytest.mark.parametrize(
    ("joined_at", "month"),
    [
        (datetime(2026, 10, 16, 9, 0, tzinfo=UTC), date(2026, 10, 1)),
        (datetime(2026, 10, 31, 23, 59, tzinfo=UTC), date(2026, 10, 1)),
        (datetime(2026, 10, 16, 9, 0, tzinfo=UTC), date(2026, 11, 1)),
    ],
    ids=["the-joining-month", "joined-in-the-last-minute-of-the-month", "a-later-month"],
)
def test_create_payroll_accepts_months_from_the_one_the_employee_joined(
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
    joined_at: datetime,
    month: date,
) -> None:
    employee = employee_repository.add(make_employee(created_at=joined_at))

    payroll = create_payroll(
        employee_repository,
        payroll_repository,
        employee.id,
        OCTOBER_PAY.model_copy(update={"month": month}),
    )

    assert payroll.month == month


@pytest.mark.parametrize(
    ("joined_at", "month", "message"),
    [
        (
            datetime(2026, 10, 1, 0, 0, tzinfo=UTC),
            date(2026, 9, 1),
            "Employee 1 joined in 2026-10, so they cannot be paid for 2026-09",
        ),
        (
            datetime(2026, 10, 16, 9, 0, tzinfo=UTC),
            date(2025, 10, 1),
            "Employee 1 joined in 2026-10, so they cannot be paid for 2025-10",
        ),
        # 8 pm on 31 October at UTC-4 is midnight on 1 November in UTC, where months are counted.
        (
            datetime(2026, 10, 31, 20, 0, tzinfo=UTC_MINUS_4),
            date(2026, 10, 1),
            "Employee 1 joined in 2026-11, so they cannot be paid for 2026-10",
        ),
    ],
    ids=["the-month-before", "a-year-before", "joined-in-november-in-utc"],
)
def test_create_payroll_rejects_months_before_the_employee_joined(
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
    joined_at: datetime,
    month: date,
    message: str,
) -> None:
    employee = employee_repository.add(make_employee(created_at=joined_at))

    with pytest.raises(PayrollBeforeJoiningError, match=message):
        create_payroll(
            employee_repository,
            payroll_repository,
            employee.id,
            OCTOBER_PAY.model_copy(update={"month": month}),
        )

    assert payroll_repository.payrolls == {}


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


def test_list_employee_payrolls_returns_only_theirs_newest_month_first(
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    ada = employee_repository.add(make_employee())
    alan = employee_repository.add(make_employee(email="alan@example.com"))
    payroll_repository.add(make_payroll(employee_id=ada.id, month=date(2026, 8, 1)))
    payroll_repository.add(make_payroll(employee_id=ada.id, month=date(2026, 10, 1)))
    payroll_repository.add(make_payroll(employee_id=alan.id, month=date(2026, 9, 1)))
    payroll_repository.add(make_payroll(employee_id=ada.id, month=date(2026, 9, 1)))

    payrolls = list_employee_payrolls(employee_repository, payroll_repository, ada.id)

    assert [payroll.month for payroll in payrolls] == [
        date(2026, 10, 1),
        date(2026, 9, 1),
        date(2026, 8, 1),
    ]
    assert {payroll.employee_id for payroll in payrolls} == {ada.id}


def test_list_employee_payrolls_is_empty_for_someone_never_paid(
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    employee = employee_repository.add(make_employee())

    assert list_employee_payrolls(employee_repository, payroll_repository, employee.id) == []


def test_list_employee_payrolls_raises_when_the_employee_does_not_exist(
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    with pytest.raises(EmployeeNotFoundError, match="Employee 42 not found"):
        list_employee_payrolls(employee_repository, payroll_repository, 42)
