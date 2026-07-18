from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "0009_user_opening_balance"
down_revision = "0008_recur_start"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "opening_balance_date" not in columns:
        op.add_column("users", sa.Column("opening_balance_date", sa.Date(), nullable=True))
    if "opening_balance_amount" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "opening_balance_amount",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default="0",
            ),
        )
        op.alter_column(
            "users",
            "opening_balance_amount",
            existing_type=sa.Numeric(precision=12, scale=2),
            server_default=None,
        )


def downgrade() -> None:
    op.drop_column("users", "opening_balance_amount")
    op.drop_column("users", "opening_balance_date")
