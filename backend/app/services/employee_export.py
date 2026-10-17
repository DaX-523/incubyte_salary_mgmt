"""The monthly employee list as a CSV file, which HR opens in a spreadsheet such as Excel."""

import csv
import io
from datetime import date
from decimal import Decimal

from app.db.models import Employee, Payroll
from app.domain.catalog import CURRENCY_BY_COUNTRY
from app.repositories.employees import EmployeeRepository, MonthlyEmployeeRow
from app.schemas.common import format_month, to_cents
from app.schemas.employees import MonthlyEmployeeFilters

CSV_HEADER = (
    "Employee ID",
    "Name",
    "Email",
    "Country",
    "Job title",
    "Department",
    "Currency",
    "Monthly salary",
    "Month",
    "Paid",
    "Base pay",
    "Bonus",
    "ESOPs",
    "Payment method",
)
# A spreadsheet runs a cell starting with one of these as a formula ("CSV injection", OWASP), so an
# employee named "=HYPERLINK(...)" would become a live link.
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
UNPAID = ("", "", "", "")


def export_employees_for_month(
    repository: EmployeeRepository, filters: MonthlyEmployeeFilters
) -> str:
    """Every employee the monthly list shows for `filters`, in the same order, as CSV text."""
    return employees_csv(filters.month, repository.list_all_for_month(filters))


def employees_csv(month: date, rows: list[MonthlyEmployeeRow]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADER)
    for employee, payroll in rows:
        writer.writerow(spreadsheet_safe(cell) for cell in _cells(month, employee, payroll))
    return buffer.getvalue()


def spreadsheet_safe(value: str) -> str:
    """A leading apostrophe makes a spreadsheet show a would-be formula as plain text."""
    return f"'{value}" if value.startswith(FORMULA_PREFIXES) else value


def _cells(month: date, employee: Employee, payroll: Payroll | None) -> tuple[str, ...]:
    pay = (
        (
            _amount(payroll.base),
            _amount(payroll.bonus),
            _amount(payroll.esops),
            payroll.payment_method.value,
        )
        if payroll
        else UNPAID
    )
    return (
        str(employee.id),
        employee.name,
        employee.email,
        employee.country,
        employee.job_title,
        employee.department,
        CURRENCY_BY_COUNTRY[employee.country],
        _amount(employee.monthly_salary),
        format_month(month),
        "Yes" if payroll else "No",
        *pay,
    )


def _amount(value: Decimal) -> str:
    """A plain number with two decimals ("4780.00"), so spreadsheets can add it up."""
    return format(to_cents(value), "f")
