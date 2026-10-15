from datetime import date
from decimal import Decimal

from app.repositories.insights import JobTitlePayRow, PaidCount
from app.repositories.population import MonthFilter
from app.schemas.insights import (
    JobTitlePay,
    PayByJobTitle,
    PayByJobTitleQuery,
    PayrollStatus,
    PayrollStatusQuery,
)
from app.services.insights import pay_by_job_title, payroll_status
from tests.fakes import StubInsightsRepository

OCTOBER = date(2026, 10, 1)


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
        JobTitlePayRow("Accountant", "Finance", 3, Decimal("4200.00"), Decimal("5600.00"))
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
            )
        ],
    )
    assert insights_repository.countries == ["JP"]


def test_pay_by_job_title_is_empty_for_a_country_without_employees(
    insights_repository: StubInsightsRepository,
) -> None:
    result = pay_by_job_title(insights_repository, PayByJobTitleQuery(country="SG"))

    assert result.job_titles == []
