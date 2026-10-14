"""Deterministic generation of demo employees and their payroll history.

Pure functions only: same arguments (including `seed` and `today`) produce the same data.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import ROUND_HALF_UP, Decimal
from random import Random

from app.db.models import PaymentMethod

CENTS = Decimal("0.01")
SALARY_STEP = Decimal(10)
PAY_DAY = 25
PAY_TIME = time(9, 0, tzinfo=UTC)
EMAIL_DOMAIN = "example.com"

# Share of employees who were already employed before the generated window starts.
EMPLOYED_FOR_WHOLE_WINDOW_RATE = 0.7
INACTIVE_RATE = 0.08
# Active employees not yet paid for the current month; makes "paid vs total" interesting.
UNPAID_CURRENT_MONTH_RATE = 0.15
BONUS_RATE = 0.10
ESOPS_RATE = 0.05
BONUS_SHARES = (Decimal("0.05"), Decimal("0.10"), Decimal("0.20"))
ESOPS_SHARES = (Decimal("0.10"), Decimal("0.25"))

# Most people earn within ±15% of their peer norm (same country and job title)...
PEER_SPREAD_PERCENT = (85, 115)
# ...and a few are planted well below or above it, so "who is paid off-peer?" has answers.
OUTLIER_RATE = 0.03
OUTLIER_FACTORS = (Decimal("0.6"), Decimal("1.6"))

PAYMENT_METHOD_WEIGHTS = {PaymentMethod.BANK_TRANSFER: 85, PaymentMethod.DIGITAL_WALLET: 15}


@dataclass(frozen=True)
class CountryProfile:
    code: str
    currency: str
    # Monthly pay, in local currency, for a job with pay_level 1.0.
    base_monthly_salary: int


COUNTRIES = (
    CountryProfile("US", "USD", 6_000),
    CountryProfile("GB", "GBP", 4_000),
    CountryProfile("DE", "EUR", 4_500),
    CountryProfile("FR", "EUR", 3_800),
    CountryProfile("IN", "INR", 90_000),
    CountryProfile("CA", "CAD", 5_500),
    CountryProfile("AU", "AUD", 6_500),
    CountryProfile("SG", "SGD", 6_000),
    CountryProfile("JP", "JPY", 400_000),
    CountryProfile("BR", "BRL", 8_000),
)
CURRENCY_BY_COUNTRY = {country.code: country.currency for country in COUNTRIES}


@dataclass(frozen=True)
class JobTitle:
    title: str
    department: str
    # Pay relative to the country's base salary.
    pay_level: Decimal


JOB_TITLES = (
    JobTitle("Software Engineer", "Engineering", Decimal("1.3")),
    JobTitle("Senior Software Engineer", "Engineering", Decimal("1.8")),
    JobTitle("Engineering Manager", "Engineering", Decimal("2.3")),
    JobTitle("Product Manager", "Product", Decimal("1.6")),
    JobTitle("Senior Product Manager", "Product", Decimal("2.1")),
    JobTitle("Product Designer", "Design", Decimal("1.2")),
    JobTitle("Senior Product Designer", "Design", Decimal("1.6")),
    JobTitle("Account Executive", "Sales", Decimal("1.1")),
    JobTitle("Sales Manager", "Sales", Decimal("1.7")),
    JobTitle("Marketing Specialist", "Marketing", Decimal("1.0")),
    JobTitle("Marketing Manager", "Marketing", Decimal("1.6")),
    JobTitle("Accountant", "Finance", Decimal("1.1")),
    JobTitle("Financial Analyst", "Finance", Decimal("1.3")),
    JobTitle("HR Generalist", "Human Resources", Decimal("1.0")),
    JobTitle("HR Business Partner", "Human Resources", Decimal("1.5")),
    JobTitle("Operations Associate", "Operations", Decimal("0.9")),
    JobTitle("Operations Manager", "Operations", Decimal("1.5")),
    JobTitle("Support Specialist", "Customer Support", Decimal("0.8")),
    JobTitle("Support Team Lead", "Customer Support", Decimal("1.2")),
    JobTitle("Legal Counsel", "Legal", Decimal("2.0")),
)

FIRST_NAMES = (
    "Aarav", "Aisha", "Alex", "Amelia", "Ana", "Arjun", "Ben", "Carlos", "Chloe", "Daniel",
    "Diya", "Elena", "Emma", "Ethan", "Fatima", "Hana", "Hiro", "Isabel", "James", "Kavya",
    "Leah", "Liam", "Lucas", "Maya", "Mei", "Mohammed", "Noah", "Olivia", "Priya", "Rahul",
    "Rosa", "Sakura", "Sara", "Sofia", "Tom", "Wei", "Yuki", "Zara", "Zoe", "Omar",
)  # fmt: skip
LAST_NAMES = (
    "Anderson", "Brown", "Chen", "Costa", "Dubois", "Fischer", "Garcia", "Gupta", "Haddad",
    "Ito", "Johnson", "Kim", "Kumar", "Lee", "Martin", "Meyer", "Miller", "Moreau", "Nakamura",
    "Nguyen", "Okafor", "Patel", "Pereira", "Rossi", "Sato", "Schmidt", "Shah", "Silva",
    "Singh", "Smith", "Suzuki", "Tanaka", "Taylor", "Thomas", "Wang", "Williams", "Wilson",
    "Wong", "Yamamoto", "Zhang",
)  # fmt: skip


@dataclass(frozen=True)
class EmployeeSeed:
    name: str
    email: str
    monthly_salary: Decimal
    country: str
    department: str
    job_title: str
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class PayrollSeed:
    employee_index: int  # position in SeedData.employees; resolved to a real id on insert
    month: date
    base: Decimal
    bonus: Decimal
    esops: Decimal
    currency: str
    payment_method: PaymentMethod
    paid_at: datetime


@dataclass(frozen=True)
class SeedData:
    employees: list[EmployeeSeed]
    payrolls: list[PayrollSeed]


def recent_months(today: date, count: int) -> list[date]:
    """The first day of the last `count` months, oldest first, ending with today's month."""
    if count < 1:
        raise ValueError(f"count must be at least 1, got {count}")
    month_index = today.year * 12 + today.month - 1 - (count - 1)
    months = []
    for _ in range(count):
        months.append(date(month_index // 12, month_index % 12 + 1, 1))
        month_index += 1
    return months


def generate_seed_data(employee_count: int, months: list[date], today: date, seed: int) -> SeedData:
    """Build employees plus one payroll per paid month, ready to insert."""
    if employee_count < 0:
        raise ValueError(f"employee_count must not be negative, got {employee_count}")
    if not months:
        raise ValueError("months must not be empty")

    rng = Random(seed)
    employees: list[EmployeeSeed] = []
    payrolls: list[PayrollSeed] = []
    for index in range(employee_count):
        employee, employee_payrolls = _employee_with_payrolls(index, months, today, rng)
        employees.append(employee)
        payrolls.extend(employee_payrolls)
    return SeedData(employees=employees, payrolls=payrolls)


def _employee_with_payrolls(
    index: int, months: list[date], today: date, rng: Random
) -> tuple[EmployeeSeed, list[PayrollSeed]]:
    country = rng.choice(COUNTRIES)
    job = rng.choice(JOB_TITLES)
    first_name = rng.choice(FIRST_NAMES)
    last_name = rng.choice(LAST_NAMES)
    monthly_salary = _monthly_salary(country, job, rng)
    last_index = len(months) - 1
    first_month_index = (
        0 if rng.random() < EMPLOYED_FOR_WHOLE_WINDOW_RATE else rng.randint(0, last_index)
    )
    is_active = rng.random() >= INACTIVE_RATE
    if is_active:
        unpaid_now = rng.random() < UNPAID_CURRENT_MONTH_RATE
        end_index = last_index if unpaid_now else last_index + 1
    else:
        # Left at some point inside the window, so never paid for the current month.
        end_index = rng.randint(first_month_index, last_index)
    payment_method = rng.choices(
        list(PAYMENT_METHOD_WEIGHTS), weights=list(PAYMENT_METHOD_WEIGHTS.values())
    )[0]

    employee = EmployeeSeed(
        name=f"{first_name} {last_name}",
        # The index keeps emails unique even when names repeat.
        email=f"{first_name}.{last_name}.{index + 1}@{EMAIL_DOMAIN}".lower(),
        monthly_salary=monthly_salary,
        country=country.code,
        department=job.department,
        job_title=job.title,
        is_active=is_active,
        created_at=datetime.combine(months[first_month_index], PAY_TIME),
    )
    payrolls = [
        PayrollSeed(
            employee_index=index,
            month=month,
            base=monthly_salary,
            bonus=_optional_share(monthly_salary, BONUS_RATE, BONUS_SHARES, rng),
            esops=_optional_share(monthly_salary, ESOPS_RATE, ESOPS_SHARES, rng),
            currency=country.currency,
            payment_method=payment_method,
            paid_at=datetime.combine(min(month.replace(day=PAY_DAY), today), PAY_TIME),
        )
        for month in months[first_month_index:end_index]
    ]
    return employee, payrolls


def _monthly_salary(country: CountryProfile, job: JobTitle, rng: Random) -> Decimal:
    """Country base x job level, spread around the peer norm, rounded to a whole SALARY_STEP."""
    salary = (
        country.base_monthly_salary * job.pay_level * Decimal(rng.randint(*PEER_SPREAD_PERCENT))
    )
    salary /= 100
    if rng.random() < OUTLIER_RATE:
        salary *= rng.choice(OUTLIER_FACTORS)
    steps = (salary / SALARY_STEP).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return (steps * SALARY_STEP).quantize(CENTS)


def _optional_share(
    amount: Decimal, probability: float, shares: tuple[Decimal, ...], rng: Random
) -> Decimal:
    if rng.random() >= probability:
        return Decimal("0.00")
    return (amount * rng.choice(shares)).quantize(CENTS, rounding=ROUND_HALF_UP)
