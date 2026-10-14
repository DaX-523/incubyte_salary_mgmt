"""Create employees and payrolls.

Revision ID: 0001
Revises:
Create Date: 2026-10-14

"""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen copy of PaymentMethod's values: migrations must not import application code.
PAYMENT_METHODS = ("bank_transfer", "cheque", "cash", "digital_wallet")


def timestamp_columns() -> list[sa.Column[datetime]]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("monthly_salary", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("last_transaction_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint(
            "monthly_salary >= 0", name=op.f("ck_employees_monthly_salary_non_negative")
        ),
        sa.CheckConstraint("country ~ '^[A-Z]{2}$'", name=op.f("ck_employees_country_iso_alpha2")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employees")),
        sa.UniqueConstraint("email", name=op.f("uq_employees_email")),
    )
    op.create_index(op.f("ix_employees_name"), "employees", ["name"])
    op.create_index(op.f("ix_employees_monthly_salary"), "employees", ["monthly_salary"])
    op.create_index(op.f("ix_employees_country"), "employees", ["country"])

    allowed_methods = ", ".join(f"'{method}'" for method in PAYMENT_METHODS)
    op.create_table(
        "payrolls",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("employee_id", sa.BigInteger(), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("base", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("bonus", sa.Numeric(precision=14, scale=2), server_default="0", nullable=False),
        sa.Column("esops", sa.Numeric(precision=14, scale=2), server_default="0", nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_method", sa.String(length=20), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "EXTRACT(DAY FROM month) = 1", name=op.f("ck_payrolls_month_is_first_day")
        ),
        sa.CheckConstraint("base >= 0", name=op.f("ck_payrolls_base_non_negative")),
        sa.CheckConstraint("bonus >= 0", name=op.f("ck_payrolls_bonus_non_negative")),
        sa.CheckConstraint("esops >= 0", name=op.f("ck_payrolls_esops_non_negative")),
        sa.CheckConstraint("currency ~ '^[A-Z]{3}$'", name=op.f("ck_payrolls_currency_iso_4217")),
        sa.CheckConstraint(
            f"payment_method IN ({allowed_methods})", name=op.f("ck_payrolls_payment_method")
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name=op.f("fk_payrolls_employee_id_employees"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payrolls")),
        sa.UniqueConstraint("employee_id", "month", name=op.f("uq_payrolls_employee_id_month")),
    )
    op.create_index(op.f("ix_payrolls_month"), "payrolls", ["month"])


def downgrade() -> None:
    op.drop_table("payrolls")
    op.drop_table("employees")
