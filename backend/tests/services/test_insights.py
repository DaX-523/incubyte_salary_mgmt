from datetime import date
from decimal import Decimal

import pytest

from app.repositories.insights import CountryPayRow, JobTitlePayRow, PaidCount
from app.repositories.population import MonthFilter
from app.schemas.insights import (
    CountryPay,
    JobTitlePay,
    PayByCountry,
    PayByJobTitle,
    PayByJobTitleQuery,
    PayrollStatus,
    PayrollStatusQuery,
)
from app.services.insights import pay_by_country, pay_by_job_title, payroll_status
from tests.fakes import StubInsightsRepository

OCTOBER = date(2026, 10, 1)
# Postgres averages come back with many decimal places; the API sends whole cents, half up.
AVERAGE_ROUNDING = pytest.mark.parametrize(
    ("average", "rounded"),
    [
        (Decimal("4200.3333333333333333"), Decimal("4200.33")),
        (Decimal("4200.0049999999999999"), Decimal("4200.00")),
        (Decimal("4200.0050000000000000"), Decimal("4200.01")),
        (Decimal("4200"), Decimal("4200.00")),
    ],
    ids=["repeating-decimal", "just-under-half-a-cent", "half-a-cent-rounds-up", "whole-number"],
)


def test_payroll_status_reports_the_unpaid_remainder(
    insights_repository: StubInsightsRepository,
) -> None:
    insights_repository.paid_count = PaidCount(total=10, paid=7)

    status = payroll_status(insights_repository, PayrollStatusQuery(month=OCTOBER))

    assert status == PayrollStatus(month=OCTOBER, total=10, paid=7, unpaid=3)


def test_payroll_status_counts_only_the_filtered_employees(
    insights_repository: StubInsightsRepository,
) -> None:
    query = PayrollStatusQuery(month=OCTOBER, country="DE", job_title="Accountant")

    payroll_status(insights_repository, query)

    assert insights_repository.month_filters == [MonthFilter(OCTOBER, "DE", "Accountant")]


def test_pay_by_job_title_reports_ranges_in_the_country_currency(
    insights_repository: StubInsightsRepository,
) -> None:
    insights_repository.job_title_rows = [
        JobTitlePayRow(
            "Accountant", "Finance", 3, Decimal("4200.00"), Decimal("5600.00"), Decimal("4900.00")
        )
    ]

    result = pay_by_job_title(insights_repository, PayByJobTitleQuery(country="JP"))

    assert result == PayByJobTitle(
        country="JP",
        currency="JPY",
        job_titles=[
            JobTitlePay(
                job_title="Accountant",
                department="Finance",
                headcount=3,
                min_salary=Decimal("4200.00"),
                max_salary=Decimal("5600.00"),
                average_salary=Decimal("4900.00"),
            )
        ],
    )
    assert insights_repository.countries == ["JP"]


@AVERAGE_ROUNDING
def test_pay_by_job_title_rounds_the_average_half_up_to_the_cent(
    insights_repository: StubInsightsRepository, average: Decimal, rounded: Decimal
) -> None:
    insights_repository.job_title_rows = [
        JobTitlePayRow("Accountant", "Finance", 3, Decimal("4000.00"), Decimal("4400.00"), average)
    ]

    result = pay_by_job_title(insights_repository, PayByJobTitleQuery(country="DE"))

    assert result.job_titles[0].average_salary == rounded


def test_pay_by_job_title_is_empty_for_a_country_without_employees(
    insights_repository: StubInsightsRepository,
) -> None:
    result = pay_by_job_title(insights_repository, PayByJobTitleQuery(country="SG"))

    assert result.job_titles == []


def test_pay_by_country_reports_each_country_in_its_own_currency(
    insights_repository: StubInsightsRepository,
) -> None:
    insights_repository.country_rows = [
        CountryPayRow("IN", 1012, Decimal("118000.00"), Decimal("119416000.00")),
        CountryPayRow("JP", 987, Decimal("610000.00"), Decimal("602070000.00")),
    ]

    result = pay_by_country(insights_repository)

    assert result == PayByCountry(
        countries=[
            CountryPay(
                country="IN",
                currency="INR",
                headcount=1012,
                average_salary=Decimal("118000.00"),
                total_monthly_salary=Decimal("119416000.00"),
            ),
            CountryPay(
                country="JP",
                currency="JPY",
                headcount=987,
                average_salary=Decimal("610000.00"),
                total_monthly_salary=Decimal("602070000.00"),
            ),
        ]
    )


@AVERAGE_ROUNDING
def test_pay_by_country_rounds_the_average_half_up_to_the_cent(
    insights_repository: StubInsightsRepository, average: Decimal, rounded: Decimal
) -> None:
    insights_repository.country_rows = [CountryPayRow("DE", 3, average, Decimal("12601.00"))]

    result = pay_by_country(insights_repository)

    assert result.countries[0].average_salary == rounded


def test_pay_by_country_is_empty_without_active_employees(
    insights_repository: StubInsightsRepository,
) -> None:
    assert pay_by_country(insights_repository) == PayByCountry(countries=[])
