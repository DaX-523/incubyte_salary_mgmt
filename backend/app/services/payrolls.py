from app.db.models import Payroll
from app.domain.catalog import CURRENCY_BY_COUNTRY
from app.domain.errors import InactiveEmployeeError, PayrollNotFoundError
from app.repositories.employees import EmployeeRepository
from app.repositories.payrolls import PayrollRepository
from app.schemas.payrolls import PayrollCreate, PayrollUpdate
from app.services.employees import get_employee


def get_payroll(repository: PayrollRepository, payroll_id: int) -> Payroll:
    payroll = repository.get(payroll_id)
    if payroll is None:
        raise PayrollNotFoundError(payroll_id)
    return payroll


def create_payroll(
    employees: EmployeeRepository,
    payrolls: PayrollRepository,
    employee_id: int,
    data: PayrollCreate,
) -> Payroll:
    employee = get_employee(employees, employee_id)
    if not employee.is_active:
        raise InactiveEmployeeError(employee_id)
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
