"""monthly incomes

Revision ID: 0003_monthly_incomes
Revises: 0002_align_postgresql_users
Create Date: 2026-05-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_monthly_incomes"
down_revision = "0002_align_postgresql_users"
branch_labels = None
depends_on = None


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    exists = any(index["name"] == index_name for index in inspector.get_indexes(table_name))
    if not exists:
        op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    dialect = op.get_bind().dialect.name

    op.create_table(
        "monthly_incomes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("salary_income", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("extra_income", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    if dialect == "mysql":
        _create_index_if_missing(op.f("ix_monthly_incomes_user_id"), "monthly_incomes", ["user_id"])
        _create_index_if_missing(
            "ix_monthly_incomes_user_period",
            "monthly_incomes",
            ["user_id", "year", "month"],
            unique=True,
        )
    else:
        op.create_index(op.f("ix_monthly_incomes_user_id"), "monthly_incomes", ["user_id"], if_not_exists=True)
        op.create_index(
            "ix_monthly_incomes_user_period",
            "monthly_incomes",
            ["user_id", "year", "month"],
            unique=True,
            if_not_exists=True,
        )


def downgrade() -> None:
    op.drop_index("ix_monthly_incomes_user_period", table_name="monthly_incomes", if_exists=True)
    op.drop_index(op.f("ix_monthly_incomes_user_id"), table_name="monthly_incomes", if_exists=True)
    op.drop_table("monthly_incomes", if_exists=True)
