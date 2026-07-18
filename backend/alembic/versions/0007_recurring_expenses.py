from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_recurring_expenses"
down_revision = "0006_user_default_salary"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recurring_expenses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.Column("day_of_month", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("month_of_year", sa.Integer(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recurring_expenses_id"), "recurring_expenses", ["id"], unique=False)
    op.create_index(op.f("ix_recurring_expenses_user_id"), "recurring_expenses", ["user_id"], unique=False)
    op.alter_column("recurring_expenses", "day_of_month", server_default=None)
    op.alter_column("recurring_expenses", "enabled", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_recurring_expenses_user_id"), table_name="recurring_expenses")
    op.drop_index(op.f("ix_recurring_expenses_id"), table_name="recurring_expenses")
    op.drop_table("recurring_expenses")
