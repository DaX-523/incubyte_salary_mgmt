import csv
import io
from datetime import date
from decimal import Decimal

import pytest

from app.repositories.employees import MonthlyEmployeeRow, MonthlyEmployeeRows
from app.schemas.employees import EmployeeSortField, MonthlyEmployeeFilters, SortOrder
from app.services.employee_export import export_employees_for_month
from tests.fakes import InMemoryEmployeeRepository, make_employee, make_payroll

OCTOBER = MonthlyEmployeeFilters(month=date(2026, 10, 1))
HEADER_LINE = (
    "Employee ID,Name,Email,Country,Job title,Department,Currency,Monthly salary,Month,Paid,"
    "Base pay,Bonus,ESOPs,Payment method\r\n"
)


def export(repository: InMemoryEmployeeRepository, *rows: MonthlyEmployeeRow) -> str:
    repository.monthly_rows = MonthlyEmployeeRows(rows=list(rows), total=len(rows))
    return export_employees_for_month(repository, OCTOBER)


def second_line_cells(text: str) -> list[str]:
    return list(csv.reader(io.StringIO(text)))[1]


def test_export_writes_one_line_per_employee_with_that_month_pay(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    paid = make_employee(id=1)
    unpaid = make_employee(
        id=2,
        name="Alan Turing",
        email="alan@example.com",
        country="IN",
        monthly_salary=Decimal("117000"),
    )

    text = export(
        employee_repository,
        (paid, make_payroll(employee_id=1, bonus=Decimal("250.5"))),
        (unpaid, None),
    )

    assert text == (
        HEADER_LINE
        + "1,Ada Lovelace,ada@example.com,GB,Software Engineer,Engineering,GBP,5000.00,2026-10,"
        "Yes,5000.00,250.50,0.00,bank_transfer\r\n"
        "2,Alan Turing,alan@example.com,IN,Software Engineer,Engineering,INR,117000.00,2026-10,"
        "No,,,,\r\n"
    )


def test_export_is_only_the_header_when_nobody_matches(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    assert export(employee_repository) == HEADER_LINE


def test_export_asks_for_every_match_of_the_filters(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    filters = MonthlyEmployeeFilters(
        month=date(2026, 9, 1),
        country="IN",
        sort_by=EmployeeSortField.MONTHLY_SALARY,
        sort_order=SortOrder.DESC,
    )

    export_employees_for_month(employee_repository, filters)

    assert employee_repository.exported_filters == [filters]


@pytest.mark.parametrize(
    ("name", "written"),
    [
        ('=HYPERLINK("http://evil.example","Pay")', '\'=HYPERLINK("http://evil.example","Pay")'),
        ("+44 Sales", "'+44 Sales"),
        ("-Ada", "'-Ada"),
        ("@SUM(A1:A9)", "'@SUM(A1:A9)"),
        ("\tAda", "'\tAda"),
        ("Ada = Lovelace", "Ada = Lovelace"),
    ],
    ids=["equals", "plus", "minus", "at-sign", "tab", "formula-sign-later-in-the-text"],
)
def test_export_stops_spreadsheets_running_a_name_as_a_formula(
    employee_repository: InMemoryEmployeeRepository, name: str, written: str
) -> None:
    text = export(employee_repository, (make_employee(id=1, name=name), None))

    assert second_line_cells(text)[1] == written


def test_export_protects_every_text_column(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    text = export(employee_repository, (make_employee(id=1, email="-ada@example.com"), None))

    assert second_line_cells(text)[2] == "'-ada@example.com"


def test_export_quotes_names_with_commas_and_quotes(
    employee_repository: InMemoryEmployeeRepository,
) -> None:
    text = export(employee_repository, (make_employee(id=1, name='Lovelace, Ada "Countess"'), None))

    assert '"Lovelace, Ada ""Countess"""' in text
    assert second_line_cells(text)[1] == 'Lovelace, Ada "Countess"'
