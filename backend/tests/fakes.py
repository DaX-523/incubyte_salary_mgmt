"""In-memory stand-ins for the repositories, for service and API tests that need no database.

They mimic the database's uniqueness rules; the real queries are covered by tests/integration.
"""

from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Any

from app.db.models import Employee, PaymentMethod, Payroll
from app.domain.errors import DuplicateEmailError, DuplicatePayrollError
from app.repositories.employees import MonthlyEmployeeRows
from app.repositories.insights import JobTitlePayRow, PaidCount
from app.repositories.population import MonthFilter
from app.schemas.employees import MonthlyEmployeeQuery


def make_employee(**overrides: Any) -> Employee:
    fields: dict[str, Any] = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "monthly_salary": Decimal("5000.00"),
        "country": "GB",
        "department": "Engineering",
        "job_title": "Software Engineer",
        "is_active": True,
    }
    return Employee(**(fields | overrides))


def make_payroll(**overrides: Any) -> Payroll:
    fields: dict[str, Any] = {
        "employee_id": 1,
        "month": date(2026, 10, 1),
        "base": Decimal("5000.00"),
        "bonus": Decimal("0.00"),
        "esops": Decimal("0.00"),
        "currency": "GBP",
        "payment_method": PaymentMethod.BANK_TRANSFER,
    }
    return Payroll(**(fields | overrides))


class InMemoryEmployeeRepository:
    def __init__(self) -> None:
        self.employees: dict[int, Employee] = {}
        self.save_count = 0
        self.monthly_rows = MonthlyEmployeeRows(rows=[], total=0)
        self.monthly_queries: list[MonthlyEmployeeQuery] = []

    def get(self, employee_id: int) -> Employee | None:
        return self.employees.get(employee_id)

    def add(self, employee: Employee) -> Employee:
        self._ensure_unique_email(employee)
        employee.id = max(self.employees, default=0) + 1
        self.employees[employee.id] = employee
        return employee

    def save(self, employee: Employee) -> Employee:
        self._ensure_unique_email(employee)
        self.save_count += 1
        return employee

    def list_for_month(self, query: MonthlyEmployeeQuery) -> MonthlyEmployeeRows:
        self.monthly_queries.append(query)
        return self.monthly_rows

    def _ensure_unique_email(self, employee: Employee) -> None:
        if any(
            other.email == employee.email and other is not employee
            for other in self.employees.values()
        ):
            raise DuplicateEmailError(employee.email)


class InMemoryPayrollRepository:
    def __init__(self) -> None:
        self.payrolls: dict[int, Payroll] = {}
        self.save_count = 0

    def get(self, payroll_id: int) -> Payroll | None:
        return self.payrolls.get(payroll_id)

    def add(self, payroll: Payroll) -> Payroll:
        if any(
            (other.employee_id, other.month) == (payroll.employee_id, payroll.month)
            for other in self.payrolls.values()
        ):
            raise DuplicatePayrollError(payroll.employee_id, payroll.month)
        payroll.id = max(self.payrolls, default=0) + 1
        self.payrolls[payroll.id] = payroll
        return payroll

    def save(self, payroll: Payroll) -> Payroll:
        self.save_count += 1
        return payroll


class StubInsightsRepository:
    def __init__(self) -> None:
        self.paid_count = PaidCount(total=0, paid=0)
        self.job_title_rows: list[JobTitlePayRow] = []
        self.month_filters: list[MonthFilter] = []
        self.countries: list[str] = []

    def count_paid(self, month_filter: MonthFilter) -> PaidCount:
        self.month_filters.append(month_filter)
        return self.paid_count

    def pay_by_job_title(self, country: str) -> list[JobTitlePayRow]:
        self.countries.append(country)
        return [replace(row) for row in self.job_title_rows]
