"""The countries and job titles the organization employs people in.

A country decides the currency its salaries are paid in, and a job title decides its department.
The API accepts only these values and derives currency and department from them.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Country:
    code: str  # ISO 3166-1 alpha-2
    currency: str  # ISO 4217


@dataclass(frozen=True)
class JobTitle:
    title: str
    department: str


COUNTRIES = (
    Country("US", "USD"),
    Country("GB", "GBP"),
    Country("DE", "EUR"),
    Country("FR", "EUR"),
    Country("IN", "INR"),
    Country("CA", "CAD"),
    Country("AU", "AUD"),
    Country("SG", "SGD"),
    Country("JP", "JPY"),
    Country("BR", "BRL"),
)

JOB_TITLES = (
    JobTitle("Software Engineer", "Engineering"),
    JobTitle("Senior Software Engineer", "Engineering"),
    JobTitle("Engineering Manager", "Engineering"),
    JobTitle("Product Manager", "Product"),
    JobTitle("Senior Product Manager", "Product"),
    JobTitle("Product Designer", "Design"),
    JobTitle("Senior Product Designer", "Design"),
    JobTitle("Account Executive", "Sales"),
    JobTitle("Sales Manager", "Sales"),
    JobTitle("Marketing Specialist", "Marketing"),
    JobTitle("Marketing Manager", "Marketing"),
    JobTitle("Accountant", "Finance"),
    JobTitle("Financial Analyst", "Finance"),
    JobTitle("HR Generalist", "Human Resources"),
    JobTitle("HR Business Partner", "Human Resources"),
    JobTitle("Operations Associate", "Operations"),
    JobTitle("Operations Manager", "Operations"),
    JobTitle("Support Specialist", "Customer Support"),
    JobTitle("Support Team Lead", "Customer Support"),
    JobTitle("Legal Counsel", "Legal"),
)

CURRENCY_BY_COUNTRY = {country.code: country.currency for country in COUNTRIES}
DEPARTMENT_BY_JOB_TITLE = {job.title: job.department for job in JOB_TITLES}
