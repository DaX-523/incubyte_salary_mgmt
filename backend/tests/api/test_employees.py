from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.repositories.employees import MonthlyEmployeeRows
from app.schemas.employees import EmployeeSortField, SortOrder
from tests.fakes import (
    InMemoryEmployeeRepository,
    InMemoryPayrollRepository,
    make_employee,
    make_payroll,
)

NEW_EMPLOYEE = {
    "name": "Grace Hopper",
    "email": "grace@example.com",
    "monthly_salary": "7000.00",
    "country": "US",
    "job_title": "Engineering Manager",
}
NEW_PAYROLL = {"month": "2026-10", "base": "5000.00", "payment_method": "bank_transfer"}
GRACE = {
    "id": 1,
    "name": "Grace Hopper",
    "email": "grace@example.com",
    "monthly_salary": "7000.00",
    "currency": "USD",
    "country": "US",
    "department": "Engineering",
    "job_title": "Engineering Manager",
    "is_active": True,
}


def employee_json(**overrides: Any) -> dict[str, Any]:
    return {**NEW_EMPLOYEE, **overrides}


# --- GET /employees (the monthly view) ---


def test_list_returns_each_employee_with_that_month_payroll(
    api_client: TestClient, employee_repository: InMemoryEmployeeRepository
) -> None:
    paid = make_employee(id=1)
    unpaid = make_employee(id=2, name="Alan Turing", email="alan@example.com", country="IN")
    employee_repository.monthly_rows = MonthlyEmployeeRows(
        rows=[(paid, make_payroll(id=9, employee_id=1, bonus=Decimal("250.50"))), (unpaid, None)],
        total=30,
    )

    response = api_client.get("/api/v1/employees", params={"month": "2026-10", "page_size": 2})

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert (body["total"], body["page"], body["page_size"]) == (30, 1, 2)
    assert body["items"][0]["payroll"] == {
        "id": 9,
        "employee_id": 1,
        "month": "2026-10",
        "base": "5000.00",
        "bonus": "250.50",
        "esops": "0.00",
        "currency": "GBP",
        "payment_method": "bank_transfer",
    }
    assert body["items"][1]["payroll"] is None
    assert body["items"][1]["employee"]["currency"] == "INR"


def test_list_sends_the_parsed_filters_to_the_repository(
    api_client: TestClient, employee_repository: InMemoryEmployeeRepository
) -> None:
    api_client.get(
        "/api/v1/employees",
        params={
            "month": "2026-09",
            "name": "  ada ",
            "email": " Ada@Example ",
            "country": "DE",
            "job_title": "Accountant",
            "sort_by": "monthly_salary",
            "sort_order": "desc",
            "page": 3,
        },
    )

    [query] = employee_repository.monthly_queries
    assert query.month == date(2026, 9, 1)
    assert (query.name, query.email) == ("ada", "Ada@Example")
    assert (query.country, query.job_title) == ("DE", "Accountant")
    assert (query.sort_by, query.sort_order) == (EmployeeSortField.MONTHLY_SALARY, SortOrder.DESC)
    assert (query.page, query.page_size) == (3, 25)


def test_list_defaults_to_the_first_page_sorted_by_name(
    api_client: TestClient, employee_repository: InMemoryEmployeeRepository
) -> None:
    api_client.get("/api/v1/employees", params={"month": "2026-10"})

    [query] = employee_repository.monthly_queries
    assert (query.sort_by, query.sort_order) == (EmployeeSortField.NAME, SortOrder.ASC)
    assert (query.page, query.page_size) == (1, 25)


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({}, "Field required"),
        ({"month": "2026-13"}, "YYYY-MM"),
        ({"month": "10-2026"}, "YYYY-MM"),
        ({"month": "2026-10", "country": "XX"}, "unknown country"),
        ({"month": "2026-10", "country": "de"}, "unknown country"),
        ({"month": "2026-10", "job_title": "Wizard"}, "unknown job title"),
        ({"month": "2026-10", "name": "   "}, "at least 1 character"),
        ({"month": "2026-10", "email": "   "}, "at least 1 character"),
        ({"month": "2026-10", "email": "x" * 321}, "at most 320 characters"),
        ({"month": "2026-10", "page": 0}, "greater than or equal to 1"),
        ({"month": "2026-10", "page_size": 0}, "greater than or equal to 1"),
        ({"month": "2026-10", "page_size": 101}, "less than or equal to 100"),
        ({"month": "2026-10", "sort_by": "id"}, "Input should be"),
        ({"month": "2026-10", "sort_by": "monthly_salary"}, "needs a country filter"),
    ],
    ids=[
        "missing-month",
        "month-13",
        "month-before-year",
        "unknown-country",
        "lowercase-country",
        "unknown-job-title",
        "blank-name",
        "blank-email",
        "email-too-long",
        "page-zero",
        "page-size-zero",
        "page-size-over-limit",
        "id-sort-is-gone",
        "salary-sort-across-countries",
    ],
)
def test_list_rejects_invalid_filters(
    api_client: TestClient, params: dict[str, Any], message: str
) -> None:
    response = api_client.get("/api/v1/employees", params=params)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert message in response.text


