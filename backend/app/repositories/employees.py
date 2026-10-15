from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Employee, Payroll
from app.domain.errors import DuplicateEmailError
from app.repositories.errors import violates_unique_constraint
from app.repositories.population import MonthFilter, on_the_books, payroll_for_month
from app.schemas.employees import EmployeeSortField, MonthlyEmployeeQuery, SortOrder

SORT_COLUMNS = {
    EmployeeSortField.ID: Employee.id,
    EmployeeSortField.NAME: Employee.name,
    EmployeeSortField.MONTHLY_SALARY: Employee.monthly_salary,
}


@dataclass(frozen=True)
class MonthlyEmployeeRows:
    rows: list[tuple[Employee, Payroll | None]]
    total: int


class EmployeeRepository(Protocol):
    def get(self, employee_id: int) -> Employee | None: ...

    def add(self, employee: Employee) -> Employee: ...

    def save(self, employee: Employee) -> Employee: ...

    def list_for_month(self, query: MonthlyEmployeeQuery) -> MonthlyEmployeeRows: ...


class SqlEmployeeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, employee_id: int) -> Employee | None:
        return self._session.get(Employee, employee_id)

    def add(self, employee: Employee) -> Employee:
        self._session.add(employee)
        return self.save(employee)

    def save(self, employee: Employee) -> Employee:
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            if violates_unique_constraint(error, "uq_employees_email"):
                raise DuplicateEmailError(employee.email) from error
            raise
        self._session.refresh(employee)
        return employee

    def list_for_month(self, query: MonthlyEmployeeQuery) -> MonthlyEmployeeRows:
        statement = self._filtered(query)
        total = self._session.scalar(select(func.count()).select_from(statement.subquery()))
        sort_column = SORT_COLUMNS[query.sort_by]
        ordered = sort_column.desc() if query.sort_order is SortOrder.DESC else sort_column.asc()
        page = (
            statement.order_by(ordered, Employee.id)
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        rows: list[tuple[Employee, Payroll | None]] = [
            (employee, payroll) for employee, payroll in self._session.execute(page)
        ]
        return MonthlyEmployeeRows(rows=rows, total=total or 0)

    @staticmethod
    def _filtered(query: MonthlyEmployeeQuery) -> Select[Employee, Payroll]:
        # Payroll is outer joined, so it is None for employees not paid for the month.
        month_filter = MonthFilter(query.month, query.country, query.job_title)
        statement = (
            select(Employee, Payroll)
            .outerjoin(Payroll, payroll_for_month(query.month))
            .where(*on_the_books(month_filter))
        )
        if query.id is not None:
            statement = statement.where(Employee.id == query.id)
        if query.name is not None:
            statement = statement.where(Employee.name.icontains(query.name, autoescape=True))
        return statement
