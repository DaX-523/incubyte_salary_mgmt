from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from tests.fakes import InMemoryPayrollRepository, make_payroll


def test_get_returns_the_payroll(
    api_client: TestClient, payroll_repository: InMemoryPayrollRepository
) -> None:
    payroll_repository.add(make_payroll(employee_id=3))

    response = api_client.get("/api/v1/payrolls/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": 1,
        "employee_id": 3,
        "month": "2026-10",
        "base": "5000.00",
        "bonus": "0.00",
        "esops": "0.00",
        "currency": "GBP",
        "payment_method": "bank_transfer",
    }


def test_get_reports_a_missing_payroll(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/payrolls/7")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Payroll 7 not found"}


def test_update_changes_the_sent_fields(
    api_client: TestClient, payroll_repository: InMemoryPayrollRepository
) -> None:
    payroll_repository.add(make_payroll())

    response = api_client.patch(
        "/api/v1/payrolls/1", json={"esops": "1200", "payment_method": "digital_wallet"}
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert (body["base"], body["esops"]) == ("5000.00", "1200.00")
    assert body["payment_method"] == "digital_wallet"


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({}, "send at least one field"),
        ({"bonus": None}, "fields cannot be null: bonus"),
        ({"month": "2026-11"}, "Extra inputs are not permitted"),
        ({"employee_id": 2}, "Extra inputs are not permitted"),
        ({"currency": "USD"}, "Extra inputs are not permitted"),
        ({"payment_method": "cheque"}, "'bank_transfer' or 'digital_wallet'"),
    ],
    ids=[
        "empty",
        "null-bonus",
        "month-is-fixed",
        "employee-is-fixed",
        "currency-is-fixed",
        "retired-method",
    ],
)
def test_update_rejects_invalid_changes(
    api_client: TestClient,
    payroll_repository: InMemoryPayrollRepository,
    body: dict[str, Any],
    message: str,
) -> None:
    payroll_repository.add(make_payroll())

    response = api_client.patch("/api/v1/payrolls/1", json=body)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert message in response.text


def test_update_reports_a_missing_payroll(api_client: TestClient) -> None:
    response = api_client.patch("/api/v1/payrolls/7", json={"bonus": "10.00"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
