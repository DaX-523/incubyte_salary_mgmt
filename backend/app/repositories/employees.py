from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Employee, Payroll
from app.domain.errors import DuplicateEmailError
from app.repositories.errors import violates_unique_constraint
from app.repositories.population import MonthFilter, on_the_books, payroll_for_month
from app.schemas.employees import (
    EmployeeSortField,
    MonthlyEmployeeFilters,
    MonthlyEmployeeQuery,
    SortOrder,
)

SORT_COLUMNS = {
    EmployeeSortField.NAME: Employee.name,
    EmployeeSortField.MONTHLY_SALARY: Employee.monthly_salary,
}


# An employee with their payroll for the month, or None if they haven't been paid for it.
MonthlyEmployeeRow = tuple[Employee, Payroll | None]


@dataclass(frozen=True)
class MonthlyEmployeeRows:
    rows: list[MonthlyEmployeeRow]
    total: int


class EmployeeRepository(Protocol):
    def get(self, employee_id: int) -> Employee | None: ...

    def add(self, employee: Employee) -> Employee: ...

    def save(self, employee: Employee) -> Employee: ...

    def list_for_month(self, query: MonthlyEmployeeQuery) -> MonthlyEmployeeRows: ...

    def list_all_for_month(self, filters: MonthlyEmployeeFilters) -> list[MonthlyEmployeeRow]: ...


class SqlEmployeeRepository:
    """Reads and writes only the employees of one organization."""

    def __init__(self, session: Session, organization_id: int) -> None:
        self._session = session
        self._organization_id = organization_id

    def get(self, employee_id: int) -> Employee | None:
        return self._session.scalar(
            select(Employee).where(
                Employee.id == employee_id, Employee.organization_id == self._organization_id
            )
        )

    def add(self, employee: Employee) -> Employee:
        employee.organization_id = self._organization_id
        self._session.add(employee)
        return self.save(employee)

    def save(self, employee: Employee) -> Employee:
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            if violates_unique_constraint(error, "uq_employees_organization_id_email"):
                raise DuplicateEmailError(employee.email) from error
            raise
        self._session.refresh(employee)
        return employee

    def list_for_month(self, query: MonthlyEmployeeQuery) -> MonthlyEmployeeRows:
        statement = self._filtered(query)
        total = self._session.scalar(select(func.count()).select_from(statement.subquery()))
        page = (
            self._sorted(statement, query)
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        rows: list[MonthlyEmployeeRow] = [
            (employee, payroll) for employee, payroll in self._session.execute(page)
        ]
        return MonthlyEmployeeRows(rows=rows, total=total or 0)

    def list_all_for_month(self, filters: MonthlyEmployeeFilters) -> list[MonthlyEmployeeRow]:
        """Every match, unpaginated, for the CSV export: at most the organization's headcount."""
        statement = self._sorted(self._filtered(filters), filters)
        return [(employee, payroll) for employee, payroll in self._session.execute(statement)]

    def _filtered(self, filters: MonthlyEmployeeFilters) -> Select[Employee, Payroll]:
        # Payroll is outer joined, so it is None for employees not paid for the month.
        month_filter = MonthFilter(filters.month, filters.country, filters.job_title)
        statement = (
            select(Employee, Payroll)
            .outerjoin(Payroll, payroll_for_month(filters.month))
            .where(Employee.organization_id == self._organization_id, *on_the_books(month_filter))
        )
        if filters.name is not None:
            statement = statement.where(Employee.name.icontains(filters.name, autoescape=True))
        if filters.email is not None:
            statement = statement.where(Employee.email.icontains(filters.email, autoescape=True))
        return statement

    @staticmethod
    def _sorted(
        statement: Select[Employee, Payroll], filters: MonthlyEmployeeFilters
    ) -> Select[Employee, Payroll]:
        sort_column = SORT_COLUMNS[filters.sort_by]
        ordered = sort_column.desc() if filters.sort_order is SortOrder.DESC else sort_column.asc()
        # Ties are broken by id, so pages and exports come out in the same order every time.
        return statement.order_by(ordered, Employee.id)
