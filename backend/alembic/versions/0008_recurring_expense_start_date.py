from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "0008_recur_start"
down_revision = "0007_recurring_expenses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("recurring_expenses")}
    if "start_date" not in columns:
        op.add_column("recurring_expenses", sa.Column("start_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("recurring_expenses", "start_date")