def test_list_sorts_by_salary_within_a_country(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/v1/employees",
        params={"month": "2026-10", "country": "GB", "sort_by": "monthly_salary"},
    )

    assert response.status_code == status.HTTP_200_OK


# --- POST /employees ---


def test_create_returns_the_employee_with_department_and_currency(api_client: TestClient) -> None:
    response = api_client.post("/api/v1/employees", json=NEW_EMPLOYEE)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == GRACE


def test_create_normalizes_name_and_email(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/employees", json=employee_json(name="  Grace Hopper ", email="Grace@Example.COM")
    )

    assert (response.json()["name"], response.json()["email"]) == (
        "Grace Hopper",
        "grace@example.com",
    )


@pytest.mark.parametrize(
    ("salary", "stored"),
    [("7000", "7000.00"), ("0", "0.00"), ("999999999999.99", "999999999999.99")],
    ids=["whole-number", "zero", "largest-storable"],
)
def test_create_accepts_salaries_at_the_boundaries(
    api_client: TestClient, salary: str, stored: str
) -> None:
    response = api_client.post("/api/v1/employees", json=employee_json(monthly_salary=salary))

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["monthly_salary"] == stored


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"name": ""}, "at least 1 character"),
        ({"name": "x" * 201}, "at most 200 characters"),
        ({"email": "not-an-email"}, "valid email address"),
        ({"monthly_salary": "-0.01"}, "greater than or equal to 0"),
        ({"monthly_salary": "7000.001"}, "decimal places"),
        ({"monthly_salary": "1000000000000.00"}, "no more than 12 digits before the decimal"),
        ({"monthly_salary": "seven"}, "valid decimal"),
        ({"country": "ZZ"}, "unknown country"),
        ({"job_title": "software engineer"}, "unknown job title"),
        ({"department": "Legal"}, "Extra inputs are not permitted"),
        ({"is_active": False}, "Extra inputs are not permitted"),
    ],
    ids=[
        "empty-name",
        "name-too-long",
        "invalid-email",
        "negative-salary",
        "sub-cent-salary",
        "salary-too-large",
        "salary-not-a-number",
        "unknown-country",
        "job-title-wrong-case",
        "department-is-derived",
        "is-active-is-not-settable",
    ],
)
def test_create_rejects_invalid_employees(
    api_client: TestClient, overrides: dict[str, Any], message: str
) -> None:
    response = api_client.post("/api/v1/employees", json=employee_json(**overrides))

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert message in response.text


@pytest.mark.parametrize("field", ["name", "email", "monthly_salary", "country", "job_title"])
def test_create_requires_every_field(api_client: TestClient, field: str) -> None:
    body = {key: value for key, value in NEW_EMPLOYEE.items() if key != field}

    response = api_client.post("/api/v1/employees", json=body)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_rejects_an_email_taken_in_another_letter_case(
    api_client: TestClient, employee_repository: InMemoryEmployeeRepository
) -> None:
    employee_repository.add(make_employee(email="grace@example.com"))

    response = api_client.post("/api/v1/employees", json=employee_json(email="GRACE@example.com"))

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "An employee with email grace@example.com already exists"}


# --- GET /employees/{id} ---


