from app.db.models import Payroll
from app.domain.catalog import CURRENCY_BY_COUNTRY
from app.domain.errors import (
    InactiveEmployeeError,
    PayrollBeforeJoiningError,
    PayrollNotFoundError,
)
from app.repositories.employees import EmployeeRepository
from app.repositories.payrolls import PayrollRepository
from app.repositories.population import month_joined
from app.schemas.payrolls import PayrollCreate, PayrollUpdate
from app.services.employees import get_employee


def get_payroll(repository: PayrollRepository, payroll_id: int) -> Payroll:
    payroll = repository.get(payroll_id)
    if payroll is None:
        raise PayrollNotFoundError(payroll_id)
    return payroll


def list_employee_payrolls(
    employees: EmployeeRepository, payrolls: PayrollRepository, employee_id: int
) -> list[Payroll]:
    """The employee's pay history, newest month first."""
    employee = get_employee(employees, employee_id)
    return payrolls.list_for_employee(employee.id)


def create_payroll(
    employees: EmployeeRepository,
    payrolls: PayrollRepository,
    employee_id: int,
    data: PayrollCreate,
) -> Payroll:
    employee = get_employee(employees, employee_id)
    if not employee.is_active:
        raise InactiveEmployeeError(employee_id)
    # Before that month the employee isn't on the books, so the payroll would never be counted.
    joined = month_joined(employee.created_at)
    if data.month < joined:
        raise PayrollBeforeJoiningError(employee_id, joined, data.month)
    payroll = Payroll(
        employee_id=employee.id,
        month=data.month,
        base=data.base,
        bonus=data.bonus,
        esops=data.esops,
        # Paid in the employee's local currency, whatever the client might prefer.
        currency=CURRENCY_BY_COUNTRY[employee.country],
        payment_method=data.payment_method,
    )
    return payrolls.add(payroll)


def update_payroll(
    repository: PayrollRepository, payroll_id: int, changes: PayrollUpdate
) -> Payroll:
    payroll = get_payroll(repository, payroll_id)
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(payroll, field, value)
    return repository.save(payroll)
