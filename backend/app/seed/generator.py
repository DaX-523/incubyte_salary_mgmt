"""Deterministic generation of demo employees and their payroll history.

Pure functions only: same arguments (including `seed` and `today`) produce the same data.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from random import Random

from app.db.models import PaymentMethod

CENTS = Decimal("0.01")
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

PAYMENT_METHODS = tuple(PaymentMethod)
PAYMENT_METHOD_WEIGHTS = (80, 5, 3, 12)


@dataclass(frozen=True)
class CountryProfile:
    code: str
    currency: str
    min_monthly_salary: int
    max_monthly_salary: int


COUNTRIES = (
    CountryProfile("US", "USD", 4_000, 18_000),
    CountryProfile("GB", "GBP", 3_000, 12_000),
    CountryProfile("DE", "EUR", 3_500, 12_000),
    CountryProfile("FR", "EUR", 3_000, 10_000),
    CountryProfile("IN", "INR", 50_000, 600_000),
    CountryProfile("CA", "CAD", 4_500, 16_000),
    CountryProfile("AU", "AUD", 5_000, 17_000),
    CountryProfile("SG", "SGD", 4_500, 17_000),
    CountryProfile("JP", "JPY", 300_000, 1_500_000),
    CountryProfile("BR", "BRL", 5_000, 35_000),
)
CURRENCY_BY_COUNTRY = {country.code: country.currency for country in COUNTRIES}

DEPARTMENTS = (
    "Engineering",
    "Product",
    "Design",
    "Sales",
    "Marketing",
    "Finance",
    "Human Resources",
    "Operations",
    "Customer Support",
    "Legal",
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
    is_active: bool
    created_at: datetime
    last_transaction_at: datetime | None


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
        employee_payrolls = _payrolls_for(index, months, today, rng)
        employees.append(_employee(index, months, employee_payrolls, rng))
        payrolls.extend(employee_payrolls.payrolls)
    return SeedData(employees=employees, payrolls=payrolls)


@dataclass(frozen=True)
class _EmploymentHistory:
    profile: CountryProfile
    monthly_salary: Decimal
    first_month_index: int
    is_active: bool
    payrolls: list[PayrollSeed]


def _payrolls_for(index: int, months: list[date], today: date, rng: Random) -> _EmploymentHistory:
    profile = rng.choice(COUNTRIES)
    monthly_salary = Decimal(
        rng.randint(profile.min_monthly_salary // 10, profile.max_monthly_salary // 10) * 10
    ).quantize(CENTS)
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
    payment_method = rng.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS)[0]

    payrolls = [
        PayrollSeed(
            employee_index=index,
            month=month,
            base=monthly_salary,
            bonus=_optional_share(monthly_salary, BONUS_RATE, BONUS_SHARES, rng),
            esops=_optional_share(monthly_salary, ESOPS_RATE, ESOPS_SHARES, rng),
            currency=profile.currency,
            payment_method=payment_method,
            paid_at=datetime.combine(min(month.replace(day=PAY_DAY), today), PAY_TIME),
        )
        for month in months[first_month_index:end_index]
    ]
    return _EmploymentHistory(profile, monthly_salary, first_month_index, is_active, payrolls)


def _employee(
    index: int, months: list[date], history: _EmploymentHistory, rng: Random
) -> EmployeeSeed:
    first_name = rng.choice(FIRST_NAMES)
    last_name = rng.choice(LAST_NAMES)
    return EmployeeSeed(
        name=f"{first_name} {last_name}",
        # The index keeps emails unique even when names repeat.
        email=f"{first_name}.{last_name}.{index + 1}@{EMAIL_DOMAIN}".lower(),
        monthly_salary=history.monthly_salary,
        country=history.profile.code,
        department=rng.choice(DEPARTMENTS),
        is_active=history.is_active,
        created_at=datetime.combine(months[history.first_month_index], PAY_TIME),
        last_transaction_at=history.payrolls[-1].paid_at if history.payrolls else None,
    )


def _optional_share(
    amount: Decimal, probability: float, shares: tuple[Decimal, ...], rng: Random
) -> Decimal:
    if rng.random() >= probability:
        return Decimal("0.00")
    return (amount * rng.choice(shares)).quantize(CENTS)