def test_get_returns_the_employee(
    api_client: TestClient, employee_repository: InMemoryEmployeeRepository
) -> None:
    employee_repository.add(make_employee())

    response = api_client.get("/api/v1/employees/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == "ada@example.com"


def test_get_reports_a_missing_employee(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/employees/42")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Employee 42 not found"}


@pytest.mark.parametrize("employee_id", ["0", "-1", str(2**63), "abc"])
def test_get_rejects_ids_that_cannot_exist(api_client: TestClient, employee_id: str) -> None:
    response = api_client.get(f"/api/v1/employees/{employee_id}")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# --- PATCH /employees/{id} ---


def test_update_changes_the_sent_fields(
    api_client: TestClient, employee_repository: InMemoryEmployeeRepository
) -> None:
    employee_repository.add(make_employee())

    response = api_client.patch(
        "/api/v1/employees/1", json={"monthly_salary": "5500.00", "job_title": "Accountant"}
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert (body["monthly_salary"], body["job_title"]) == ("5500.00", "Accountant")
    assert (body["department"], body["name"]) == ("Finance", "Ada Lovelace")


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({}, "send at least one field"),
        ({"name": None}, "fields cannot be null: name"),
        ({"country": "IN"}, "Extra inputs are not permitted"),
        ({"is_active": True}, "Extra inputs are not permitted"),
        ({"monthly_salary": "-1"}, "greater than or equal to 0"),
    ],
    ids=["empty", "null-name", "country-is-fixed", "is-active-is-not-settable", "negative-salary"],
)
def test_update_rejects_invalid_changes(
    api_client: TestClient,
    employee_repository: InMemoryEmployeeRepository,
    body: dict[str, Any],
    message: str,
) -> None:
    employee_repository.add(make_employee())

    response = api_client.patch("/api/v1/employees/1", json=body)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert message in response.text


def test_update_rejects_an_email_taken_by_someone_else(
    api_client: TestClient, employee_repository: InMemoryEmployeeRepository
) -> None:
    employee_repository.add(make_employee())
    employee_repository.add(make_employee(email="alan@example.com"))

    response = api_client.patch("/api/v1/employees/1", json={"email": "alan@example.com"})

    assert response.status_code == status.HTTP_409_CONFLICT


def test_update_reports_a_missing_employee(api_client: TestClient) -> None:
    response = api_client.patch("/api/v1/employees/42", json={"name": "Ada King"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- DELETE /employees/{id} ---


def test_delete_deactivates_and_keeps_the_employee(
    api_client: TestClient, employee_repository: InMemoryEmployeeRepository
) -> None:
    employee_repository.add(make_employee())

    response = api_client.delete("/api/v1/employees/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""
    assert api_client.get("/api/v1/employees/1").json()["is_active"] is False


def test_delete_reports_a_missing_employee(api_client: TestClient) -> None:
    response = api_client.delete("/api/v1/employees/42")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- POST /employees/{id}/payrolls ---


def test_create_payroll_pays_in_the_employee_currency(
    api_client: TestClient, employee_repository: InMemoryEmployeeRepository
) -> None:
    employee_repository.add(make_employee(country="FR"))

    response = api_client.post("/api/v1/employees/1/payrolls", json=NEW_PAYROLL)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "id": 1,
        "employee_id": 1,
        "month": "2026-10",
        "base": "5000.00",
        "bonus": "0.00",
        "esops": "0.00",
        "currency": "EUR",
        "payment_method": "bank_transfer",
    }


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"month": "2026-10-01"}, "YYYY-MM"),
        ({"base": "-5"}, "greater than or equal to 0"),
        ({"bonus": "1.234"}, "decimal places"),
        ({"payment_method": "cash"}, "'bank_transfer' or 'digital_wallet'"),
        ({"currency": "USD"}, "Extra inputs are not permitted"),
    ],
    ids=["full-date", "negative-base", "sub-cent-bonus", "retired-method", "currency-is-derived"],
)
def test_create_payroll_rejects_invalid_payrolls(
    api_client: TestClient,
    employee_repository: InMemoryEmployeeRepository,
    overrides: dict[str, Any],
    message: str,
) -> None:
    employee_repository.add(make_employee())

    response = api_client.post("/api/v1/employees/1/payrolls", json={**NEW_PAYROLL, **overrides})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert message in response.text


def test_create_payroll_reports_a_missing_employee(api_client: TestClient) -> None:
    response = api_client.post("/api/v1/employees/42/payrolls", json=NEW_PAYROLL)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_payroll_rejects_an_inactive_employee(
    api_client: TestClient, employee_repository: InMemoryEmployeeRepository
) -> None:
    employee_repository.add(make_employee(is_active=False))

    response = api_client.post("/api/v1/employees/1/payrolls", json=NEW_PAYROLL)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "Employee 1 is inactive, so no new payrolls can be added"}


def test_create_payroll_rejects_a_second_payroll_for_the_month(
    api_client: TestClient,
    employee_repository: InMemoryEmployeeRepository,
    payroll_repository: InMemoryPayrollRepository,
) -> None:
    employee_repository.add(make_employee())
    payroll_repository.add(make_payroll(employee_id=1, month=date(2026, 10, 1)))

    response = api_client.post("/api/v1/employees/1/payrolls", json=NEW_PAYROLL)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "Employee 1 already has a payroll for 2026-10"}
