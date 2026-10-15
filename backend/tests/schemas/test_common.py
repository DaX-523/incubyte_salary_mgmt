from datetime import date
from decimal import Decimal

import pytest

from app.schemas.common import format_month, parse_month, to_cents


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-10", date(2026, 10, 1)),
        ("2026-01", date(2026, 1, 1)),
        ("2026-12", date(2026, 12, 1)),
        (date(2026, 10, 1), date(2026, 10, 1)),
        (date(2026, 10, 15), date(2026, 10, 1)),
    ],
    ids=["text", "january", "december", "month-start-date", "mid-month-date"],
)
def test_parse_month_returns_the_first_day_of_the_month(value: object, expected: date) -> None:
    assert parse_month(value) == expected


@pytest.mark.parametrize(
    "value",
    ["2026-13", "2026-00", "2026-1", "26-10", "2026/10", "2026-10-01", "October", "", 202610],
    ids=[
        "month-13",
        "month-00",
        "single-digit-month",
        "two-digit-year",
        "slash",
        "full-date",
        "month-name",
        "empty",
        "number",
    ],
)
def test_parse_month_rejects_anything_but_year_dash_month(value: object) -> None:
    with pytest.raises(ValueError, match="YYYY-MM"):
        parse_month(value)


def test_parse_month_rejects_year_zero() -> None:
    with pytest.raises(ValueError, match="year 0 is out of range"):
        parse_month("0000-01")


def test_format_month_writes_year_dash_month() -> None:
    assert format_month(date(2026, 3, 1)) == "2026-03"


@pytest.mark.parametrize(
    ("amount", "expected"),
    [("7000", "7000.00"), ("0", "0.00"), ("12.5", "12.50"), ("12.34", "12.34")],
    ids=["whole", "zero", "one-decimal", "two-decimals"],
)
def test_to_cents_always_has_two_decimal_places(amount: str, expected: str) -> None:
    assert str(to_cents(Decimal(amount))) == expected
