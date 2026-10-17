from app.domain.catalog import CURRENCY_BY_COUNTRY
from app.repositories.insights import InsightsRepository
from app.repositories.population import MonthFilter
from app.schemas.common import to_cents
from app.schemas.insights import (
    CountryPay,
    JobTitlePay,
    PayByCountry,
    PayByJobTitle,
    PayByJobTitleQuery,
    PayrollStatus,
    PayrollStatusQuery,
)


def payroll_status(repository: InsightsRepository, query: PayrollStatusQuery) -> PayrollStatus:
    counts = repository.count_paid(MonthFilter(query.month, query.country, query.job_title))
    return PayrollStatus(
        month=query.month, total=counts.total, paid=counts.paid, unpaid=counts.total - counts.paid
    )


def pay_by_job_title(repository: InsightsRepository, query: PayByJobTitleQuery) -> PayByJobTitle:
    return PayByJobTitle(
        country=query.country,
        currency=CURRENCY_BY_COUNTRY[query.country],
        job_titles=[
            JobTitlePay(
                job_title=row.job_title,
                department=row.department,
                headcount=row.headcount,
                min_salary=row.min_salary,
                max_salary=row.max_salary,
                # Averages are rounded half up to the cent, like every amount the API sends.
                average_salary=to_cents(row.average_salary),
            )
            for row in repository.pay_by_job_title(query.country)
        ],
    )


def pay_by_country(repository: InsightsRepository) -> PayByCountry:
    return PayByCountry(
        countries=[
            CountryPay(
                country=row.country,
                currency=CURRENCY_BY_COUNTRY[row.country],
                headcount=row.headcount,
                average_salary=to_cents(row.average_salary),
                total_monthly_salary=row.total_salary,
            )
            for row in repository.pay_by_country()
        ]
    )
