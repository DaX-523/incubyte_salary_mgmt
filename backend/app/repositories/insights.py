from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Employee, Payroll
from app.repositories.population import MonthFilter, on_the_books, payroll_for_month


@dataclass(frozen=True)
class PaidCount:
    total: int
    paid: int


@dataclass(frozen=True)
class JobTitlePayRow:
    job_title: str
    department: str
    headcount: int
    min_salary: Decimal
    max_salary: Decimal


class InsightsRepository(Protocol):
    def count_paid(self, month_filter: MonthFilter) -> PaidCount: ...

    def pay_by_job_title(self, country: str) -> list[JobTitlePayRow]: ...


class SqlInsightsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def count_paid(self, month_filter: MonthFilter) -> PaidCount:
        statement = (
            select(func.count(Employee.id), func.count(Payroll.id))
            .select_from(Employee)
            .outerjoin(Payroll, payroll_for_month(month_filter.month))
            .where(*on_the_books(month_filter))
        )
        total, paid = self._session.execute(statement).one()
        return PaidCount(total=total, paid=paid)

    def pay_by_job_title(self, country: str) -> list[JobTitlePayRow]:
        statement = (
            select(
                Employee.job_title,
                Employee.department,
                func.count(Employee.id),
                func.min(Employee.monthly_salary),
                func.max(Employee.monthly_salary),
            )
            .where(Employee.is_active, Employee.country == country)
            .group_by(Employee.job_title, Employee.department)
            .order_by(Employee.department, Employee.job_title)
        )
        return [
            JobTitlePayRow(job_title, department, headcount, min_salary, max_salary)
            for job_title, department, headcount, min_salary, max_salary in self._session.execute(
                statement
            )
        ]
