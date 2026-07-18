from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "0010_balance_reset"
down_revision = "0009_user_opening_balance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "opening_balance_reset_at" not in columns:
        op.add_column("users", sa.Column("opening_balance_reset_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "opening_balance_reset_at")
