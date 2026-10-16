"""Each organization's HR only ever sees and changes that organization's employees."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

NEW_EMPLOYEE = {
    "name": "Grace Hopper",
    "email": "grace@example.com",
    "monthly_salary": "7000",
    "country": "US",
    "job_title": "Engineering Manager",
}
NEW_PAYROLL = {"month": "2026-10", "base": "7000", "payment_method": "bank_transfer"}
LogIn = Callable[..., dict[str, str]]
# Far enough ahead that everyone created during the test is on the books.
LATER_MONTH = "2099-12"


@pytest.fixture
def other_organization(engine: Engine, log_in: LogIn) -> dict[str, str]:
    """Headers for an HR user of a second organization."""
    with engine.begin() as connection:
        organization_id = connection.scalar(
            text("INSERT INTO organizations (name) VALUES ('Globex') RETURNING id")
        )
    return log_in(organization_id, "hr@globex.example")


@pytest.fixture
def records(db_client: TestClient) -> dict[str, int]:
    """An employee and a payroll of the test organization."""
    employee = db_client.post("/api/v1/employees", json=NEW_EMPLOYEE).json()
    payroll = db_client.post(f"/api/v1/employees/{employee['id']}/payrolls", json=NEW_PAYROLL)
    return {"employee": employee["id"], "payroll": payroll.json()["id"]}


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/api/v1/employees/{employee}", None),
        ("PATCH", "/api/v1/employees/{employee}", {"name": "Taken Over"}),
        ("DELETE", "/api/v1/employees/{employee}", None),
        ("POST", "/api/v1/employees/{employee}/payrolls", {**NEW_PAYROLL, "month": "2026-11"}),
        ("GET", "/api/v1/payrolls/{payroll}", None),
        ("PATCH", "/api/v1/payrolls/{payroll}", {"bonus": "1000"}),
    ],
    ids=[
        "read-employee",
        "edit-employee",
        "deactivate-employee",
        "pay-employee",
        "read-payroll",
        "edit-payroll",
    ],
)
def test_another_organization_cannot_reach_its_records(
    db_client: TestClient,
    records: dict[str, int],
    other_organization: dict[str, str],
    method: str,
    path: str,
    body: dict[str, Any] | None,
) -> None:
    response = db_client.request(
        method, path.format(**records), json=body, headers=other_organization
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_another_organization_sees_none_of_its_employees(
    db_client: TestClient, records: dict[str, int], other_organization: dict[str, str]
) -> None:
    own_listing = db_client.get("/api/v1/employees", params={"month": LATER_MONTH})

    listing = db_client.get(
        "/api/v1/employees", params={"month": LATER_MONTH}, headers=other_organization
    )
    paid = db_client.get(
        "/api/v1/insights/payroll-status",
        params={"month": LATER_MONTH},
        headers=other_organization,
    )
    pay_ranges = db_client.get(
        "/api/v1/insights/pay-by-job-title", params={"country": "US"}, headers=other_organization
    )

    assert own_listing.json()["total"] == 1
    assert listing.json()["total"] == 0
    assert (paid.json()["total"], paid.json()["paid"]) == (0, 0)
    assert pay_ranges.json()["job_titles"] == []


def test_two_organizations_can_employ_the_same_email(
    db_client: TestClient, records: dict[str, int], other_organization: dict[str, str]
) -> None:
    response = db_client.post("/api/v1/employees", json=NEW_EMPLOYEE, headers=other_organization)

    assert response.status_code == status.HTTP_201_CREATED
