"""Add organizations and users, and make every employee belong to an organization.

Existing employees join a new organization named ACME. Employee emails become unique per
organization instead of globally. Downgrading drops users and organizations, and fails if two
organizations have an employee with the same email.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-16

"""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Employees that predate organizations join the demo organization.
BACKFILL_ORGANIZATION = "ACME"


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
        "organizations",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
        sa.UniqueConstraint("name", name=op.f("uq_organizations_name")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("session_version", sa.Integer(), server_default="1", nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint("session_version >= 1", name=op.f("ck_users_session_version_positive")),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_users_organization_id_organizations"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_organization_id"), "users", ["organization_id"])

    op.add_column("employees", sa.Column("organization_id", sa.BigInteger(), nullable=True))
    op.execute(
        f"INSERT INTO organizations (name) SELECT '{BACKFILL_ORGANIZATION}' "
        "WHERE EXISTS (SELECT 1 FROM employees)"
    )
    op.execute(
        "UPDATE employees SET organization_id = "
        f"(SELECT id FROM organizations WHERE name = '{BACKFILL_ORGANIZATION}')"
    )
    op.alter_column("employees", "organization_id", nullable=False)
    op.create_foreign_key(
        op.f("fk_employees_organization_id_organizations"),
        "employees",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(op.f("ix_employees_organization_id"), "employees", ["organization_id"])
    op.drop_constraint(op.f("uq_employees_email"), "employees", type_="unique")
    op.create_unique_constraint(
        op.f("uq_employees_organization_id_email"), "employees", ["organization_id", "email"]
    )


def downgrade() -> None:
    op.drop_constraint(op.f("uq_employees_organization_id_email"), "employees", type_="unique")
    op.create_unique_constraint(op.f("uq_employees_email"), "employees", ["email"])
    op.drop_index(op.f("ix_employees_organization_id"), table_name="employees")
    op.drop_constraint(
        op.f("fk_employees_organization_id_organizations"), "employees", type_="foreignkey"
    )
    op.drop_column("employees", "organization_id")
    op.drop_index(op.f("ix_users_organization_id"), table_name="users")
    op.drop_table("users")
    op.drop_table("organizations")
