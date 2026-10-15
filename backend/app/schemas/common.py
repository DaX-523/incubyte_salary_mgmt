"""Types shared by the API contract: months, money, catalog values and pagination."""

import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    StringConstraints,
    WithJsonSchema,
    model_validator,
)

from app.domain.catalog import CURRENCY_BY_COUNTRY, DEPARTMENT_BY_JOB_TITLE

CENTS = Decimal("0.01")
MONTH_PATTERN = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
# Ids are Postgres BIGINTs; anything larger can never match a row.
MAX_ID = 2**63 - 1
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


def parse_month(value: object) -> date:
    """Accept "YYYY-MM" from clients and stored month dates (always the 1st) from the database."""
    if isinstance(value, date):
        return value.replace(day=1)
    if not isinstance(value, str) or not (match := MONTH_PATTERN.fullmatch(value)):
        raise ValueError("expected a month formatted as YYYY-MM, for example 2026-10")
    return date(int(match[1]), int(match[2]), 1)


def format_month(value: date) -> str:
    return f"{value:%Y-%m}"


def to_cents(amount: Decimal) -> Decimal:
    """Always two decimal places, so "7000" and "7000.00" are the same amount on the wire."""
    return amount.quantize(CENTS, rounding=ROUND_HALF_UP)


def ensure_known_country(code: str) -> str:
    if code not in CURRENCY_BY_COUNTRY:
        raise ValueError(f"unknown country {code!r}; expected one of {sorted(CURRENCY_BY_COUNTRY)}")
    return code


def ensure_known_job_title(title: str) -> str:
    if title not in DEPARTMENT_BY_JOB_TITLE:
        raise ValueError(f"unknown job title {title!r}")
    return title


Month = Annotated[
    date,
    BeforeValidator(parse_month),
    PlainSerializer(format_month, return_type=str),
    WithJsonSchema({"type": "string", "pattern": MONTH_PATTERN.pattern, "examples": ["2026-10"]}),
]
# Decimal strings on the wire; Numeric(14, 2) in the database.
Money = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2), AfterValidator(to_cents)]
CountryCode = Annotated[str, AfterValidator(ensure_known_country)]
JobTitleName = Annotated[str, AfterValidator(ensure_known_job_title)]
EmployeeName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
PageNumber = Annotated[int, Field(ge=1)]
PageSize = Annotated[int, Field(ge=1, le=MAX_PAGE_SIZE)]


class PartialUpdate(BaseModel):
    """PATCH body: send only the fields to change. Sent fields may not be null."""

    @model_validator(mode="after")
    def _require_non_null_changes(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("send at least one field to update")
        nulls = sorted(name for name in self.model_fields_set if getattr(self, name) is None)
        if nulls:
            raise ValueError(f"fields cannot be null: {', '.join(nulls)}")
        return self


class Page[ItemT](BaseModel):
    items: list[ItemT]
    total: int
    page: int
    page_size: int
