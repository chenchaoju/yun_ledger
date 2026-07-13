"""add recurring membership expenses

Revision ID: 0007_recurring_expenses
Revises: 0006_user_default_salary
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_recurring_expenses"
down_revision = "0006_user_default_salary"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recurring_expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("category", sa.String(60), nullable=False, server_default="会员订阅"),
        sa.Column("frequency", sa.String(10), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_recurring_expenses_user_id", "recurring_expenses", ["user_id"])
    op.add_column("expenses", sa.Column("recurring_expense_id", sa.Integer(), nullable=True))
    op.add_column("expenses", sa.Column("recurring_period", sa.String(10), nullable=True))
    op.create_foreign_key("fk_expenses_recurring", "expenses", "recurring_expenses", ["recurring_expense_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_expenses_recurring_expense_id", "expenses", ["recurring_expense_id"])
    op.create_unique_constraint("uq_expense_recurring_period", "expenses", ["recurring_expense_id", "recurring_period"])


def downgrade():
    op.drop_constraint("uq_expense_recurring_period", "expenses", type_="unique")
    op.drop_index("ix_expenses_recurring_expense_id", table_name="expenses")
    op.drop_constraint("fk_expenses_recurring", "expenses", type_="foreignkey")
    op.drop_column("expenses", "recurring_period")
    op.drop_column("expenses", "recurring_expense_id")
    op.drop_index("ix_recurring_expenses_user_id", table_name="recurring_expenses")
    op.drop_table("recurring_expenses")
