from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_user_default_salary"
down_revision = "0005_user_username"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "default_salary_income",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.alter_column(
        "users",
        "default_salary_income",
        existing_type=sa.Numeric(precision=12, scale=2),
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("users", "default_salary_income")
