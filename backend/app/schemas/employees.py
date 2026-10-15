from enum import StrEnum
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    StringConstraints,
    model_validator,
)

from app.db.models import Employee
from app.domain.catalog import CURRENCY_BY_COUNTRY
from app.schemas.common import (
    DEFAULT_PAGE_SIZE,
    CountryCode,
    EmployeeName,
    JobTitleName,
    Money,
    Month,
    PageNumber,
    PageSize,
    PartialUpdate,
)
from app.schemas.payrolls import PayrollOut

# Emails are unique per employee regardless of letter case.
Email = Annotated[EmailStr, AfterValidator(str.lower)]
# Any part of an email address, matched ignoring case like the name search.
EmailSearch = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=320)]


class EmployeeCreate(BaseModel):
    """Department and currency follow from job title and country, so clients don't send them."""

    model_config = ConfigDict(extra="forbid")

    name: EmployeeName
    email: Email
    monthly_salary: Money
    country: CountryCode
    job_title: JobTitleName


class EmployeeUpdate(PartialUpdate):
    """Country is fixed once set: the salary is in its currency."""

    model_config = ConfigDict(extra="forbid")

    name: EmployeeName | None = None
    email: Email | None = None
    monthly_salary: Money | None = None
    job_title: JobTitleName | None = None


class EmployeeOut(BaseModel):
    id: int
    name: str
    email: str
    monthly_salary: Money
    currency: str
    country: str
    department: str
    job_title: str
    is_active: bool

    @classmethod
    def from_model(cls, employee: Employee) -> Self:
        return cls(
            id=employee.id,
            name=employee.name,
            email=employee.email,
            monthly_salary=employee.monthly_salary,
            currency=CURRENCY_BY_COUNTRY[employee.country],
            country=employee.country,
            department=employee.department,
            job_title=employee.job_title,
            is_active=employee.is_active,
        )


class EmployeeSortField(StrEnum):
    NAME = "name"
    MONTHLY_SALARY = "monthly_salary"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class MonthlyEmployeeQuery(BaseModel):
    """Who is on the books in `month`, filtered, sorted and paginated."""

    month: Month
    name: EmployeeName | None = None
    email: EmailSearch | None = None
    country: CountryCode | None = None
    job_title: JobTitleName | None = None
    sort_by: EmployeeSortField = EmployeeSortField.NAME
    sort_order: SortOrder = SortOrder.ASC
    page: PageNumber = 1
    page_size: PageSize = DEFAULT_PAGE_SIZE

    @model_validator(mode="after")
    def _salary_sort_needs_a_country(self) -> Self:
        if self.sort_by is EmployeeSortField.MONTHLY_SALARY and self.country is None:
            raise ValueError(
                "sorting by monthly_salary needs a country filter: salaries are in local currencies"
            )
        return self


class MonthlyEmployee(BaseModel):
    employee: EmployeeOut
    payroll: PayrollOut | None  # None: not paid for the month yet
