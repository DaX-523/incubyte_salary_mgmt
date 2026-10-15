"""Deterministic generation of demo employees and their payroll history.

Pure functions only: same arguments (including `seed` and `today`) produce the same data.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import ROUND_HALF_UP, Decimal
from random import Random

from app.db.models import PaymentMethod
from app.domain.catalog import COUNTRIES, JOB_TITLES, Country, JobTitle

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


# Monthly pay, in each country's local currency, for a job with pay level 1.0.
BASE_MONTHLY_SALARY_BY_COUNTRY = {
    "US": 6_000,
    "GB": 4_000,
    "DE": 4_500,
    "FR": 3_800,
    "IN": 90_000,
    "CA": 5_500,
    "AU": 6_500,
    "SG": 6_000,
    "JP": 400_000,
    "BR": 8_000,
}

# Pay relative to the country's base salary.
PAY_LEVEL_BY_JOB_TITLE = {
    "Software Engineer": Decimal("1.3"),
    "Senior Software Engineer": Decimal("1.8"),
    "Engineering Manager": Decimal("2.3"),
    "Product Manager": Decimal("1.6"),
    "Senior Product Manager": Decimal("2.1"),
    "Product Designer": Decimal("1.2"),
    "Senior Product Designer": Decimal("1.6"),
    "Account Executive": Decimal("1.1"),
    "Sales Manager": Decimal("1.7"),
    "Marketing Specialist": Decimal("1.0"),
    "Marketing Manager": Decimal("1.6"),
    "Accountant": Decimal("1.1"),
    "Financial Analyst": Decimal("1.3"),
    "HR Generalist": Decimal("1.0"),
    "HR Business Partner": Decimal("1.5"),
    "Operations Associate": Decimal("0.9"),
    "Operations Manager": Decimal("1.5"),
    "Support Specialist": Decimal("0.8"),
    "Support Team Lead": Decimal("1.2"),
    "Legal Counsel": Decimal("2.0"),
}

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


def _monthly_salary(country: Country, job: JobTitle, rng: Random) -> Decimal:
    """Country base x job level, spread around the peer norm, rounded to a whole SALARY_STEP."""
    salary = (
        BASE_MONTHLY_SALARY_BY_COUNTRY[country.code]
        * PAY_LEVEL_BY_JOB_TITLE[job.title]
        * Decimal(rng.randint(*PEER_SPREAD_PERCENT))
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
