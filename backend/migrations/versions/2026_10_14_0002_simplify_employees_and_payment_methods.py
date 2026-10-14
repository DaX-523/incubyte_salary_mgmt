"""Add job titles, drop last_transaction_at and the salary index, retire cash and cheque.

Existing employees get the job title "Unassigned"; existing cash and cheque payrolls become
bank transfers. Downgrading recomputes last_transaction_at from payrolls, but cannot restore the
original cash/cheque payment methods.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen copies of PaymentMethod's values: migrations must not import application code.
PAYMENT_METHODS = ("bank_transfer", "digital_wallet")
PREVIOUS_PAYMENT_METHODS = ("bank_transfer", "cheque", "cash", "digital_wallet")
RETIRED_PAYMENT_METHODS = ("cheque", "cash")
REPLACEMENT_PAYMENT_METHOD = "bank_transfer"
# Rows that predate job titles get a visible placeholder instead of a guess.
JOB_TITLE_PLACEHOLDER = "Unassigned"


def sql_list(values: Sequence[str]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def replace_payment_method_constraint(methods: Sequence[str]) -> None:
    op.drop_constraint(op.f("ck_payrolls_payment_method"), "payrolls", type_="check")
    op.create_check_constraint(
        op.f("ck_payrolls_payment_method"), "payrolls", f"payment_method IN ({sql_list(methods)})"
    )


def upgrade() -> None:
    op.add_column("employees", sa.Column("job_title", sa.String(length=150), nullable=True))
    op.execute(f"UPDATE employees SET job_title = '{JOB_TITLE_PLACEHOLDER}'")
    op.alter_column("employees", "job_title", nullable=False)
    op.create_index(op.f("ix_employees_job_title"), "employees", ["job_title"])
    op.create_index(op.f("ix_employees_department"), "employees", ["department"])
    op.drop_index(op.f("ix_employees_monthly_salary"), table_name="employees")
    op.drop_column("employees", "last_transaction_at")

    op.execute(
        f"UPDATE payrolls SET payment_method = '{REPLACEMENT_PAYMENT_METHOD}' "
        f"WHERE payment_method IN ({sql_list(RETIRED_PAYMENT_METHODS)})"
    )
    replace_payment_method_constraint(PAYMENT_METHODS)


def downgrade() -> None:
    replace_payment_method_constraint(PREVIOUS_PAYMENT_METHODS)

    op.add_column(
        "employees",
        sa.Column("last_transaction_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE employees SET last_transaction_at = "
        "(SELECT max(created_at) FROM payrolls WHERE payrolls.employee_id = employees.id)"
    )
    op.create_index(op.f("ix_employees_monthly_salary"), "employees", ["monthly_salary"])
    op.drop_index(op.f("ix_employees_department"), table_name="employees")
    op.drop_index(op.f("ix_employees_job_title"), table_name="employees")
    op.drop_column("employees", "job_title")
