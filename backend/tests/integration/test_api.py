"""End-to-end through HTTP, the real repositories and Postgres: proves the wiring, not the rules."""

from fastapi import status
from fastapi.testclient import TestClient

NEW_EMPLOYEE = {
    "name": "Grace Hopper",
    "email": "grace@example.com",
    "monthly_salary": "7000",
    "country": "US",
    "job_title": "Engineering Manager",
}
# Employees join in the month they are added, so pay them for a month far enough ahead that it
# comes after "now" whenever the test runs.
MONTH = "2099-12"


def test_an_employee_can_be_hired_paid_and_deactivated(db_client: TestClient) -> None:
    employee = db_client.post("/api/v1/employees", json=NEW_EMPLOYEE).json()
    payroll = db_client.post(
        f"/api/v1/employees/{employee['id']}/payrolls",
        json={"month": MONTH, "base": "7000", "payment_method": "digital_wallet"},
    ).json()
    month_view = db_client.get("/api/v1/employees", params={"month": MONTH}).json()
    status_view = db_client.get("/api/v1/insights/payroll-status", params={"month": MONTH})
    deactivated = db_client.delete(f"/api/v1/employees/{employee['id']}")
    stored = db_client.get(f"/api/v1/employees/{employee['id']}").json()

    assert (employee["monthly_salary"], employee["department"]) == ("7000.00", "Engineering")
    assert (payroll["currency"], payroll["base"]) == ("USD", "7000.00")
    assert month_view["items"][0]["payroll"]["id"] == payroll["id"]
    assert status_view.json() == {"month": MONTH, "total": 1, "paid": 1, "unpaid": 0}
    assert deactivated.status_code == status.HTTP_204_NO_CONTENT
    assert stored["is_active"] is False


def test_database_constraints_surface_as_conflicts(db_client: TestClient) -> None:
    employee = db_client.post("/api/v1/employees", json=NEW_EMPLOYEE).json()
    payroll = {"month": MONTH, "base": "7000", "payment_method": "bank_transfer"}
    db_client.post(f"/api/v1/employees/{employee['id']}/payrolls", json=payroll)

    duplicate_email = db_client.post("/api/v1/employees", json=NEW_EMPLOYEE)
    duplicate_payroll = db_client.post(f"/api/v1/employees/{employee['id']}/payrolls", json=payroll)

    assert duplicate_email.status_code == status.HTTP_409_CONFLICT
    assert duplicate_payroll.status_code == status.HTTP_409_CONFLICT


def test_an_employee_cannot_be_paid_for_a_month_before_they_were_added(
    db_client: TestClient,
) -> None:
    employee = db_client.post("/api/v1/employees", json=NEW_EMPLOYEE).json()

    response = db_client.post(
        f"/api/v1/employees/{employee['id']}/payrolls",
        json={"month": "2000-01", "base": "7000", "payment_method": "bank_transfer"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "cannot be paid for 2000-01" in response.json()["detail"]


def test_payroll_and_employee_edits_are_saved(db_client: TestClient) -> None:
    employee = db_client.post("/api/v1/employees", json=NEW_EMPLOYEE).json()
    payroll = db_client.post(
        f"/api/v1/employees/{employee['id']}/payrolls",
        json={"month": MONTH, "base": "7000", "payment_method": "bank_transfer"},
    ).json()

    db_client.patch(f"/api/v1/employees/{employee['id']}", json={"job_title": "Legal Counsel"})
    db_client.patch(f"/api/v1/payrolls/{payroll['id']}", json={"bonus": "500"})

    assert db_client.get(f"/api/v1/employees/{employee['id']}").json()["department"] == "Legal"
    assert db_client.get(f"/api/v1/payrolls/{payroll['id']}").json()["bonus"] == "500.00"
    assert (
        db_client.get("/api/v1/insights/pay-by-job-title", params={"country": "US"}).json()[
            "job_titles"
        ][0]["job_title"]
        == "Legal Counsel"
    )


def test_a_raise_leaves_earlier_payrolls_unchanged(db_client: TestClient) -> None:
    employee = db_client.post("/api/v1/employees", json=NEW_EMPLOYEE).json()
    payroll = db_client.post(
        f"/api/v1/employees/{employee['id']}/payrolls",
        json={"month": MONTH, "base": "7000", "payment_method": "bank_transfer"},
    ).json()

    db_client.patch(f"/api/v1/employees/{employee['id']}", json={"monthly_salary": "7700"})

    assert db_client.get(f"/api/v1/employees/{employee['id']}").json()["monthly_salary"] == (
        "7700.00"
    )
    assert db_client.get(f"/api/v1/payrolls/{payroll['id']}").json()["base"] == "7000.00"


def test_logging_out_ends_the_session(db_client: TestClient) -> None:
    profile = db_client.get("/api/v1/auth/me")

    logout = db_client.post("/api/v1/auth/logout")
    after_logout = db_client.get("/api/v1/employees", params={"month": MONTH})

    assert profile.json() == {
        "name": "ACME HR",
        "email": "hr@acme.example",
        "organization": "Test organization",
    }
    assert logout.status_code == status.HTTP_204_NO_CONTENT
    assert after_logout.status_code == status.HTTP_401_UNAUTHORIZED
