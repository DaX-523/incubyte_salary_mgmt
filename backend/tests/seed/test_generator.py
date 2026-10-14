from collections import Counter
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.seed.generator import (
    COUNTRIES,
    CURRENCY_BY_COUNTRY,
    PAY_DAY,
    SeedData,
    generate_seed_data,
    recent_months,
)

TODAY = date(2026, 10, 14)
MONTHS = recent_months(TODAY, 12)
CURRENT_MONTH = date(2026, 10, 1)
SALARY_RANGE_BY_COUNTRY = {
    country.code: (country.min_monthly_salary, country.max_monthly_salary) for country in COUNTRIES
}


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


def test_salaries_are_whole_cents_within_the_country_range(data: SeedData) -> None:
    out_of_range = [
        employee
        for employee in data.employees
        if not (
            SALARY_RANGE_BY_COUNTRY[employee.country][0]
            <= employee.monthly_salary
            <= SALARY_RANGE_BY_COUNTRY[employee.country][1]
        )
        or employee.monthly_salary.as_tuple().exponent != -2
    ]

    assert out_of_range == []


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


def test_last_transaction_is_the_latest_payment_or_none(data: SeedData) -> None:
    # Payrolls are generated oldest first, so the last one per employee wins.
    latest_paid_at = {payroll.employee_index: payroll.paid_at for payroll in data.payrolls}
    expected = [latest_paid_at.get(index) for index in range(len(data.employees))]

    assert [employee.last_transaction_at for employee in data.employees] == expected
    assert None in expected
