"""Who counts as "on the books" for a month: shared by the monthly list and the paid-vs-total
insight, so the two always agree."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time

from sqlalchemy import ColumnElement, and_, or_

from app.db.models import Employee, Payroll


@dataclass(frozen=True)
class MonthFilter:
    month: date
    country: str | None = None
    job_title: str | None = None


def first_moment_of_next_month(month: date) -> datetime:
    next_month = date(month.year + month.month // 12, month.month % 12 + 1, 1)
    return datetime.combine(next_month, time.min, tzinfo=UTC)


def payroll_for_month(month: date) -> ColumnElement[bool]:
    """Join condition: the employee's payroll for `month`, if any."""
    return and_(Payroll.employee_id == Employee.id, Payroll.month == month)


def on_the_books(month_filter: MonthFilter) -> list[ColumnElement[bool]]:
    """Employees who had joined by the end of the month and are still active or were paid for it.

    Someone who has since left still appears in the months they were paid for.
    """
    conditions = [
        Employee.created_at < first_moment_of_next_month(month_filter.month),
        or_(Employee.is_active, Payroll.id.is_not(None)),
    ]
    if month_filter.country is not None:
        conditions.append(Employee.country == month_filter.country)
    if month_filter.job_title is not None:
        conditions.append(Employee.job_title == month_filter.job_title)
    return conditions
