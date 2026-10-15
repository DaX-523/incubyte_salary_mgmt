from app.db.models import Employee
from app.domain.catalog import DEPARTMENT_BY_JOB_TITLE
from app.domain.errors import EmployeeNotFoundError
from app.repositories.employees import EmployeeRepository, MonthlyEmployeeRows
from app.schemas.employees import EmployeeCreate, EmployeeUpdate, MonthlyEmployeeQuery


def get_employee(repository: EmployeeRepository, employee_id: int) -> Employee:
    employee = repository.get(employee_id)
    if employee is None:
        raise EmployeeNotFoundError(employee_id)
    return employee


def create_employee(repository: EmployeeRepository, data: EmployeeCreate) -> Employee:
    employee = Employee(
        name=data.name,
        email=data.email,
        monthly_salary=data.monthly_salary,
        country=data.country,
        job_title=data.job_title,
        department=DEPARTMENT_BY_JOB_TITLE[data.job_title],
        is_active=True,
    )
    return repository.add(employee)


def update_employee(
    repository: EmployeeRepository, employee_id: int, changes: EmployeeUpdate
) -> Employee:
    employee = get_employee(repository, employee_id)
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)
    if changes.job_title is not None:
        employee.department = DEPARTMENT_BY_JOB_TITLE[changes.job_title]
    return repository.save(employee)


def deactivate_employee(repository: EmployeeRepository, employee_id: int) -> None:
    """Employees are never deleted: their payroll history is a financial record."""
    employee = get_employee(repository, employee_id)
    if employee.is_active:
        employee.is_active = False
        repository.save(employee)


def list_employees_for_month(
    repository: EmployeeRepository, query: MonthlyEmployeeQuery
) -> MonthlyEmployeeRows:
    return repository.list_for_month(query)
