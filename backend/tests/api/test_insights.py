from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.repositories.insights import JobTitlePayRow, PaidCount
from app.repositories.population import MonthFilter
from tests.fakes import StubInsightsRepository


def test_payroll_status_reports_paid_and_total_for_the_month(
    api_client: TestClient, insights_repository: StubInsightsRepository
) -> None:
    insights_repository.paid_count = PaidCount(total=9168, paid=7815)

    response = api_client.get(
        "/api/v1/insights/payroll-status", params={"month": "2026-10", "country": "GB"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"month": "2026-10", "total": 9168, "paid": 7815, "unpaid": 1353}
    assert insights_repository.month_filters == [MonthFilter(date(2026, 10, 1), "GB", None)]


@pytest.mark.parametrize(
    "params",
    [{}, {"month": "2026-1"}, {"month": "2026-10", "job_title": "Wizard"}],
    ids=["missing-month", "bad-month", "unknown-job-title"],
)
def test_payroll_status_rejects_invalid_filters(
    api_client: TestClient, params: dict[str, Any]
) -> None:
    response = api_client.get("/api/v1/insights/payroll-status", params=params)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_pay_by_job_title_lists_salary_ranges_for_one_country(
    api_client: TestClient, insights_repository: StubInsightsRepository
) -> None:
    insights_repository.job_title_rows = [
        JobTitlePayRow("Accountant", "Finance", 41, Decimal("3060.00"), Decimal("4140.00"))
    ]

    response = api_client.get("/api/v1/insights/pay-by-job-title", params={"country": "DE"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "country": "DE",
        "currency": "EUR",
        "job_titles": [
            {
                "job_title": "Accountant",
                "department": "Finance",
                "headcount": 41,
                "min_salary": "3060.00",
                "max_salary": "4140.00",
            }
        ],
    }


@pytest.mark.parametrize(
    "params", [{}, {"country": "XX"}], ids=["country-is-required", "unknown-country"]
)
def test_pay_by_job_title_needs_a_known_country(
    api_client: TestClient, params: dict[str, Any]
) -> None:
    response = api_client.get("/api/v1/insights/pay-by-job-title", params=params)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
