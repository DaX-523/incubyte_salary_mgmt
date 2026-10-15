from app.domain.catalog import CURRENCY_BY_COUNTRY
from app.repositories.insights import InsightsRepository
from app.repositories.population import MonthFilter
from app.schemas.insights import (
    JobTitlePay,
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
            )
            for row in repository.pay_by_job_title(query.country)
        ],
    )
