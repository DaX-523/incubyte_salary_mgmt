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
    average_salary: Decimal  # as the database computes it, not yet rounded to cents


@dataclass(frozen=True)
class CountryPayRow:
    country: str
    headcount: int
    average_salary: Decimal  # as the database computes it, not yet rounded to cents
    total_salary: Decimal


class InsightsRepository(Protocol):
    def count_paid(self, month_filter: MonthFilter) -> PaidCount: ...

    def pay_by_job_title(self, country: str) -> list[JobTitlePayRow]: ...

    def pay_by_country(self) -> list[CountryPayRow]: ...


class SqlInsightsRepository:
    """Aggregates only one organization's employees."""

    def __init__(self, session: Session, organization_id: int) -> None:
        self._session = session
        self._organization_id = organization_id

    def count_paid(self, month_filter: MonthFilter) -> PaidCount:
        statement = (
            select(func.count(Employee.id), func.count(Payroll.id))
            .select_from(Employee)
            .outerjoin(Payroll, payroll_for_month(month_filter.month))
            .where(Employee.organization_id == self._organization_id, *on_the_books(month_filter))
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
                func.avg(Employee.monthly_salary),
            )
            .where(
                Employee.organization_id == self._organization_id,
                Employee.is_active,
                Employee.country == country,
            )
            .group_by(Employee.job_title, Employee.department)
            .order_by(Employee.department, Employee.job_title)
        )
        return [
            JobTitlePayRow(job_title, department, headcount, min_salary, max_salary, average)
            for job_title, department, headcount, min_salary, max_salary, average in (
                self._session.execute(statement)
            )
        ]

    def pay_by_country(self) -> list[CountryPayRow]:
        """One row per country: its salaries share a currency, so they can be averaged and summed.
        Different countries' rows are never added together."""
        statement = (
            select(
                Employee.country,
                func.count(Employee.id),
                func.avg(Employee.monthly_salary),
                func.sum(Employee.monthly_salary),
            )
            .where(Employee.organization_id == self._organization_id, Employee.is_active)
            .group_by(Employee.country)
            .order_by(Employee.country)
        )
        return [
            CountryPayRow(country, headcount, average, total)
            for country, headcount, average, total in self._session.execute(statement)
        ]
