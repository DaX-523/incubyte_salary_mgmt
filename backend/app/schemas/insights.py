from pydantic import BaseModel

from app.schemas.common import CountryCode, JobTitleName, Money, Month


class PayrollStatusQuery(BaseModel):
    month: Month
    country: CountryCode | None = None
    job_title: JobTitleName | None = None


class PayrollStatus(BaseModel):
    """How many of the employees on the books in `month` have been paid for it."""

    month: Month
    total: int
    paid: int
    unpaid: int


class PayByJobTitleQuery(BaseModel):
    # Required: salaries are only comparable within one country's currency.
    country: CountryCode


class JobTitlePay(BaseModel):
    job_title: str
    department: str
    headcount: int
    min_salary: Money
    max_salary: Money


class PayByJobTitle(BaseModel):
    """Monthly salary range per job title among a country's active employees."""

    country: str
    currency: str
    job_titles: list[JobTitlePay]
