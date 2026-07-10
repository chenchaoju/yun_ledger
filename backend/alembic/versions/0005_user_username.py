from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_user_username"
down_revision = "0004_extra_income_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=80), nullable=True))
    dialect = op.get_bind().dialect.name
    if dialect == "mysql":
        op.execute("UPDATE users SET username = SUBSTRING_INDEX(email, '@', 1) WHERE username IS NULL")
    else:
        op.execute("UPDATE users SET username = split_part(email, '@', 1) WHERE username IS NULL")


def downgrade() -> None:
    op.drop_column("users", "username")
