from collections import Counter
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.db.models import PaymentMethod
from app.domain.catalog import COUNTRIES, CURRENCY_BY_COUNTRY, JOB_TITLES
from app.seed.generator import (
    BASE_MONTHLY_SALARY_BY_COUNTRY,
    PAY_DAY,
    PAY_LEVEL_BY_JOB_TITLE,
    EmployeeSeed,
    SeedData,
    generate_seed_data,
    recent_months,
)

TODAY = date(2026, 10, 14)
MONTHS = recent_months(TODAY, 12)
CURRENT_MONTH = date(2026, 10, 1)


def peer_ratio(employee: EmployeeSeed) -> Decimal:
    """Salary relative to the norm for its peers (same country and job title)."""
    norm = (
        BASE_MONTHLY_SALARY_BY_COUNTRY[employee.country]
        * PAY_LEVEL_BY_JOB_TITLE[employee.job_title]
    )
    return employee.monthly_salary / norm


@pytest.fixture(scope="module")
def data() -> SeedData:
    return generate_seed_data(employee_count=500, months=MONTHS, today=TODAY, seed=7)


@pytest.mark.parametrize(
    ("today", "count", "expected"),
    [
        (date(2026, 10, 14), 3, [date(2026, 8, 1), date(2026, 9, 1), date(2026, 10, 1)]),
        (date(2026, 2, 28), 3, [date(2025, 12, 1), date(2026, 1, 1), date(2026, 2, 1)]),
        (date(2026, 1, 31), 1, [date(2026, 1, 1)]),
    ],
    ids=["same-year", "crosses-year-boundary", "single-month"],
)
def test_recent_months_lists_month_starts_oldest_first(
    today: date, count: int, expected: list[date]
) -> None:
    assert recent_months(today, count) == expected


@pytest.mark.parametrize("count", [0, -1])
def test_recent_months_rejects_non_positive_count(count: int) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        recent_months(TODAY, count)


def test_pay_tables_cover_exactly_the_catalog() -> None:
    assert set(BASE_MONTHLY_SALARY_BY_COUNTRY) == {country.code for country in COUNTRIES}
    assert set(PAY_LEVEL_BY_JOB_TITLE) == {job.title for job in JOB_TITLES}


def test_generation_is_deterministic_for_a_seed() -> None:
    first = generate_seed_data(employee_count=50, months=MONTHS, today=TODAY, seed=1)
    second = generate_seed_data(employee_count=50, months=MONTHS, today=TODAY, seed=1)

    assert first == second


def test_different_seeds_produce_different_data() -> None:
    first = generate_seed_data(employee_count=50, months=MONTHS, today=TODAY, seed=1)
    second = generate_seed_data(employee_count=50, months=MONTHS, today=TODAY, seed=2)

    assert first != second


def test_generates_the_requested_number_of_employees(data: SeedData) -> None:
    assert len(data.employees) == 500


def test_zero_employees_produces_no_data() -> None:
    data = generate_seed_data(employee_count=0, months=MONTHS, today=TODAY, seed=1)

    assert data == SeedData(employees=[], payrolls=[])


def test_rejects_negative_employee_count() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        generate_seed_data(employee_count=-1, months=MONTHS, today=TODAY, seed=1)


def test_rejects_empty_month_window() -> None:
    with pytest.raises(ValueError, match="months must not be empty"):
        generate_seed_data(employee_count=1, months=[], today=TODAY, seed=1)


def test_employee_emails_are_unique(data: SeedData) -> None:
    emails = [employee.email for employee in data.employees]

    assert len(set(emails)) == len(emails)


def test_salaries_are_positive_whole_tens(data: SeedData) -> None:
    invalid = [
        employee.monthly_salary
        for employee in data.employees
        if employee.monthly_salary <= 0
        or employee.monthly_salary % 10 != 0
        or employee.monthly_salary.as_tuple().exponent != -2
    ]

    assert invalid == []


def test_job_titles_belong_to_the_employee_department(data: SeedData) -> None:
    known_roles = {(job.title, job.department) for job in JOB_TITLES}

    assert {(e.job_title, e.department) for e in data.employees} <= known_roles


def test_most_salaries_sit_near_their_peer_norm(data: SeedData) -> None:
    # ±15% spread, plus a little slack for rounding to whole tens.
    near_norm = [e for e in data.employees if Decimal("0.84") <= peer_ratio(e) <= Decimal("1.16")]

    assert len(near_norm) / len(data.employees) >= 0.9


def test_some_salaries_are_planted_far_below_and_above_peers(data: SeedData) -> None:
    ratios = [peer_ratio(employee) for employee in data.employees]

    assert min(ratios) < Decimal("0.7")
    assert max(ratios) > Decimal("1.4")


def test_each_employee_is_paid_at_most_once_per_month(data: SeedData) -> None:
    pay_counts = Counter((payroll.employee_index, payroll.month) for payroll in data.payrolls)

    assert max(pay_counts.values()) == 1


def test_payrolls_fall_on_month_starts_inside_the_window(data: SeedData) -> None:
    assert {payroll.month for payroll in data.payrolls} <= set(MONTHS)


def test_payrolls_use_the_employee_salary_and_country_currency(data: SeedData) -> None:
    mismatched = [
        payroll
        for payroll in data.payrolls
        if payroll.base != data.employees[payroll.employee_index].monthly_salary
        or payroll.currency != CURRENCY_BY_COUNTRY[data.employees[payroll.employee_index].country]
    ]

    assert mismatched == []


def test_payrolls_use_exactly_the_supported_payment_methods(data: SeedData) -> None:
    assert {payroll.payment_method for payroll in data.payrolls} == set(PaymentMethod)


def test_bonuses_and_esops_are_non_negative_and_sometimes_paid(data: SeedData) -> None:
    bonuses = [payroll.bonus for payroll in data.payrolls]
    esops = [payroll.esops for payroll in data.payrolls]

    assert min(bonuses) == min(esops) == Decimal("0.00")
    assert max(bonuses) > 0
    assert max(esops) > 0


def test_inactive_employees_are_not_paid_for_the_current_month(data: SeedData) -> None:
    paid_now = {p.employee_index for p in data.payrolls if p.month == CURRENT_MONTH}
    inactive = {i for i, employee in enumerate(data.employees) if not employee.is_active}

    assert inactive
    assert paid_now.isdisjoint(inactive)


def test_some_active_employees_are_still_unpaid_this_month(data: SeedData) -> None:
    paid_now = {p.employee_index for p in data.payrolls if p.month == CURRENT_MONTH}
    active = {i for i, employee in enumerate(data.employees) if employee.is_active}

    assert 0 < len(paid_now) < len(active)


def test_payments_are_never_dated_in_the_future(data: SeedData) -> None:
    current_month_paid_at = {p.paid_at for p in data.payrolls if p.month == CURRENT_MONTH}
    earlier_paid_days = {p.paid_at.day for p in data.payrolls if p.month < CURRENT_MONTH}

    assert current_month_paid_at == {datetime(2026, 10, 14, 9, 0, tzinfo=UTC)}
    assert earlier_paid_days == {PAY_DAY}
