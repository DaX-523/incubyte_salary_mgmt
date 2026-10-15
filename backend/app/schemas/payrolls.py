from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from app.db.models import PaymentMethod, Payroll
from app.schemas.common import Money, Month, PartialUpdate


class PayrollCreate(BaseModel):
    """The currency comes from the employee's country, so clients don't send it."""

    model_config = ConfigDict(extra="forbid")

    month: Month
    base: Money
    bonus: Money = Decimal("0.00")
    esops: Money = Decimal("0.00")
    payment_method: PaymentMethod


class PayrollUpdate(PartialUpdate):
    """Employee, month and currency identify the payment and cannot change."""

    model_config = ConfigDict(extra="forbid")

    base: Money | None = None
    bonus: Money | None = None
    esops: Money | None = None
    payment_method: PaymentMethod | None = None


class PayrollOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    month: Month
    base: Money
    bonus: Money
    esops: Money
    currency: str
    payment_method: PaymentMethod

    @classmethod
    def from_model(cls, payroll: Payroll) -> Self:
        return cls.model_validate(payroll)
