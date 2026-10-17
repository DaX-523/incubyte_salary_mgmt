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
    average_salary: Money


class PayByJobTitle(BaseModel):
    """Monthly salary range and average per job title among a country's active employees."""

    country: str
    currency: str
    job_titles: list[JobTitlePay]


class CountryPay(BaseModel):
    country: str
    currency: str
    headcount: int
    average_salary: Money
    total_monthly_salary: Money


class PayByCountry(BaseModel):
    """Active employees' monthly salaries per country, each in that country's currency. There is
    no organization-wide total: it would add up different currencies."""

    countries: list[CountryPay]
