from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Up to 999,999,999,999.99 in any currency. Never use floats for money.
Money = Numeric(14, 2)


class PaymentMethod(StrEnum):
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Organization(TimestampMixin, Base):
    """A company using the portal. Its users only ever see its own employees."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)


class User(TimestampMixin, Base):
    """Someone who logs in to manage their organization's employees."""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("session_version >= 1", name="session_version_positive"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    # Stored lowercase, so logging in ignores the email's case.
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    # Copied into every token; logging out bumps it, which invalidates all earlier tokens.
    session_version: Mapped[int] = mapped_column(Integer, server_default="1")


class Employee(TimestampMixin, Base):
    """An employee. `monthly_salary` is in the local currency of `country`, so salaries are only
    compared or aggregated within one country (peers: same country and job title)."""

    __tablename__ = "employees"
    __table_args__ = (
        # Emails are unique within an organization; another company may employ the same person.
        UniqueConstraint("organization_id", "email"),
        CheckConstraint("monthly_salary >= 0", name="monthly_salary_non_negative"),
        CheckConstraint("country ~ '^[A-Z]{2}$'", name="country_iso_alpha2"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), index=True)
    email: Mapped[str] = mapped_column(String(320))
    monthly_salary: Mapped[Decimal] = mapped_column(Money)
    country: Mapped[str] = mapped_column(String(2), index=True)
    department: Mapped[str] = mapped_column(String(100), index=True)
    job_title: Mapped[str] = mapped_column(String(150), index=True)
    is_active: Mapped[bool] = mapped_column(server_default=true())


class Payroll(TimestampMixin, Base):
    __tablename__ = "payrolls"
    __table_args__ = (
        # One payroll per employee per month: also what makes "paid this month" countable.
        UniqueConstraint("employee_id", "month"),
        CheckConstraint("EXTRACT(DAY FROM month) = 1", name="month_is_first_day"),
        CheckConstraint("base >= 0", name="base_non_negative"),
        CheckConstraint("bonus >= 0", name="bonus_non_negative"),
        CheckConstraint("esops >= 0", name="esops_non_negative"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency_iso_4217"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id", ondelete="RESTRICT")
    )
    month: Mapped[date] = mapped_column(Date, index=True)
    base: Mapped[Decimal] = mapped_column(Money)
    bonus: Mapped[Decimal] = mapped_column(Money, server_default="0")
    esops: Mapped[Decimal] = mapped_column(Money, server_default="0")
    currency: Mapped[str] = mapped_column(String(3))
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(
            PaymentMethod,
            name="payment_method",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda methods: [method.value for method in methods],
        )
    )
